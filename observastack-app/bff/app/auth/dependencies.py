"""FastAPI dependencies for authentication and authorization."""

import logging
from typing import Optional, List, Callable, Any
from functools import wraps
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import UserContext
from .jwt_handler import JWTHandler
from ..exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI documentation
security = HTTPBearer(auto_error=False)


def get_jwt_handler() -> JWTHandler:
    """Dependency to get JWT handler instance."""
    return JWTHandler()


def get_current_user(request: Request) -> UserContext:
    """
    Dependency to get the current authenticated user from request state.
    
    This dependency assumes the JWTAuthMiddleware has already processed
    the request and added user context to request.state.
    """
    if not hasattr(request.state, "authenticated") or not request.state.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User context not available"
        )
    
    return request.state.user


def get_current_tenant(current_user: UserContext = Depends(get_current_user)) -> str:
    """Dependency to get the current user's tenant ID."""
    return current_user.tenant_id


def get_optional_user(request: Request) -> Optional[UserContext]:
    """
    Dependency to optionally get the current user.
    Returns None if not authenticated.
    """
    if hasattr(request.state, "authenticated") and request.state.authenticated:
        return getattr(request.state, "user", None)
    return None


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> UserContext:
    """
    Dependency that validates JWT token directly (alternative to middleware).
    
    This can be used for endpoints that need authentication but bypass
    the middleware for some reason.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return jwt_handler.validate_token(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(required_roles: List[str]):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @app.get("/admin")
        def admin_endpoint(user: UserContext = Depends(require_roles(["admin"]))):
            pass
    """
    def check_roles(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        if not current_user.has_any_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        return current_user
    
    return check_roles


def require_admin(current_user: UserContext = Depends(get_current_user)) -> UserContext:
    """Dependency to require admin role."""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


def require_tenant_access(tenant_id: str):
    """
    Dependency factory to require access to a specific tenant.
    
    Usage:
        @app.get("/tenant/{tenant_id}/data")
        def get_tenant_data(
            tenant_id: str,
            user: UserContext = Depends(require_tenant_access(tenant_id))
        ):
            pass
    """
    def check_tenant_access(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        # Admin users can access any tenant
        if current_user.is_admin():
            return current_user
        
        # Regular users can only access their own tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        return current_user
    
    return check_tenant_access


def validate_tenant_context(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: Optional[str] = None
) -> str:
    """
    Dependency to validate and return the appropriate tenant context.
    
    If tenant_id is provided, validates access to that tenant.
    Otherwise, returns the user's default tenant.
    """
    if tenant_id:
        # Validate access to specified tenant
        if not current_user.is_admin() and current_user.tenant_id != tenant_id:
            logger.warning(
                f"User {current_user.user_id} attempted to access tenant {tenant_id} "
                f"but belongs to tenant {current_user.tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        return tenant_id
    
    # Return user's default tenant
    return current_user.tenant_id


def require_permission(resource: str, action: str):
    """
    Dependency factory to require specific permissions.
    
    Usage:
        @app.get("/data")
        def get_data(user: UserContext = Depends(require_permission("data", "read"))):
            pass
    """
    def check_permission(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        # Admin users have all permissions
        if current_user.is_admin():
            return current_user
        
        # Check role-based permissions
        allowed = _check_role_permissions(current_user.roles, resource, action)
        
        if not allowed:
            logger.warning(
                f"User {current_user.user_id} with roles {current_user.roles} "
                f"denied access to {resource}:{action}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for {resource}:{action}"
            )
        
        return current_user
    
    return check_permission


def require_tenant_isolation(allow_cross_tenant_admin: bool = True):
    """
    Dependency factory to enforce tenant isolation for data access.
    
    Usage:
        @app.get("/tenant/{tenant_id}/logs")
        def get_logs(
            tenant_id: str,
            user: UserContext = Depends(require_tenant_isolation())
        ):
            pass
    """
    def check_tenant_isolation(
        request: Request,
        current_user: UserContext = Depends(get_current_user)
    ) -> UserContext:
        # Extract tenant_id from path parameters
        path_params = request.path_params
        tenant_id = path_params.get("tenant_id")
        
        if tenant_id:
            # Admin users can access other tenants if allowed
            if allow_cross_tenant_admin and current_user.is_admin():
                logger.info(
                    f"Admin user {current_user.user_id} accessing tenant {tenant_id}"
                )
                return current_user
            
            # Regular users can only access their own tenant
            if current_user.tenant_id != tenant_id:
                logger.warning(
                    f"User {current_user.user_id} attempted cross-tenant access: "
                    f"own={current_user.tenant_id}, requested={tenant_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-tenant access denied"
                )
        
        return current_user
    
    return check_tenant_isolation


def _check_role_permissions(roles: List[str], resource: str, action: str) -> bool:
    """
    Check if any of the user's roles allow the specified resource/action.
    
    This implements a basic RBAC model. In production, this would likely
    be replaced with a more sophisticated permission system.
    """
    # Define role-based permissions
    role_permissions = {
        "admin": ["*:*"],  # Admin can do everything
        "user": [
            "logs:read", "metrics:read", "traces:read", "alerts:read",
            "search:read", "insights:read", "profile:read", "profile:write"
        ],
        "viewer": [
            "logs:read", "metrics:read", "traces:read", "alerts:read",
            "search:read", "insights:read", "profile:read"
        ],
        "editor": [
            "logs:read", "metrics:read", "traces:read", 
            "alerts:read", "alerts:write", "alerts:acknowledge",
            "search:read", "insights:read", "profile:read", "profile:write"
        ],
        "analyst": [
            "logs:read", "metrics:read", "traces:read", "alerts:read",
            "search:read", "search:advanced", "insights:read", "insights:write",
            "profile:read", "profile:write"
        ]
    }
    
    # Check each role
    for role in roles:
        permissions = role_permissions.get(role, [])
        
        # Check for wildcard permission
        if "*:*" in permissions:
            return True
        
        # Check for exact match
        permission = f"{resource}:{action}"
        if permission in permissions:
            return True
        
        # Check for resource wildcard
        resource_wildcard = f"{resource}:*"
        if resource_wildcard in permissions:
            return True
    
    return False


def enforce_data_isolation(
    query_filters: Optional[dict] = None,
    current_user: UserContext = Depends(get_current_user)
) -> dict:
    """
    Dependency to enforce tenant isolation in data queries.
    
    This adds tenant_id filters to data queries to ensure users
    only see data from their own tenant.
    
    Usage:
        @app.post("/search")
        def search(
            query: SearchQuery,
            filters: dict = Depends(enforce_data_isolation)
        ):
            # filters will include tenant_id constraint
            pass
    """
    filters = query_filters or {}
    
    # Admin users can optionally bypass tenant isolation
    # if they explicitly request cross-tenant access
    if current_user.is_admin() and filters.get("cross_tenant") is True:
        logger.info(f"Admin user {current_user.user_id} performing cross-tenant query")
        # Remove the cross_tenant flag but don't add tenant filter
        filters.pop("cross_tenant", None)
        return filters
    
    # Add tenant isolation filter
    filters["tenant_id"] = current_user.tenant_id
    
    logger.debug(f"Applied tenant isolation filter for user {current_user.user_id}")
    return filters