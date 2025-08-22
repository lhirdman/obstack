"""
Centralized error handling middleware for FastAPI application.
"""

import logging
import traceback
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Base class for application-specific errors."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CustomValidationError(ApplicationError):
    """Error for custom validation failures."""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class AuthenticationError(ApplicationError):
    """Error for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(ApplicationError):
    """Error for authorization failures."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(ApplicationError):
    """Error for resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(ApplicationError):
    """Error for resource conflicts."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class ExternalServiceError(ApplicationError):
    """Error for external service failures."""
    
    def __init__(self, message: str = "External service unavailable"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all unhandled exceptions and standardize error responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and handle any exceptions."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._handle_exception(request, exc)
    
    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle different types of exceptions and return standardized error responses.
        
        Args:
            request: The FastAPI request object
            exc: The exception that was raised
            
        Returns:
            JSONResponse with standardized error format
        """
        # Log the exception details for debugging
        logger.error(
            f"Exception occurred: {type(exc).__name__}: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else "unknown",
                "traceback": traceback.format_exc()
            }
        )
        
        # Handle HTTPException (FastAPI's standard exception)
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": exc.detail,
                    "type": "http_exception"
                }
            )
        
        # Handle custom application exceptions
        if isinstance(exc, ApplicationError):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": exc.message,
                    "type": "application_error"
                }
            )
        
        # Handle Pydantic validation errors
        if isinstance(exc, PydanticValidationError):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": "Validation error",
                    "type": "validation_error",
                    "errors": exc.errors()
                }
            )
        
        # Handle SQLAlchemy database errors
        if isinstance(exc, SQLAlchemyError):
            logger.error(f"Database error: {str(exc)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Database error occurred",
                    "type": "database_error"
                }
            )
        
        # Handle any other unexpected exceptions
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "type": "internal_error"
            }
        )


def create_error_response(
    message: str, 
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_type: str = "error"
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message to return
        status_code: HTTP status code
        error_type: Type of error for categorization
        
    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message,
            "type": error_type
        }
    )


# Exception handler functions for specific use cases
async def handle_validation_exception(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "type": "validation_error",
            "errors": exc.errors()
        }
    )


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "http_exception"
        }
    )


async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )
