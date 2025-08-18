"""Error handlers for FastAPI application."""

import logging
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    ObservaStackException,
    ErrorResponse,
    ErrorDetail,
    create_error_response,
    ValidationException
)

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """Setup error handlers for the FastAPI application."""
    
    @app.exception_handler(ObservaStackException)
    async def observastack_exception_handler(request: Request, exc: ObservaStackException) -> JSONResponse:
        """Handle custom ObservaStack exceptions."""
        logger.error(
            f"ObservaStack exception: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "request_id": exc.request_id,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = create_error_response(exc)
        headers = {}
        
        # Add retry-after header for rate limit errors
        if hasattr(exc, 'retry_after') and exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
            headers=headers if headers else None
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        validation_errors = []
        
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            validation_errors.append(ErrorDetail(
                field=field,
                message=error["msg"],
                code=error["type"]
            ))
        
        validation_exc = ValidationException(
            message="Request validation failed",
            validation_errors=validation_errors,
            details={"raw_errors": exc.errors()}
        )
        
        logger.warning(
            f"Validation error: {validation_exc.message}",
            extra={
                "validation_errors": [ve.model_dump() for ve in validation_errors],
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = create_error_response(validation_exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        # If detail is already a dict (from our custom exceptions), use it directly
        if isinstance(exc.detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
                headers=exc.headers
            )
        
        # Otherwise, create a standard error response
        error_response = ErrorResponse(
            error="HTTP_ERROR",
            message=str(exc.detail),
            details={"status_code": exc.status_code},
            timestamp=exc.timestamp if hasattr(exc, 'timestamp') else None,
            request_id=exc.request_id if hasattr(exc, 'request_id') else None
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
            headers=exc.headers
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            f"Starlette HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = ErrorResponse(
            error="HTTP_ERROR",
            message=str(exc.detail),
            details={"status_code": exc.status_code},
            timestamp=None,
            request_id=None
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        validation_errors = []
        
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            validation_errors.append(ErrorDetail(
                field=field,
                message=error["msg"],
                code=error["type"]
            ))
        
        validation_exc = ValidationException(
            message="Data validation failed",
            validation_errors=validation_errors,
            details={"raw_errors": exc.errors()}
        )
        
        logger.warning(
            f"Pydantic validation error: {validation_exc.message}",
            extra={
                "validation_errors": [ve.model_dump() for ve in validation_errors],
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = create_error_response(validation_exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method
            },
            exc_info=True
        )
        
        # Don't expose internal error details in production
        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            details={"exception_type": type(exc).__name__} if app.debug else None,
            timestamp=None,
            request_id=None
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )


def log_error_context(request: Request, error_details: Dict[str, Any]) -> None:
    """Log additional error context for debugging."""
    context = {
        "url": str(request.url),
        "method": request.method,
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        **error_details
    }
    
    logger.error("Error context", extra=context)