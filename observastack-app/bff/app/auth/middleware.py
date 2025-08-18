"""JWT Authentication middleware for FastAPI."""

import logging
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .jwt_handler import JWTHandler
from .models import UserContext
from ..exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle JWT authentication for protected routes."""
    
    def __init__(
        self,
        app: ASGIApp,
        jwt_handler: Optional[JWTHandler] = None,
        exclude_paths: Optional[list[str]] = None
    ):
        """Initialize the JWT authentication middleware."""
        super().__init__(app)
        self.jwt_handler = jwt_handler or JWTHandler()
        
        # Default paths that don't require authentication
        self.exclude_paths = exclude_paths or [
            "/api/docs",
            "/api/redoc", 
            "/api/openapi.json",
            "/api/auth/login",
            "/api/auth/refresh",
            "/api/auth/jwks",
            "/api/meta/flags",
            "/health",
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and handle authentication."""
        # Skip authentication for excluded paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # Extract and validate JWT token
        try:
            user_context = self._extract_and_validate_token(request)
            
            # Add user context to request state
            request.state.user = user_context
            request.state.authenticated = True
            
            # Add tenant context for easy access
            request.state.tenant_id = user_context.tenant_id
            
            logger.debug(
                f"Authenticated request for user {user_context.user_id} "
                f"in tenant {user_context.tenant_id}"
            )
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed for {request.url.path}: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "authentication_required",
                    "message": str(e),
                    "details": "Valid JWT token required"
                }
            )
        except AuthorizationError as e:
            logger.warning(f"Authorization failed for {request.url.path}: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "insufficient_permissions", 
                    "message": str(e),
                    "details": "User lacks required permissions"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in auth middleware: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "Authentication service unavailable"
                }
            )
        
        # Continue with the request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    def _extract_and_validate_token(self, request: Request) -> UserContext:
        """Extract JWT token from request and validate it."""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        token = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Fallback to cookie if no header token
        if not token:
            token = request.cookies.get("access_token")
        
        if not token:
            raise AuthenticationError("No authentication token provided")
        
        # Validate the token
        return self.jwt_handler.validate_token(token)
    
    def add_exclude_path(self, path: str) -> None:
        """Add a path to the exclusion list."""
        if path not in self.exclude_paths:
            self.exclude_paths.append(path)
    
    def remove_exclude_path(self, path: str) -> None:
        """Remove a path from the exclusion list."""
        if path in self.exclude_paths:
            self.exclude_paths.remove(path)