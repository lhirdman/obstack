"""Grafana proxy and dashboard management API endpoints."""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx

from ...auth.dependencies import get_current_user, get_current_tenant
from ...auth.models import UserContext
from ...services.grafana_client import GrafanaClient
from ...exceptions import GrafanaException, create_http_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grafana", tags=["grafana"])

# Dependency to get Grafana client
def get_grafana_client() -> GrafanaClient:
    """Dependency to get Grafana client instance."""
    return GrafanaClient()


# Request/Response models
class DashboardUrlRequest(BaseModel):
    """Request model for generating dashboard URLs."""
    dashboard_uid: str = Field(..., description="Dashboard UID")
    panel_id: Optional[int] = Field(None, description="Panel ID for direct panel linking")
    time_from: Optional[str] = Field(None, description="Time range start")
    time_to: Optional[str] = Field(None, description="Time range end")
    refresh: Optional[str] = Field(None, description="Refresh interval")
    variables: Optional[Dict[str, str]] = Field(None, description="Dashboard variables")
    theme: Optional[str] = Field("light", description="Theme (light/dark)")


class DashboardUrlResponse(BaseModel):
    """Response model for dashboard URLs."""
    url: str = Field(..., description="Complete dashboard URL")
    embed_url: str = Field(..., description="Embed URL for iframe")


class DashboardInfo(BaseModel):
    """Dashboard information model."""
    uid: str = Field(..., description="Dashboard UID")
    title: str = Field(..., description="Dashboard title")
    tags: List[str] = Field(default_factory=list, description="Dashboard tags")
    url: str = Field(..., description="Dashboard URL")
    folder_title: Optional[str] = Field(None, description="Folder title")


class DashboardListResponse(BaseModel):
    """Response model for dashboard list."""
    dashboards: List[DashboardInfo] = Field(..., description="List of dashboards")
    total: int = Field(..., description="Total number of dashboards")


class EmbedConfigResponse(BaseModel):
    """Response model for embed configuration."""
    grafana_url: str = Field(..., description="Grafana base URL")
    theme: str = Field(..., description="Default theme")
    tenant_id: str = Field(..., description="Tenant ID")
    auth_token: str = Field(..., description="Authentication token")


@router.get("/health")
async def grafana_health(
    grafana_client: GrafanaClient = Depends(get_grafana_client)
) -> Dict[str, Any]:
    """
    Check Grafana health status.
    
    Returns:
        Health status of Grafana instance
    """
    try:
        is_healthy = await grafana_client.health_check()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "grafana",
            "timestamp": "2025-08-15T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Grafana health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Grafana health check failed"
        )
    finally:
        await grafana_client.close()


@router.get("/dashboards", response_model=DashboardListResponse)
async def list_dashboards(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    grafana_client: GrafanaClient = Depends(get_grafana_client)
) -> DashboardListResponse:
    """
    List all dashboards accessible to the current tenant.
    
    Args:
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        grafana_client: Grafana client instance
        
    Returns:
        List of dashboards with metadata
    """
    try:
        dashboards_data = await grafana_client.get_dashboards_for_tenant(current_user)
        
        dashboards = []
        for dashboard in dashboards_data:
            dashboard_info = DashboardInfo(
                uid=dashboard.get("uid", ""),
                title=dashboard.get("title", ""),
                tags=dashboard.get("tags", []),
                url=dashboard.get("url", ""),
                folder_title=dashboard.get("folderTitle")
            )
            dashboards.append(dashboard_info)
        
        return DashboardListResponse(
            dashboards=dashboards,
            total=len(dashboards)
        )
        
    except GrafanaException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Failed to list dashboards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboards"
        )
    finally:
        await grafana_client.close()


