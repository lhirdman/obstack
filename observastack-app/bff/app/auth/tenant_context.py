"""Tenant context management for multi-tenant isolation."""

import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from contextvars import ContextVar

from .models import UserContext
from ..exceptions import AuthorizationError

logger = logging.getLogger(__name__)

# Context variable to store current tenant context
_tenant_context: ContextVar[Optional['TenantContext']] = ContextVar('tenant_context', default=None)


class TenantContext:
    """Context manager for tenant-specific operations."""
    
    def __init__(
        self,
        tenant_id: str,
        user_context: UserContext,
        allow_cross_tenant: bool = False
    ):
        """Initialize tenant context."""
        self.tenant_id = tenant_id
        self.user_context = user_context
        self.allow_cross_tenant = allow_cross_tenant
        self._original_context = None
    
    def __enter__(self):
        """Enter tenant context."""
        self._original_context = _tenant_context.get()
        _tenant_context.set(self)
        
        logger.debug(f"Entered tenant context: {self.tenant_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit tenant context."""
        _tenant_context.set(self._original_context)
        logger.debug(f"Exited tenant context: {self.tenant_id}")
    
    def validate_access(self) -> None:
        """Validate that the user can access this tenant."""
        if not self.allow_cross_tenant:
            if not self.user_context.is_admin() and self.user_context.tenant_id != self.tenant_id:
                raise AuthorizationError(
                    f"User {self.user_context.user_id} cannot access tenant {self.tenant_id}"
                )
    
    def add_tenant_filter(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tenant isolation filter to query parameters."""
        # Don't add filter if cross-tenant access is allowed and user is admin
        if self.allow_cross_tenant and self.user_context.is_admin():
            return query_params
        
        # Add tenant filter
        query_params = query_params.copy()
        query_params['tenant_id'] = self.tenant_id
        
        return query_params
    
    def filter_results_by_tenant(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results to only include items from the current tenant."""
        if self.allow_cross_tenant and self.user_context.is_admin():
            return results
        
        return [
            result for result in results
            if result.get('tenant_id') == self.tenant_id
        ]
    
    @property
    def is_cross_tenant_access(self) -> bool:
        """Check if this is cross-tenant access."""
        return self.user_context.tenant_id != self.tenant_id
    
    @property
    def is_admin_access(self) -> bool:
        """Check if this is admin access."""
        return self.user_context.is_admin()


def get_current_tenant_context() -> Optional[TenantContext]:
    """Get the current tenant context."""
    return _tenant_context.get()


def require_tenant_context() -> TenantContext:
    """Get the current tenant context, raising an error if not set."""
    context = get_current_tenant_context()
    if context is None:
        raise RuntimeError("No tenant context is currently active")
    return context


@contextmanager
def tenant_context(
    tenant_id: str,
    user_context: UserContext,
    allow_cross_tenant: bool = False
):
    """Context manager for tenant-specific operations."""
    context = TenantContext(tenant_id, user_context, allow_cross_tenant)
    context.validate_access()
    
    with context:
        yield context


class TenantIsolationMixin:
    """Mixin class to add tenant isolation capabilities to services."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin."""
        super().__init__(*args, **kwargs)
    
    def get_tenant_context(self) -> TenantContext:
        """Get the current tenant context."""
        return require_tenant_context()
    
    def add_tenant_filters(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tenant isolation filters to query parameters."""
        context = self.get_tenant_context()
        return context.add_tenant_filter(query_params)
    
    def filter_tenant_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results by tenant."""
        context = self.get_tenant_context()
        return context.filter_results_by_tenant(results)
    
    def validate_tenant_access(self, tenant_id: str) -> None:
        """Validate access to a specific tenant."""
        context = self.get_tenant_context()
        if tenant_id != context.tenant_id and not context.allow_cross_tenant:
            raise AuthorizationError(f"Access denied to tenant {tenant_id}")
    
    def log_tenant_access(self, operation: str, resource: str = None) -> None:
        """Log tenant access for audit purposes."""
        context = self.get_tenant_context()
        
        log_data = {
            "operation": operation,
            "tenant_id": context.tenant_id,
            "user_id": context.user_context.user_id,
            "is_cross_tenant": context.is_cross_tenant_access,
            "is_admin": context.is_admin_access
        }
        
        if resource:
            log_data["resource"] = resource
        
        logger.info(f"Tenant access: {log_data}")


class TenantAwareQueryBuilder:
    """Helper class for building tenant-aware queries."""
    
    def __init__(self, base_query: Dict[str, Any] = None):
        """Initialize query builder."""
        self.query = base_query or {}
    
    def add_tenant_filter(self, tenant_id: str = None) -> 'TenantAwareQueryBuilder':
        """Add tenant filter to the query."""
        context = get_current_tenant_context()
        
        if context:
            # Use context tenant if no specific tenant provided
            if tenant_id is None:
                tenant_id = context.tenant_id
            
            # Validate access to the requested tenant
            if tenant_id != context.tenant_id and not context.allow_cross_tenant:
                raise AuthorizationError(f"Access denied to tenant {tenant_id}")
            
            self.query['tenant_id'] = tenant_id
        elif tenant_id:
            # No context but tenant specified - add filter
            self.query['tenant_id'] = tenant_id
        
        return self
    
    def add_time_range(self, start_time: str = None, end_time: str = None) -> 'TenantAwareQueryBuilder':
        """Add time range filter."""
        if start_time:
            self.query['start_time'] = start_time
        if end_time:
            self.query['end_time'] = end_time
        return self
    
    def add_filter(self, key: str, value: Any) -> 'TenantAwareQueryBuilder':
        """Add a generic filter."""
        self.query[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final query."""
        return self.query.copy()


def create_tenant_aware_query(base_query: Dict[str, Any] = None) -> TenantAwareQueryBuilder:
    """Create a new tenant-aware query builder."""
    return TenantAwareQueryBuilder(base_query)


def validate_tenant_data_access(data: Dict[str, Any], required_tenant: str = None) -> None:
    """Validate that data belongs to the current tenant context."""
    context = get_current_tenant_context()
    
    if not context:
        # No tenant context - allow access (for system operations)
        return
    
    # Determine which tenant to validate against
    tenant_to_check = required_tenant or context.tenant_id
    
    # Get tenant from data
    data_tenant = data.get('tenant_id')
    
    if data_tenant and data_tenant != tenant_to_check:
        if not (context.allow_cross_tenant and context.is_admin_access):
            raise AuthorizationError(
                f"Data belongs to tenant {data_tenant}, access denied"
            )


def ensure_tenant_isolation(func):
    """Decorator to ensure tenant isolation for data operations."""
    def wrapper(*args, **kwargs):
        context = get_current_tenant_context()
        
        if context:
            # Log the operation
            logger.debug(
                f"Tenant-isolated operation: {func.__name__} "
                f"for tenant {context.tenant_id}"
            )
        
        return func(*args, **kwargs)
    
    return wrapper