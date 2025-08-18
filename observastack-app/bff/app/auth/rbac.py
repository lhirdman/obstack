"""Role-Based Access Control (RBAC) utilities and decorators."""

import logging
from typing import List, Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum

from .models import UserContext
from ..exceptions import AuthorizationError

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Enumeration of system permissions."""
    
    # Data access permissions
    LOGS_READ = "logs:read"
    LOGS_WRITE = "logs:write"
    METRICS_READ = "metrics:read"
    METRICS_WRITE = "metrics:write"
    TRACES_READ = "traces:read"
    TRACES_WRITE = "traces:write"
    
    # Alert permissions
    ALERTS_READ = "alerts:read"
    ALERTS_WRITE = "alerts:write"
    ALERTS_ACKNOWLEDGE = "alerts:acknowledge"
    ALERTS_RESOLVE = "alerts:resolve"
    ALERTS_ASSIGN = "alerts:assign"
    
    # Search permissions
    SEARCH_READ = "search:read"
    SEARCH_ADVANCED = "search:advanced"
    SEARCH_EXPORT = "search:export"
    
    # Insights permissions
    INSIGHTS_READ = "insights:read"
    INSIGHTS_WRITE = "insights:write"
    INSIGHTS_EXPORT = "insights:export"
    
    # Admin permissions
    TENANT_MANAGE = "tenant:manage"
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    SYSTEM_CONFIG = "system:config"
    
    # Profile permissions
    PROFILE_READ = "profile:read"
    PROFILE_WRITE = "profile:write"


class Role(Enum):
    """Enumeration of system roles."""
    
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    EDITOR = "editor"
    ANALYST = "analyst"
    TENANT_ADMIN = "tenant_admin"


class RBACManager:
    """Manages role-based access control logic."""
    
    def __init__(self):
        """Initialize RBAC manager with default role permissions."""
        self._role_permissions = self._get_default_role_permissions()
    
    def _get_default_role_permissions(self) -> Dict[str, List[Permission]]:
        """Get default permissions for each role."""
        return {
            Role.ADMIN.value: [
                # Admin has all permissions
                Permission.LOGS_READ, Permission.LOGS_WRITE,
                Permission.METRICS_READ, Permission.METRICS_WRITE,
                Permission.TRACES_READ, Permission.TRACES_WRITE,
                Permission.ALERTS_READ, Permission.ALERTS_WRITE,
                Permission.ALERTS_ACKNOWLEDGE, Permission.ALERTS_RESOLVE,
                Permission.ALERTS_ASSIGN,
                Permission.SEARCH_READ, Permission.SEARCH_ADVANCED,
                Permission.SEARCH_EXPORT,
                Permission.INSIGHTS_READ, Permission.INSIGHTS_WRITE,
                Permission.INSIGHTS_EXPORT,
                Permission.TENANT_MANAGE, Permission.USER_MANAGE,
                Permission.ROLE_MANAGE, Permission.SYSTEM_CONFIG,
                Permission.PROFILE_READ, Permission.PROFILE_WRITE
            ],
            
            Role.TENANT_ADMIN.value: [
                # Tenant admin can manage users and data within their tenant
                Permission.LOGS_READ, Permission.LOGS_WRITE,
                Permission.METRICS_READ, Permission.METRICS_WRITE,
                Permission.TRACES_READ, Permission.TRACES_WRITE,
                Permission.ALERTS_READ, Permission.ALERTS_WRITE,
                Permission.ALERTS_ACKNOWLEDGE, Permission.ALERTS_RESOLVE,
                Permission.ALERTS_ASSIGN,
                Permission.SEARCH_READ, Permission.SEARCH_ADVANCED,
                Permission.SEARCH_EXPORT,
                Permission.INSIGHTS_READ, Permission.INSIGHTS_WRITE,
                Permission.INSIGHTS_EXPORT,
                Permission.USER_MANAGE, Permission.ROLE_MANAGE,
                Permission.PROFILE_READ, Permission.PROFILE_WRITE
            ],
            
            Role.ANALYST.value: [
                # Analyst can read all data and perform advanced analysis
                Permission.LOGS_READ, Permission.METRICS_READ,
                Permission.TRACES_READ, Permission.ALERTS_READ,
                Permission.SEARCH_READ, Permission.SEARCH_ADVANCED,
                Permission.SEARCH_EXPORT,
                Permission.INSIGHTS_READ, Permission.INSIGHTS_WRITE,
                Permission.INSIGHTS_EXPORT,
                Permission.PROFILE_READ, Permission.PROFILE_WRITE
            ],
            
            Role.EDITOR.value: [
                # Editor can read data and manage alerts
                Permission.LOGS_READ, Permission.METRICS_READ,
                Permission.TRACES_READ, Permission.ALERTS_READ,
                Permission.ALERTS_WRITE, Permission.ALERTS_ACKNOWLEDGE,
                Permission.ALERTS_RESOLVE, Permission.ALERTS_ASSIGN,
                Permission.SEARCH_READ, Permission.INSIGHTS_READ,
                Permission.PROFILE_READ, Permission.PROFILE_WRITE
            ],
            
            Role.USER.value: [
                # Regular user can read data and basic search
                Permission.LOGS_READ, Permission.METRICS_READ,
                Permission.TRACES_READ, Permission.ALERTS_READ,
                Permission.SEARCH_READ, Permission.INSIGHTS_READ,
                Permission.PROFILE_READ, Permission.PROFILE_WRITE
            ],
            
            Role.VIEWER.value: [
                # Viewer has read-only access
                Permission.LOGS_READ, Permission.METRICS_READ,
                Permission.TRACES_READ, Permission.ALERTS_READ,
                Permission.SEARCH_READ, Permission.INSIGHTS_READ,
                Permission.PROFILE_READ
            ]
        }
    
    def has_permission(self, user_context: UserContext, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        # Admin role has all permissions
        if user_context.is_admin():
            return True
        
        # Check each role for the permission
        for role in user_context.roles:
            role_permissions = self._role_permissions.get(role, [])
            if permission in role_permissions:
                return True
        
        return False
    
    def has_any_permission(self, user_context: UserContext, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(user_context, perm) for perm in permissions)
    
    def has_all_permissions(self, user_context: UserContext, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(self.has_permission(user_context, perm) for perm in permissions)
    
    def get_user_permissions(self, user_context: UserContext) -> List[Permission]:
        """Get all permissions for a user."""
        if user_context.is_admin():
            # Admin has all permissions
            return list(Permission)
        
        permissions = set()
        for role in user_context.roles:
            role_permissions = self._role_permissions.get(role, [])
            permissions.update(role_permissions)
        
        return list(permissions)
    
    def can_access_tenant(self, user_context: UserContext, tenant_id: str) -> bool:
        """Check if user can access a specific tenant."""
        # Admin can access any tenant
        if user_context.is_admin():
            return True
        
        # Users can only access their own tenant
        return user_context.tenant_id == tenant_id
    
    def validate_tenant_access(self, user_context: UserContext, tenant_id: str) -> None:
        """Validate tenant access and raise exception if denied."""
        if not self.can_access_tenant(user_context, tenant_id):
            logger.warning(
                f"User {user_context.user_id} denied access to tenant {tenant_id}"
            )
            raise AuthorizationError(f"Access denied to tenant {tenant_id}")
    
    def validate_permission(self, user_context: UserContext, permission: Permission) -> None:
        """Validate permission and raise exception if denied."""
        if not self.has_permission(user_context, permission):
            logger.warning(
                f"User {user_context.user_id} denied permission {permission.value}"
            )
            raise AuthorizationError(f"Permission denied: {permission.value}")
    
    def add_role_permission(self, role: str, permission: Permission) -> None:
        """Add a permission to a role."""
        if role not in self._role_permissions:
            self._role_permissions[role] = []
        
        if permission not in self._role_permissions[role]:
            self._role_permissions[role].append(permission)
            logger.info(f"Added permission {permission.value} to role {role}")
    
    def remove_role_permission(self, role: str, permission: Permission) -> None:
        """Remove a permission from a role."""
        if role in self._role_permissions:
            if permission in self._role_permissions[role]:
                self._role_permissions[role].remove(permission)
                logger.info(f"Removed permission {permission.value} from role {role}")


# Global RBAC manager instance
rbac_manager = RBACManager()


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for a function.
    
    Usage:
        @require_permission(Permission.LOGS_READ)
        def get_logs(user_context: UserContext):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find UserContext in arguments
            user_context = None
            for arg in args:
                if isinstance(arg, UserContext):
                    user_context = arg
                    break
            
            if not user_context:
                # Look in kwargs
                for value in kwargs.values():
                    if isinstance(value, UserContext):
                        user_context = value
                        break
            
            if not user_context:
                raise AuthorizationError("User context not found in function arguments")
            
            # Validate permission
            rbac_manager.validate_permission(user_context, permission)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @require_any_permission([Permission.LOGS_READ, Permission.METRICS_READ])
        def get_data(user_context: UserContext):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find UserContext in arguments
            user_context = None
            for arg in args:
                if isinstance(arg, UserContext):
                    user_context = arg
                    break
            
            if not user_context:
                # Look in kwargs
                for value in kwargs.values():
                    if isinstance(value, UserContext):
                        user_context = value
                        break
            
            if not user_context:
                raise AuthorizationError("User context not found in function arguments")
            
            # Check if user has any of the required permissions
            if not rbac_manager.has_any_permission(user_context, permissions):
                permission_names = [p.value for p in permissions]
                raise AuthorizationError(f"One of these permissions required: {', '.join(permission_names)}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_tenant_access(tenant_id_param: str = "tenant_id"):
    """
    Decorator to require access to a specific tenant.
    
    Usage:
        @require_tenant_access("tenant_id")
        def get_tenant_data(tenant_id: str, user_context: UserContext):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find UserContext and tenant_id in arguments
            user_context = None
            tenant_id = None
            
            # Look for UserContext
            for arg in args:
                if isinstance(arg, UserContext):
                    user_context = arg
                    break
            
            if not user_context:
                for value in kwargs.values():
                    if isinstance(value, UserContext):
                        user_context = value
                        break
            
            # Look for tenant_id
            tenant_id = kwargs.get(tenant_id_param)
            
            if not user_context:
                raise AuthorizationError("User context not found in function arguments")
            
            if not tenant_id:
                raise AuthorizationError(f"Tenant ID parameter '{tenant_id_param}' not found")
            
            # Validate tenant access
            rbac_manager.validate_tenant_access(user_context, tenant_id)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_rbac_manager() -> RBACManager:
    """Get the global RBAC manager instance."""
    return rbac_manager