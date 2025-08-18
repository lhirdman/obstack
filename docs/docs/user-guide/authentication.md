# Authentication

ObservaStack provides secure authentication and authorization through integration with Keycloak, supporting multi-tenant environments with role-based access control (RBAC).

## Overview

ObservaStack's authentication system provides:

- **Single Sign-On (SSO)** through Keycloak
- **Multi-tenant isolation** with tenant-specific access
- **Role-based permissions** for different user types
- **JWT token-based** API authentication
- **Session management** with automatic token refresh

## User Roles

### System Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | System administrator | Full access to all tenants and system configuration |
| **Tenant Admin** | Tenant administrator | Full access within assigned tenant(s) |
| **User** | Standard user | Read/write access to assigned resources |
| **Viewer** | Read-only user | View-only access to dashboards and data |

### Tenant-Specific Permissions

Each role can be scoped to specific tenants:

- **Global**: Access across all tenants (Admin only)
- **Tenant-specific**: Access limited to assigned tenant(s)
- **Resource-specific**: Access to specific dashboards, alerts, or data sources

## Getting Started

### First Login

1. Navigate to ObservaStack in your browser
2. Click **Sign In** to be redirected to Keycloak
3. Enter your credentials or use SSO provider
4. Complete any required profile setup
5. You'll be redirected back to ObservaStack

### Default Credentials

For development environments:

- **Username**: `admin`
- **Password**: `admin`
- **Tenant**: `default`

:::warning Production Security
Change default credentials immediately in production environments!
:::

## User Management

### Creating Users

Administrators can create users through the Keycloak admin console:

1. Access Keycloak admin at `http://your-domain:8080/admin`
2. Navigate to **Users** → **Add User**
3. Fill in user details:
   ```
   Username: john.doe
   Email: john.doe@company.com
   First Name: John
   Last Name: Doe
   ```
4. Set temporary password in **Credentials** tab
5. Assign roles in **Role Mappings** tab

### Assigning Roles

To assign roles to users:

1. In Keycloak admin, select the user
2. Go to **Role Mappings** tab
3. Select **Client Roles** → **observastack-app**
4. Assign appropriate roles:
   - `observastack-admin`
   - `observastack-user`
   - `observastack-viewer`

### Tenant Assignment

Assign users to specific tenants:

1. In user's **Attributes** tab, add:
   ```
   tenant_id: your-tenant-id
   tenant_name: Your Tenant Name
   ```
2. For multiple tenants, use comma-separated values:
   ```
   tenant_id: tenant1,tenant2,tenant3
   ```

## Multi-Tenant Configuration

### Tenant Isolation

ObservaStack enforces tenant isolation at multiple levels:

#### Data Level
- **Logs**: Filtered by tenant labels in Loki
- **Metrics**: Scoped by tenant-specific Prometheus instances
- **Traces**: Isolated by tenant metadata in Tempo
- **Dashboards**: Tenant-specific Grafana organizations

#### API Level
```python
# All API calls include tenant context
@router.get("/search")
async def search(
    query: SearchQuery,
    current_user: User = Depends(get_current_user)
):
    # Automatically filters by user's tenant
    tenant_id = current_user.tenant_id
    results = await search_service.search(query, tenant_id)
    return results
```

#### UI Level
- Navigation filtered by tenant permissions
- Data visualizations scoped to tenant data
- Branding customized per tenant

### Tenant Configuration

Configure tenants in the admin interface:

```json
{
  "tenant_id": "acme-corp",
  "name": "ACME Corporation",
  "domain": "acme.com",
  "branding": {
    "logo_url": "/assets/acme-logo.png",
    "primary_color": "#1a365d",
    "secondary_color": "#3182ce"
  },
  "data_sources": {
    "prometheus_url": "http://prometheus-acme:9090",
    "loki_url": "http://loki-acme:3100",
    "tempo_url": "http://tempo-acme:3200"
  },
  "features": {
    "alerts": true,
    "insights": true,
    "custom_dashboards": true
  }
}
```

## API Authentication

### JWT Tokens

ObservaStack uses JWT tokens for API authentication:

#### Token Structure
```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "tenant_id": "acme-corp",
  "roles": ["observastack-user"],
  "exp": 1692123456,
  "iat": 1692120456
}
```

#### Using Tokens

Include the JWT token in API requests:

```bash
# Get token from login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:8000/api/search
```

### Token Refresh

Tokens are automatically refreshed by the frontend:

```typescript
// Automatic token refresh
const apiClient = new ApiClient({
  baseURL: '/api',
  tokenRefreshHandler: async () => {
    const newToken = await authService.refreshToken();
    return newToken;
  }
});
```

## SSO Integration

### SAML Configuration

Configure SAML SSO in Keycloak:

1. **Create Identity Provider**:
   ```xml
   <EntityDescriptor entityID="https://your-idp.com">
     <IDPSSODescriptor>
       <SingleSignOnService 
         Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
         Location="https://your-idp.com/sso" />
     </IDPSSODescriptor>
   </EntityDescriptor>
   ```

2. **Configure Attribute Mapping**:
   ```
   email → email
   firstName → first_name
   lastName → last_name
   department → tenant_id
   ```

### OIDC Configuration

For OpenID Connect providers:

```json
{
  "client_id": "observastack",
  "client_secret": "your-secret",
  "issuer": "https://your-oidc-provider.com",
  "redirect_uri": "http://localhost:3000/auth/callback",
  "scopes": ["openid", "profile", "email", "groups"]
}
```

## Security Best Practices

### Password Policies

Configure strong password policies in Keycloak:

```json
{
  "minimumLength": 12,
  "requireUppercase": true,
  "requireLowercase": true,
  "requireNumbers": true,
  "requireSpecialChars": true,
  "passwordHistory": 5,
  "maxAge": 90
}
```

### Session Security

```bash
# Secure session configuration
SESSION_TIMEOUT=3600          # 1 hour
IDLE_TIMEOUT=1800            # 30 minutes
REQUIRE_HTTPS=true           # Production only
SECURE_COOKIES=true          # Production only
SAME_SITE_COOKIES=strict     # CSRF protection
```

### Rate Limiting

Protect against brute force attacks:

```python
# Rate limiting configuration
RATE_LIMIT_LOGIN = "5/minute"
RATE_LIMIT_API = "100/minute"
RATE_LIMIT_SEARCH = "20/minute"
```

## Troubleshooting

### Common Issues

#### Login Redirect Loop
```bash
# Check Keycloak configuration
curl http://localhost:8080/realms/observastack/.well-known/openid_configuration

# Verify redirect URIs match
# Frontend: http://localhost:3000/*
# Backend: http://localhost:8000/auth/callback
```

#### Token Validation Errors
```bash
# Check JWT token validity
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/auth/validate

# Verify token hasn't expired
echo "<token>" | base64 -d | jq .exp
```

#### Tenant Access Denied
```bash
# Check user's tenant assignment
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/user/profile

# Verify tenant exists and is active
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:8000/api/admin/tenants
```

### Debug Mode

Enable authentication debugging:

```bash
# Backend debugging
KEYCLOAK_DEBUG=true
JWT_DEBUG=true
AUTH_LOG_LEVEL=debug

# Frontend debugging
VITE_AUTH_DEBUG=true
```

## Next Steps

- [Configure search permissions](search.md)
- [Set up alert notifications](alerts.md)
- [Customize tenant branding](dashboards.md)
- [Monitor authentication metrics](../troubleshooting/debugging.md)