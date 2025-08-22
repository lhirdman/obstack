"""
Metrics API endpoints for querying Prometheus/Thanos data.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import jwt_middleware
from app.db.session import get_db
from app.db.models import User
from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)

router = APIRouter()


class MetricsQueryRequest(BaseModel):
    """Request model for metrics queries."""
    query: str = Field(..., description="PromQL query string")
    time: Optional[str] = Field(None, description="Evaluation timestamp (RFC3339 format)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "up",
                "time": "2023-01-01T12:00:00Z"
            }
        }
    }


class MetricsRangeQueryRequest(BaseModel):
    """Request model for metrics range queries."""
    query: str = Field(..., description="PromQL query string")
    start: str = Field(..., description="Start timestamp (RFC3339 format)")
    end: str = Field(..., description="End timestamp (RFC3339 format)")
    step: str = Field(..., description="Query resolution step (e.g., '15s', '1m', '1h')")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "rate(http_requests_total[5m])",
                "start": "2023-01-01T12:00:00Z",
                "end": "2023-01-01T13:00:00Z",
                "step": "1m"
            }
        }
    }


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    return await jwt_middleware.get_current_user(request, db)


@router.post("/query")
async def query_metrics(
    request: MetricsQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a PromQL query against Prometheus/Thanos.
    
    This endpoint proxies queries to the configured Prometheus/Thanos instance
    and automatically injects the user's tenant_id for data isolation.
    
    - **query**: PromQL query string (e.g., "up", "rate(http_requests_total[5m])")
    - **time**: Optional evaluation timestamp in RFC3339 format
    
    The query will be automatically modified to include tenant isolation by
    injecting `tenant_id="<user_tenant_id>"` into all metric selectors.
    
    **Example:**
    - Input query: `up`
    - Modified query: `up{tenant_id="123"}`
    
    Returns the query results in Prometheus API format.
    """
    logger.info(f"Metrics query request from user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        result = await metrics_service.query(
            query=request.query,
            tenant_id=current_user.tenant_id,
            time=request.time
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in metrics query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/query_range")
async def query_range_metrics(
    request: MetricsRangeQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a PromQL range query against Prometheus/Thanos.
    
    This endpoint proxies range queries to the configured Prometheus/Thanos instance
    and automatically injects the user's tenant_id for data isolation.
    
    - **query**: PromQL query string (e.g., "rate(http_requests_total[5m])")
    - **start**: Start timestamp in RFC3339 format
    - **end**: End timestamp in RFC3339 format  
    - **step**: Query resolution step (e.g., "15s", "1m", "1h")
    
    The query will be automatically modified to include tenant isolation by
    injecting `tenant_id="<user_tenant_id>"` into all metric selectors.
    
    Returns the range query results in Prometheus API format.
    """
    logger.info(f"Metrics range query request from user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        result = await metrics_service.query_range(
            query=request.query,
            tenant_id=current_user.tenant_id,
            start=request.start,
            end=request.end,
            step=request.step
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in metrics range query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/labels/{label}/values")
async def get_label_values(
    label: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all values for a specific label with tenant isolation.
    
    This endpoint retrieves all possible values for a given label name,
    filtered by the user's tenant_id for data isolation.
    
    - **label**: Label name to get values for (e.g., "job", "instance", "__name__")
    
    Only returns label values for metrics that belong to the user's tenant.
    
    Returns the label values in Prometheus API format.
    """
    logger.info(f"Label values request for '{label}' from user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        result = await metrics_service.get_label_values(
            label=label,
            tenant_id=current_user.tenant_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get label values: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )