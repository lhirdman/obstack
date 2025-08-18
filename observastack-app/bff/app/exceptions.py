"""Custom exceptions and error handling for ObservaStack BFF."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import uuid


class ErrorDetail(BaseModel):
    """Error detail model for validation errors."""
    field: str
    message: str
    code: str


class ObservaStackException(Exception):
    """Base exception class for ObservaStack."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow()
        self.request_id = str(uuid.uuid4())
        super().__init__(self.message)


class AuthenticationException(ObservaStackException):
    """Authentication related exceptions."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(ObservaStackException):
    """Authorization related exceptions."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationException(ObservaStackException):
    """Validation related exceptions."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        validation_errors: Optional[List[ErrorDetail]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.validation_errors = validation_errors or []
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class TenantException(ObservaStackException):
    """Tenant related exceptions."""
    
    def __init__(self, message: str = "Tenant access error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TENANT_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundException(ObservaStackException):
    """Resource not found exceptions."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(ObservaStackException):
    """Resource conflict exceptions."""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_CONFLICT",
            details=details,
            status_code=status.HTTP_409_CONFLICT
        )


class RateLimitException(ObservaStackException):
    """Rate limiting exceptions."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class ServiceUnavailableException(ObservaStackException):
    """Service unavailable exceptions."""
    
    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ExternalServiceException(ObservaStackException):
    """External service integration exceptions."""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.service_name = service_name
        super().__init__(
            message=f"{service_name}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class SearchException(ObservaStackException):
    """Search operation exceptions."""
    
    def __init__(self, message: str = "Search operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SEARCH_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AlertException(ObservaStackException):
    """Alert operation exceptions."""
    
    def __init__(self, message: str = "Alert operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ALERT_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class InsightsException(ObservaStackException):
    """Insights operation exceptions."""
    
    def __init__(self, message: str = "Insights operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INSIGHTS_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ConfigurationException(ObservaStackException):
    """Configuration related exceptions."""
    
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DatabaseException(ObservaStackException):
    """Database operation exceptions."""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CacheException(ObservaStackException):
    """Cache operation exceptions."""
    
    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class OpenCostException(ObservaStackException):
    """OpenCost integration exceptions."""
    
    def __init__(self, message: str = "OpenCost operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="OPENCOST_ERROR",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class TenantIsolationException(ObservaStackException):
    """Tenant isolation violation exceptions."""
    
    def __init__(self, message: str = "Tenant isolation violation", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TENANT_ISOLATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class GrafanaException(ObservaStackException):
    """Grafana integration exceptions."""
    
    def __init__(self, message: str = "Grafana operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="GRAFANA_ERROR",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: str
    validation_errors: Optional[List[ErrorDetail]] = None


def create_error_response(exception: ObservaStackException) -> ErrorResponse:
    """Create a standardized error response from an exception."""
    validation_errors = None
    if isinstance(exception, ValidationException):
        validation_errors = exception.validation_errors
    
    return ErrorResponse(
        error=exception.error_code,
        message=exception.message,
        details=exception.details,
        timestamp=exception.timestamp,
        request_id=exception.request_id,
        validation_errors=validation_errors
    )


def create_http_exception(exception: ObservaStackException) -> HTTPException:
    """Convert ObservaStackException to FastAPI HTTPException."""
    error_response = create_error_response(exception)
    
    headers = {}
    if isinstance(exception, RateLimitException) and exception.retry_after:
        headers["Retry-After"] = str(exception.retry_after)
    
    return HTTPException(
        status_code=exception.status_code,
        detail=error_response.model_dump(),
        headers=headers if headers else None
    )


# Error code constants
class ErrorCodes:
    """Error code constants."""
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TENANT_ERROR = "TENANT_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"
    ALERT_ERROR = "ALERT_ERROR"
    INSIGHTS_ERROR = "INSIGHTS_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    OPENCOST_ERROR = "OPENCOST_ERROR"
    TENANT_ISOLATION_ERROR = "TENANT_ISOLATION_ERROR"
    GRAFANA_ERROR = "GRAFANA_ERROR"


# Tenant-specific exceptions
class TenantNotFoundError(ResourceNotFoundException):
    """Tenant not found exception."""
    
    def __init__(self, message: str = "Tenant not found"):
        super().__init__(message=message)


class TenantAlreadyExistsError(ConflictException):
    """Tenant already exists exception."""
    
    def __init__(self, message: str = "Tenant already exists"):
        super().__init__(message=message)


class TenantOperationError(ObservaStackException):
    """Tenant operation error exception."""
    
    def __init__(self, message: str = "Tenant operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TENANT_OPERATION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# HTTP status code constants
# Aliases for backward compatibility
AuthenticationError = AuthenticationException
AuthorizationError = AuthorizationException
ValidationError = ValidationException
NotFoundError = ResourceNotFoundException
OpenCostError = OpenCostException
TenantIsolationError = TenantIsolationException
GrafanaError = GrafanaException


class StatusCodes:
    """HTTP status code constants."""
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED
    CONFLICT = status.HTTP_409_CONFLICT
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    BAD_GATEWAY = status.HTTP_502_BAD_GATEWAY
    SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE
    GATEWAY_TIMEOUT = status.HTTP_504_GATEWAY_TIMEOUT