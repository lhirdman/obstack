# RBAC and Tenant Isolation Implementation

This document describes the Role-Based Access Control (RBAC) and tenant isolation features implemented for the ObservaStack unified observability platform.

## Overview

The implementation provides:

1. **Multi-tenant context management** - Ensures data isolation between tenants
2. **Role-based access control** - Fine-grained permissions based on user roles
3. **JWT token integration** - Tenant and role information embedded in tokens
4. **FastAPI dependencies** - Easy integration with API endpoints
5. **Comprehensive testing** - Full test coverage for security features

## Architecture

### Core Components

#### 1. UserContext Model (`app/auth/models.py`)

```python
class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    roles: List[str]
    token_id: Optional[str]
    expires_at: datetime
    
    def has_role(self, role: str) -> bool
    def has_any_role(self, roles: List[str]) -> bool
    def is_admin(self) -> bool
```

#### 2. RBAC Manager (`app/auth/rbac.py`)

Manages role-based permissions with predefined roles:

- **Admin**: Full system access
- **Tenant Admin**: Manage users and data within tenant
- **Analyst**: Advanced data analysis capabilities
- **Editor**: Read data and manage alerts
- **User**: Basic data access
- **Viewer**: Read-only access

#### 3. Tenant Context Manager (`app/auth/tenant_context.py`)

Provides tenant isolation through context management:

```python
with tenant_context("tenant-a", user_context) as context:
    # All operations within this block are tenant-isolated
    filtered_data = context.filter_results_by_tenant(data)
```

#### 4. FastAPI Dependencies (`app/auth/dependencies.py`)

Ready-to-use dependencies for API endpoints:

```python
@app.get("/logs")
def get_logs(
    user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    filters: dict = Depends(enforce_data_isolation)
):
    # Automatically enforced tenant isolation and authentication
    pass
```

## Usage Examples

### 1. Basic RBAC Check

```python
from app.auth.rbac import rbac_manager, Permission

# Check if user has permission
if rbac_manager.has_permission(user_context, Permission.LOGS_READ):
    # User can read logs
    logs = get_logs()
```

### 2. Decorator-Based Permission Checking

```python
from app.auth.rbac import require_permission, Permission

@require_permission(Permission.ALERTS_WRITE)
def create_alert(user_context: UserContext, alert_data: dict):
    # This function requires ALERTS_WRITE permission
    return create_new_alert(alert_data)
```

### 3. Tenant-Isolated Data Access

```python
from app.auth.tenant_context import tenant_context

with tenant_context("tenant-a", user_context) as context:
    # Add tenant filter to query
    query = context.add_tenant_filter({"search": "error"})
    
    # Execute query (automatically filtered by tenant)
    results = search_logs(query)
    
    # Filter results (additional safety)
    safe_results = context.filter_results_by_tenant(results)
```

### 4. Service with Tenant Isolation

```python
from app.auth.tenant_context import TenantIsolationMixin

class LogService(TenantIsolationMixin):
    def get_logs(self, filters: dict = None):
        # Automatically add tenant filters
        tenant_filters = self.add_tenant_filters(filters or {})
        
        # Query with tenant isolation
        results = self.query_logs(tenant_filters)
        
        # Log access for audit
        self.log_tenant_access("get_logs")
        
        return results
```

### 5. FastAPI Endpoint Integration

```python
from fastapi import Depends
from app.auth.dependencies import (
    get_current_user, 
    require_permission, 
    enforce_data_isolation
)

@app.get("/api/logs")
def get_logs(
    user: UserContext = Depends(get_current_user),
    _: UserContext = Depends(require_permission(Permission.LOGS_READ)),
    filters: dict = Depends(enforce_data_isolation)
):
    # User is authenticated, authorized, and filters include tenant isolation
    return log_service.get_logs(filters)

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    user: UserContext = Depends(require_roles(["editor", "admin"])),
    _: UserContext = Depends(require_tenant_isolation())
):
    # User has editor or admin role and can only access their tenant's alerts
    return alert_service.acknowledge(alert_id, user.user_id)
```

## Permissions Matrix

| Role | Logs | Metrics | Traces | Alerts | Search | Insights | Admin |
|------|------|---------|--------|--------|--------|----------|-------|
| **Viewer** | Read | Read | Read | Read | Basic | Read | ❌ |
| **User** | Read | Read | Read | Read | Basic | Read | ❌ |
| **Editor** | Read | Read | Read | Read/Write | Basic | Read | ❌ |
| **Analyst** | Read | Read | Read | Read | Advanced | Read/Write | ❌ |
| **Tenant Admin** | Read/Write | Read/Write | Read/Write | Read/Write | Advanced | Read/Write | Tenant |
| **Admin** | Read/Write | Read/Write | Read/Write | Read/Write | Advanced | Read/Write | Full |

## Security Features

### 1. JWT Token Integration

User context is extracted from JWT tokens containing:
- `sub`: User ID
- `tenant_id`: Tenant identifier
- `roles`: Array of user roles
- `exp`: Token expiration
- `jti`: Token ID for revocation

### 2. Tenant Isolation

Multiple layers of tenant isolation:
- **Query Level**: Automatic tenant filters added to database queries
- **Result Level**: Results filtered by tenant before returning
- **Context Level**: Tenant context enforced throughout request lifecycle
- **Validation Level**: Data validated to ensure tenant ownership

