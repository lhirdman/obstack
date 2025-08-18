"""Health check and monitoring API endpoints."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from ...auth.dependencies import get_current_user, require_admin_role
from ...auth.models import UserContext
from ...core.monitoring import (
    health_checker,
    metrics_collector,
    HealthStatus,
    HealthCheck,
    MetricPoint
)
from ...core.logging import get_logger

logger = get_logger("api.health")

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: Dict[str, Dict[str, Any]]
    overall_status: str


class MetricsResponse(BaseModel):
    """Metrics response model."""
    metrics: list[Dict[str, Any]]
    count: int
    timestamp: datetime


class MetricSummaryResponse(BaseModel):
    """Metric summary response model."""
    name: str
    summary: Dict[str, Any]
    timestamp: datetime


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Get overall system health status.
    
    Returns comprehensive health information including:
    - Overall system status
    - Individual service health checks
    - System metadata
    """
    try:
        # Get overall health
        overall_health = await health_checker.get_overall_health()
        
        # Get individual checks
        individual_checks = await health_checker.run_all_checks()
        
        # Format response
        checks_dict = {}
        for name, check in individual_checks.items():
            checks_dict[name] = {
                "status": check.status.value,
                "message": check.message,
                "timestamp": check.timestamp.isoformat(),
                "response_time_ms": check.response_time_ms,
                "details": check.details
            }
        
        return HealthResponse(
            status="ok",
            timestamp=datetime.utcnow(),
            version="1.0.0",  # TODO: Get from config or environment
            environment="development",  # TODO: Get from config
            checks=checks_dict,
            overall_status=overall_health.status.value
        )
        
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/live")
async def liveness_probe():
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 if the application is running and can handle requests.
    This should only fail if the application is completely broken.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe endpoint.
    
    Returns 200 if the application is ready to handle requests.
    This checks critical dependencies and returns 503 if not ready.
    """
    try:
        # Check critical services only (not all dependencies)
        critical_checks = ["redis"]  # Add other critical services as needed
        
        results = {}
        for check_name in critical_checks:
            if check_name in health_checker.checks:
                result = await health_checker.run_check(check_name)
                results[check_name] = result
        
        # If any critical service is unhealthy, return 503
        if any(check.status == HealthStatus.UNHEALTHY for check in results.values()):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Critical services unavailable"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "critical_services": {
                name: check.status.value for name, check in results.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Readiness check failed"
        )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check(
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin_role)
):
    """
    Get detailed health information (admin only).
    
    Provides comprehensive health information including:
    - All service health checks
    - Performance metrics
    - System resource usage
    - Detailed error information
    """
    try:
        # Get all health checks
        overall_health = await health_checker.get_overall_health()
        individual_checks = await health_checker.run_all_checks()
        
        # Add performance metrics to health data
        for name, check in individual_checks.items():
            if check.response_time_ms is not None:
                # Get historical performance data
                since = datetime.utcnow() - timedelta(minutes=5)
                perf_metrics = metrics_collector.get_metrics(
                    name_filter=f"{name}_duration",
                    since=since
                )
                
                if perf_metrics:
                    avg_response_time = sum(m.value for m in perf_metrics) / len(perf_metrics)
                    check.details["avg_response_time_5m"] = avg_response_time
                    check.details["sample_count_5m"] = len(perf_metrics)
        
        # Format response with enhanced details
        checks_dict = {}
        for name, check in individual_checks.items():
            checks_dict[name] = {
                "status": check.status.value,
                "message": check.message,
                "timestamp": check.timestamp.isoformat(),
                "response_time_ms": check.response_time_ms,
                "details": check.details
            }
        
        return HealthResponse(
            status="ok",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            environment="development",
            checks=checks_dict,
            overall_status=overall_health.status.value
        )
        
    except Exception as e:
        logger.error("Detailed health check failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detailed health check failed"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    name_filter: Optional[str] = Query(None, description="Filter metrics by name"),
    since_minutes: int = Query(60, description="Get metrics from last N minutes"),
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin_role)
):
    """
    Get application metrics (admin only).
    
    Returns collected application metrics including:
    - Request performance metrics
    - Search operation metrics
    - Alert processing metrics
    - Cost monitoring metrics
    """
    try:
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        metrics = metrics_collector.get_metrics(name_filter, since)
        
        # Convert metrics to response format
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "name": metric.name,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "labels": metric.labels,
                "unit": metric.unit
            })
        
        return MetricsResponse(
            metrics=metrics_data,
            count=len(metrics_data),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Failed to get metrics", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


@router.get("/metrics/{metric_name}/summary", response_model=MetricSummaryResponse)
async def get_metric_summary(
    metric_name: str,
    since_minutes: int = Query(60, description="Calculate summary from last N minutes"),
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin_role)
):
    """
    Get summary statistics for a specific metric (admin only).
    
    Returns statistical summary including:
    - Count, min, max, average values
    - Latest value and timestamp
    - Trend information if available
    """
    try:
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        summary = metrics_collector.get_metric_summary(metric_name, since)
        
        return MetricSummaryResponse(
            name=metric_name,
            summary=summary,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get metric summary for {metric_name}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve summary for metric {metric_name}"
        )


@router.get("/services/{service_name}")
async def get_service_health(
    service_name: str,
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get health status for a specific service.
    
    Returns detailed health information for the specified service
    including response times and error details.
    """
    try:
        if service_name not in health_checker.checks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found"
            )
        
        health_result = await health_checker.run_check(service_name)
        
        return {
            "service": service_name,
            "status": health_result.status.value,
            "message": health_result.message,
            "timestamp": health_result.timestamp.isoformat(),
            "response_time_ms": health_result.response_time_ms,
            "details": health_result.details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check health for service {service_name}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check health for service {service_name}"
        )