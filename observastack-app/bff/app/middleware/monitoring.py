"""Monitoring middleware for request tracking and performance measurement."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import (
    get_logger,
    set_correlation_id,
    set_tenant_context,
    set_user_context,
    clear_context,
    log_performance
)
from ..core.monitoring import record_request_metrics, metrics_collector

logger = get_logger("middleware.monitoring")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for request monitoring and performance tracking."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with monitoring and logging."""
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Extract tenant and user context from request if available
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        
        if tenant_id:
            set_tenant_context(tenant_id)
        if user_id:
            set_user_context(user_id)
        
        # Record request start
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "user_agent": request.headers.get("user-agent"),
                    "remote_addr": request.client.host if request.client else None,
                    "correlation_id": correlation_id
                }
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Record metrics
            record_request_metrics(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                tenant_id=tenant_id
            )
            
            # Log request completion
            log_performance(
                logger,
                f"{request.method} {request.url.path}",
                duration_ms,
                status_code=response.status_code,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration_ms = (time.time() - start_time) * 1000
            
            # Record error metrics
            record_request_metrics(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                tenant_id=tenant_id
            )
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "error": str(e)
                    }
                }
            )
            
            raise
        
        finally:
            # Clear context after request
            clear_context()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting application metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect application-level metrics."""
        # Record active requests
        metrics_collector.increment_counter(
            "http_requests_active",
            {"method": request.method}
        )
        
        try:
            response = await call_next(request)
            
            # Record response size if available
            content_length = response.headers.get("content-length")
            if content_length:
                metrics_collector.record_histogram(
                    "http_response_size_bytes",
                    float(content_length),
                    {
                        "method": request.method,
                        "status_code": str(response.status_code)
                    },
                    "bytes"
                )
            
            return response
            
        finally:
            # Decrement active requests
            metrics_collector.increment_counter(
                "http_requests_active",
                {"method": request.method},
                -1.0
            )