### 3. Cross-Tenant Access Control

Admin users can access other tenants when explicitly allowed:

```python
with tenant_context("other-tenant", admin_user, allow_cross_tenant=True):
    # Admin can access other tenant's data
    data = get_cross_tenant_data()
```

### 4. Audit Logging

All tenant access is logged for audit purposes:

```python
# Automatic logging in TenantIsolationMixin
self.log_tenant_access("operation_name", "resource_details")
```

## Testing

Comprehensive test suites cover:

### 1. RBAC Testing (`tests/test_rbac.py`)
- Permission validation for all roles
- Multi-role permission inheritance
- Permission decorators
- Cross-tenant access validation

### 2. Tenant Context Testing (`tests/test_tenant_context.py`)
- Tenant isolation enforcement
- Context manager functionality
- Query builder with tenant filters
- Data validation

### 3. Integration Testing (`tests/test_auth.py`)
- JWT token validation
- FastAPI dependency integration
- End-to-end authentication flows
- Error handling

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis Configuration (for session management)
REDIS_URL=redis://localhost:6379

# Keycloak Integration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=observastack
```

### Role Customization

Roles and permissions can be customized:

```python
from app.auth.rbac import rbac_manager, Permission

# Add custom permission to role
rbac_manager.add_role_permission("custom_role", Permission.LOGS_WRITE)

# Remove permission from role
rbac_manager.remove_role_permission("viewer", Permission.PROFILE_WRITE)
```

## Best Practices

### 1. Always Use Tenant Context

```python
# ✅ Good - Explicit tenant context
with tenant_context(tenant_id, user_context):
    data = service.get_data()

# ❌ Bad - No tenant isolation
data = service.get_data()
```

### 2. Validate Permissions Early

```python
# ✅ Good - Check permissions before processing
@require_permission(Permission.LOGS_WRITE)
def create_log(user_context: UserContext, log_data: dict):
    return process_log(log_data)

# ❌ Bad - Check permissions after processing
def create_log(user_context: UserContext, log_data: dict):
    result = process_log(log_data)  # Expensive operation
    if not has_permission(user_context, Permission.LOGS_WRITE):
        raise AuthorizationError()
    return result
```

### 3. Use Dependency Injection

```python
# ✅ Good - Use FastAPI dependencies
@app.get("/data")
def get_data(
    user: UserContext = Depends(get_current_user),
    filters: dict = Depends(enforce_data_isolation)
):
    return service.get_data(filters)

# ❌ Bad - Manual authentication
@app.get("/data")
def get_data(request: Request):
    user = manually_extract_user(request)
    if not user:
        raise HTTPException(401)
    # ... manual tenant filtering
```

### 4. Validate Data Ownership

```python
# ✅ Good - Validate data belongs to tenant
def update_alert(alert_id: int, user_context: UserContext):
    alert = get_alert(alert_id)
    validate_tenant_data_access(alert)  # Ensures alert belongs to user's tenant
    return update_alert_data(alert)

# ❌ Bad - No validation
def update_alert(alert_id: int, user_context: UserContext):
    alert = get_alert(alert_id)  # Could be from any tenant
    return update_alert_data(alert)
```

## Migration Guide

### Existing Endpoints

To add RBAC and tenant isolation to existing endpoints:

1. **Add authentication dependency**:
   ```python
   user: UserContext = Depends(get_current_user)
   ```

2. **Add permission checking**:
   ```python
   _: UserContext = Depends(require_permission(Permission.LOGS_READ))
   ```

3. **Add tenant isolation**:
   ```python
   filters: dict = Depends(enforce_data_isolation)
   ```

4. **Update service calls**:
   ```python
   with tenant_context(user.tenant_id, user):
       return service.get_data(filters)
   ```

### Database Queries

Ensure all queries include tenant filters:

```python
# Before
SELECT * FROM logs WHERE level = 'error'

# After  
SELECT * FROM logs WHERE level = 'error' AND tenant_id = ?
```

## Troubleshooting

### Common Issues

1. **"No tenant context is currently active"**
   - Ensure operations are wrapped in `tenant_context()`
   - Check that middleware is properly configured

2. **"Permission denied"**
   - Verify user has required role
   - Check permission is correctly defined
   - Ensure JWT token contains proper roles

3. **"Cross-tenant access denied"**
   - Verify admin user has proper permissions
   - Check `allow_cross_tenant=True` is set
   - Ensure tenant_id parameter is correct

### Debug Mode

Enable debug logging to trace permission checks:

```python
import logging
logging.getLogger("app.auth").setLevel(logging.DEBUG)
```

## Performance Considerations

1. **Permission Caching**: Permissions are cached per request
2. **Tenant Filtering**: Database indexes on `tenant_id` recommended
3. **JWT Validation**: Tokens validated once per request via middleware
4. **Context Variables**: Minimal overhead using Python contextvars

## Security Considerations

1. **Token Security**: Use strong JWT secrets in production
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Expiration**: Set appropriate token lifetimes
4. **Audit Logging**: Enable comprehensive audit logging
5. **Regular Reviews**: Periodically review roles and permissions