"""Authentication module for ObservaStack BFF."""

from .middleware import JWTAuthMiddleware
from .dependencies import (
    get_current_user, 
    get_current_tenant, 
    require_auth,
    require_roles,
    require_admin,
    require_tenant_access,
    validate_tenant_context,
    require_permission,
    require_tenant_isolation,
    enforce_data_isolation
)
from .jwt_handler import JWTHandler
from .models import JWTPayload, UserContext, TokenRefreshContext
from .service import AuthService
from .rbac import (
    RBACManager,
    Permission,
    Role,
    rbac_manager,
    require_permission as rbac_require_permission,
    require_any_permission,
    require_tenant_access as rbac_require_tenant_access,
    get_rbac_manager
)
from .tenant_context import (
    TenantContext,
    tenant_context,
    TenantIsolationMixin,
    TenantAwareQueryBuilder,
    create_tenant_aware_query,
    get_current_tenant_context,
    require_tenant_context,
    validate_tenant_data_access,
    ensure_tenant_isolation
)

__all__ = [
    # Core components
    "JWTAuthMiddleware",
    "JWTHandler",
    "AuthService",
    "JWTPayload",
    "UserContext",
    "TokenRefreshContext",
    
    # FastAPI dependencies
    "get_current_user", 
    "get_current_tenant",
    "require_auth",
    "require_roles",
    "require_admin",
    "require_tenant_access",
    "validate_tenant_context",
    "require_permission",
    "require_tenant_isolation",
    "enforce_data_isolation",
    
    # RBAC components
    "RBACManager",
    "Permission",
    "Role",
    "rbac_manager",
    "rbac_require_permission",
    "require_any_permission",
    "rbac_require_tenant_access",
    "get_rbac_manager",
    
    # Tenant context management
    "TenantContext",
    "tenant_context",
    "TenantIsolationMixin",
    "TenantAwareQueryBuilder",
    "create_tenant_aware_query",
    "get_current_tenant_context",
    "require_tenant_context",
    "validate_tenant_data_access",
    "ensure_tenant_isolation"
]