@router.get("/dashboards/{dashboard_uid}")
async def get_dashboard(
    dashboard_uid: str,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    grafana_client: GrafanaClient = Depends(get_grafana_client)
) -> Dict[str, Any]:
    """
    Get a specific dashboard by UID.
    
    Args:
        dashboard_uid: Dashboard UID
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        grafana_client: Grafana client instance
        
    Returns:
        Dashboard data and metadata
    """
    try:
        dashboard = await grafana_client.get_dashboard_by_uid(dashboard_uid, current_user)
        return dashboard
        
    except GrafanaException as e:
        raise create_http_exception(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard {dashboard_uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard"
        )
    finally:
        await grafana_client.close()


@router.post("/dashboards/url", response_model=DashboardUrlResponse)
async def generate_dashboard_url(
    request: DashboardUrlRequest,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    grafana_client: GrafanaClient = Depends(get_grafana_client)
) -> DashboardUrlResponse:
    """
    Generate a dashboard URL with tenant context and authentication.
    
    Args:
        request: Dashboard URL request parameters
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        grafana_client: Grafana client instance
        
    Returns:
        Dashboard URL and embed URL
    """
    try:
        # Generate authenticated dashboard URL
        dashboard_url = await grafana_client.get_dashboard_url(
            dashboard_uid=request.dashboard_uid,
            user_context=current_user,
            panel_id=request.panel_id,
            time_from=request.time_from,
            time_to=request.time_to,
            refresh=request.refresh,
            variables=request.variables
        )
        
        # Generate embed URL for iframe
        embed_url = grafana_client.get_embed_url(
            dashboard_uid=request.dashboard_uid,
            panel_id=request.panel_id,
            theme=request.theme or "light",
            time_from=request.time_from,
            time_to=request.time_to,
            variables=request.variables
        )
        
        return DashboardUrlResponse(
            url=dashboard_url,
            embed_url=embed_url
        )
        
    except GrafanaException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Failed to generate dashboard URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard URL"
        )
    finally:
        await grafana_client.close()


@router.get("/embed/config", response_model=EmbedConfigResponse)
async def get_embed_config(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    grafana_client: GrafanaClient = Depends(get_grafana_client)
) -> EmbedConfigResponse:
    """
    Get configuration for embedding Grafana dashboards.
    
    Args:
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        grafana_client: Grafana client instance
        
    Returns:
        Embed configuration including auth token
    """
    try:
        # Get tenant-specific token
        auth_token = await grafana_client.get_or_create_tenant_token(tenant_id)
        
        return EmbedConfigResponse(
            grafana_url=grafana_client.base_url,
            theme="light",
            tenant_id=tenant_id,
            auth_token=auth_token
        )
        
    except GrafanaException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Failed to get embed config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get embed configuration"
        )
    finally:
        await grafana_client.close()


@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def grafana_proxy(
    request: Request,
    path: str,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    grafana_client: GrafanaClient = Depends(get_grafana_client)
):
    """
    Proxy requests to Grafana with tenant-aware authentication.
    
    Args:
        request: FastAPI request object
        path: Grafana API path to proxy
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        grafana_client: Grafana client instance
        
    Returns:
        Proxied response from Grafana
    """
    try:
        # Extract request data
        method = request.method
        params = dict(request.query_params)
        headers = dict(request.headers)
        
        # Get request body for POST/PUT requests
        json_data = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                json_data = await request.json()
            except Exception:
                # Handle non-JSON requests
                pass
        
        # Remove host and authorization headers to avoid conflicts
        headers.pop("host", None)
        headers.pop("authorization", None)
        
        # Proxy the request
        response = await grafana_client.proxy_request(
            method=method,
            path=f"/{path}",
            user_context=current_user,
            params=params,
            json_data=json_data,
            headers=headers
        )
        
        # Prepare response headers
        response_headers = {}
        for key, value in response.headers.items():
            # Skip headers that shouldn't be forwarded
            if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]:
                response_headers[key] = value
        
        # Add CORS headers for frontend
        response_headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Tenant-ID"
        })
        
        # Return streaming response for large responses
        if response.headers.get("content-type", "").startswith("application/json"):
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type="application/json"
            )
        else:
            # Stream non-JSON responses
            async def generate():
                async for chunk in response.aiter_bytes():
                    yield chunk
            
            return StreamingResponse(
                generate(),
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type", "application/octet-stream")
            )
        
    except GrafanaException as e:
        raise create_http_exception(e)
    except httpx.HTTPStatusError as e:
        # Forward HTTP errors from Grafana
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Grafana error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Grafana proxy error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Grafana proxy error"
        )
    finally:
        await grafana_client.close()


@router.post("/dashboards/{dashboard_uid}/snapshot")
async def create_dashboard_snapshot(
    dashboard_uid: str,
    expires: int = 3600,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    grafana_client: GrafanaClient = Depends(get_grafana_client)
) -> Dict[str, Any]:
    """
    Create a dashboard snapshot for sharing.
    
    Args:
        dashboard_uid: Dashboard UID
        expires: Snapshot expiration time in seconds
        current_user: Authenticated user context
        tenant_id: Tenant ID for isolation
        grafana_client: Grafana client instance
        
    Returns:
        Snapshot information including URL
    """
    try:
        snapshot = await grafana_client.create_dashboard_snapshot(
            dashboard_uid=dashboard_uid,
            user_context=current_user,
            expires=expires
        )
        
        return snapshot
        
    except GrafanaException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Failed to create dashboard snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dashboard snapshot"
        )
    finally:
        await grafana_client.close()