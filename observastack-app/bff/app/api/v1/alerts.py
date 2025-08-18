"""Alert management API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ...auth import get_current_user, get_current_tenant
from ...auth.models import UserContext
from ...models.alerts import (
    Alert, AlertWebhookPayload, AlertActionRequest, AlertActionResponse,
    AlertQuery, AlertsResponse, AlertStatistics, SilenceRequest, Silence
)
from ...services.alert_service import AlertService
from ...exceptions import AlertException, ValidationError, NotFoundError

# Create router
router = APIRouter(prefix="/alerts", tags=["alerts"])

# Initialize alert service (in production, this would be dependency injected)
alert_service = AlertService()


@router.post("/webhook/alertmanager")
async def alertmanager_webhook(
    payload: AlertWebhookPayload,
    request: Request
):
    """
    Webhook endpoint for Alertmanager notifications.
    
    This endpoint receives alert notifications from Prometheus Alertmanager
    and processes them for storage and management.
    
    Args:
        payload: Alertmanager webhook payload
        request: FastAPI request object for logging
        tenant_id: Tenant ID extracted from authentication
        
    Returns:
        Success response with processed alert count
        
    Raises:
        HTTPException: 400 for invalid payload, 500 for processing errors
    """
    try:
        # Log incoming webhook for debugging
        client_ip = request.client.host if request.client else "unknown"
        
        # For webhooks, we need to determine tenant from the payload or use a default
        # In production, this would be configured per webhook endpoint
        tenant_id = payload.group_labels.get("tenant_id", "default")
        
        # Process the webhook payload
        processed_alerts = await alert_service.process_webhook(payload, tenant_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"Processed {len(processed_alerts)} alerts",
                "processed_count": len(processed_alerts),
                "group_key": payload.group_key,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(e)}"
        )
    except AlertException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert processing failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during alert processing"
        )


@router.post("/webhook/generic")
async def generic_webhook(
    request: Request
):
    """
    Generic webhook endpoint for other alert sources.
    
    This endpoint can receive alerts from various sources like Grafana,
    custom monitoring tools, or other alerting systems.
    
    Args:
        request: FastAPI request object containing webhook data
        tenant_id: Tenant ID extracted from authentication
        
    Returns:
        Success response with processed alert information
        
    Raises:
        HTTPException: 400 for invalid payload, 500 for processing errors
    """
    try:
        # Parse request body
        body = await request.json()
        
        # For generic webhooks, determine tenant from payload or use default
        tenant_id = body.get("tenant_id", "default")
        
        # Convert generic webhook to AlertWebhookPayload format
        # This is a simplified conversion - in production, you'd have
        # specific parsers for different webhook formats
        converted_payload = AlertWebhookPayload(
            version="4",
            group_key=body.get("groupKey", f"generic_{datetime.utcnow().timestamp()}"),
            status=body.get("status", "firing"),
            receiver="generic",
            group_labels=body.get("groupLabels", {}),
            common_labels=body.get("commonLabels", {}),
            common_annotations=body.get("commonAnnotations", {}),
            external_url=body.get("externalURL", ""),
            alerts=body.get("alerts", [body])  # If single alert, wrap in array
        )
        
        # Process the converted payload
        processed_alerts = await alert_service.process_webhook(converted_payload, tenant_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"Processed {len(processed_alerts)} alerts from generic webhook",
                "processed_count": len(processed_alerts),
                "source": "generic",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(e)}"
        )
    except AlertException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert processing failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during alert processing"
        )


@router.get("", response_model=AlertsResponse)
async def get_alerts(
    status: Optional[List[str]] = None,
    severity: Optional[List[str]] = None,
    source: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> AlertsResponse:
    """
    Get alerts with filtering and pagination.
    
    Args:
        status: Filter by alert status (active, acknowledged, resolved, silenced)
        severity: Filter by severity level (critical, high, medium, low, info)
        source: Filter by alert source (prometheus, loki, tempo, opensearch, external)
        assignee: Filter by assigned user
        from_time: Filter alerts from this timestamp
        to_time: Filter alerts until this timestamp
        limit: Maximum number of alerts to return (1-1000)
        offset: Number of alerts to skip for pagination
        sort_by: Field to sort by (timestamp, severity, title, status)
        sort_order: Sort order (asc, desc)
        current_user: Authenticated user context
        tenant_id: Tenant ID for data isolation
        
    Returns:
        Paginated list of alerts matching the criteria
        
    Raises:
        HTTPException: 400 for invalid parameters, 500 for query errors
    """
    try:
        # Build query object
        query = AlertQuery(
            status=status,
            severity=severity,
            source=source,
            assignee=assignee,
            from_time=from_time,
            to_time=to_time,
            limit=min(limit, 1000),  # Cap at 1000
            offset=max(offset, 0),   # Ensure non-negative
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get alerts from service
        response = await alert_service.get_alerts(query, tenant_id)
        
        return response
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.post("/actions", response_model=AlertActionResponse)
async def perform_alert_action(
    action_request: AlertActionRequest,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> AlertActionResponse:
    """
    Perform actions on alerts (acknowledge, resolve, assign, silence).
    
    Args:
        action_request: Action request with alert IDs and action type
        current_user: Authenticated user context
        tenant_id: Tenant ID for authorization
        
    Returns:
        Action response with results and any failures
        
    Raises:
        HTTPException: 400 for invalid request, 403 for unauthorized, 500 for errors
    """
    try:
        # Perform the action
        response = await alert_service.perform_action(
            action_request, 
            current_user.user_id, 
            tenant_id
        )
        
        return response
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action request: {str(e)}"
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AlertException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during action processing"
        )


@router.get("/statistics", response_model=AlertStatistics)
async def get_alert_statistics(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> AlertStatistics:
    """
    Get alert statistics for the current tenant.
    
    Args:
        current_user: Authenticated user context
        tenant_id: Tenant ID for data isolation
        
    Returns:
        Alert statistics including counts by status, severity, source, and MTTR
        
    Raises:
        HTTPException: 500 for calculation errors
    """
    try:
        stats = await alert_service.get_alert_statistics(tenant_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate alert statistics"
        )


@router.post("/silences", response_model=Silence)
async def create_silence(
    silence_request: SilenceRequest,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> Silence:
    """
    Create a new silence to suppress matching alerts.
    
    Args:
        silence_request: Silence configuration with matchers and duration
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        
    Returns:
        Created silence object
        
    Raises:
        HTTPException: 400 for invalid request, 500 for creation errors
    """
    try:
        silence = await alert_service.create_silence(
            silence_request,
            current_user.user_id,
            tenant_id
        )
        
        return silence
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid silence request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create silence"
        )


@router.get("/health")
async def alert_service_health():
    """
    Check health status of alert service components.
    
    Returns:
        Health status of alert processing components
    """
    try:
        health_status = await alert_service.health_check()
        
        overall_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "components": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }