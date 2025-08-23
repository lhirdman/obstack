"""
Traces API endpoints for querying Tempo distributed tracing data.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import jwt_middleware
from app.db.session import get_db
from app.db.models import User
from app.services.tempo_service import tempo_service
from app.core.error_handling import ExternalServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


class TraceSearchRequest(BaseModel):
    """Request model for trace search queries."""
    service: Optional[str] = Field(None, description="Service name filter")
    operation: Optional[str] = Field(None, description="Operation name filter")
    start: Optional[int] = Field(None, description="Start time (Unix timestamp in seconds)")
    end: Optional[int] = Field(None, description="End time (Unix timestamp in seconds)")
    limit: Optional[int] = Field(20, description="Maximum number of results", ge=1, le=100)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "service": "frontend",
                "operation": "GET /api/users",
                "start": 1640995200,
                "end": 1641081600,
                "limit": 20
            }
        }
    }


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    return await jwt_middleware.get_current_user(request, db)


@router.get("/{trace_id}")
async def get_trace(
    trace_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific trace by ID.
    
    This endpoint retrieves a distributed trace from Tempo by its trace ID.
    The trace must belong to the user's tenant for security isolation.
    
    - **trace_id**: Hexadecimal trace ID (e.g., "1234567890abcdef")
    
    The endpoint automatically validates that the trace belongs to the user's
    tenant by checking for `tenant_id` attributes in the trace data.
    
    **Security:**
    - Requires valid JWT authentication
    - Enforces tenant isolation - users can only access traces from their tenant
    - Returns 404 if trace doesn't exist or doesn't belong to user's tenant
    
    **Response:**
    Returns the complete trace data in OpenTelemetry format, including:
    - Trace spans with timing information
    - Service and operation names
    - Tags and attributes
    - Parent-child span relationships
    """
    logger.info(f"Trace retrieval request for {trace_id} from user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        trace_data = await tempo_service.get_trace(
            trace_id=trace_id,
            tenant_id=current_user.tenant_id
        )
        return trace_data
    except ExternalServiceError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve trace"
            )


@router.post("/search")
async def search_traces(
    request: TraceSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for traces with optional filters.
    
    This endpoint searches for distributed traces in Tempo with tenant isolation.
    All results are automatically filtered to only include traces from the user's tenant.
    
    **Filters:**
    - **service**: Filter by service name (optional)
    - **operation**: Filter by operation name (optional)
    - **start**: Start time as Unix timestamp in seconds (optional)
    - **end**: End time as Unix timestamp in seconds (optional)
    - **limit**: Maximum number of results (1-100, default: 20)
    
    **Security:**
    - Requires valid JWT authentication
    - Enforces tenant isolation automatically
    - Only returns traces that belong to the user's tenant
    
    **Response:**
    Returns a list of trace summaries matching the search criteria.
    Each result includes basic trace information like trace ID, duration,
    service names, and timestamps.
    """
    logger.info(f"Trace search request from user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        search_results = await tempo_service.search_traces(
            tenant_id=current_user.tenant_id,
            service=request.service,
            operation=request.operation,
            start=request.start,
            end=request.end,
            limit=request.limit
        )
        return search_results
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search traces"
        )


@router.get("/")
async def list_recent_traces(
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    List recent traces for the user's tenant.
    
    This is a convenience endpoint that returns the most recent traces
    for the authenticated user's tenant without additional filters.
    
    - **limit**: Maximum number of results (1-100, default: 20)
    
    **Security:**
    - Requires valid JWT authentication
    - Enforces tenant isolation automatically
    
    **Response:**
    Returns a list of recent trace summaries for the user's tenant.
    """
    logger.info(f"Recent traces request from user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        search_results = await tempo_service.search_traces(
            tenant_id=current_user.tenant_id,
            limit=limit
        )
        return search_results
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent traces"
        )