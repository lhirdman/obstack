# Keycloak Integration

This guide explains how to configure and use Keycloak for OIDC-based authentication in ObservaStack, enabling Enterprise customers with SSO requirements.

## Overview

ObservaStack supports two authentication methods:
- **Local Authentication**: Traditional username/password with JWT tokens
- **Keycloak Authentication**: OIDC-based authentication using Keycloak as the identity provider

## Configuration

### Environment Variables

To enable Keycloak authentication, set the following environment variables:

```bash
# Authentication Method
AUTH_METHOD=keycloak

# Keycloak Configuration (Required)
KEYCLOAK_SERVER_URL=https://your-keycloak-server.com
KEYCLOAK_REALM=your-realm-name
KEYCLOAK_CLIENT_ID=observastack-client

# Optional: For confidential clients
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

### Keycloak Setup

1. **Create a Realm**: Create a new realm in Keycloak or use an existing one.

2. **Create a Client**: 
   - Client ID: `observastack-client` (or your preferred name)
   - Client Protocol: `openid-connect`
   - Access Type: `public` (for frontend) or `confidential` (for backend-only)
   - Valid Redirect URIs: Add your application URLs
   - Web Origins: Add your application domains

3. **Configure Client Scopes**: Ensure the following scopes are available:
   - `openid`
   - `profile`
   - `email`
   - `roles` (for role mapping)

4. **User Attributes**: Configure custom attributes if needed for tenant mapping:
   - `tenant`
   - `organization`
   - `company`

## How It Works

### JWT Validation Flow

1. **Token Reception**: The backend receives JWT tokens from:
   - `Authorization: Bearer <token>` header
   - `access_token` HttpOnly cookie

2. **Token Validation**: 
   - Fetches JWKS (JSON Web Key Set) from Keycloak
   - Validates token signature using public keys
   - Verifies token claims (issuer, audience, expiration)

3. **User Information Extraction**:
   - Extracts user details from token claims
   - Maps Keycloak roles to internal application roles
   - Determines tenant association

4. **User Management**:
   - Creates new users automatically on first login
   - Updates existing user information and roles
   - Associates users with appropriate tenants

### Role Mapping

Keycloak roles are automatically mapped to internal application roles:

| Keycloak Role | Internal Role | Description |
|---------------|---------------|-------------|
| `admin`, `realm-admin` | `admin` | Full system administration |
| `manager`, `team-lead` | `manager` | Team and resource management |
| `user`, `member` | `user` | Standard user access |
| `viewer`, `read-only` | `viewer` | Read-only access |

Client-specific roles are also supported with the `client:` prefix.

### Tenant Association

The system attempts to determine tenant association using these token claims (in order):
1. `tenant`
2. `organization` 
3. `org`
4. `company`
5. `tenant_id`
6. `org_id`

If no tenant claim is found, the Keycloak realm name is used as the tenant identifier.

## API Endpoints

### Authentication Information

```http
GET /api/v1/auth/auth-info
```

Returns current authentication configuration:

```json
{
  "auth_method": "keycloak",
  "supports_local_auth": false,
  "supports_keycloak_auth": true,
  "keycloak_server_url": "https://your-keycloak-server.com",
  "keycloak_realm": "your-realm-name",
  "keycloak_client_id": "observastack-client",
  "keycloak_auth_url": "https://your-keycloak-server.com/realms/your-realm-name/protocol/openid_connect/auth",
  "keycloak_token_url": "https://your-keycloak-server.com/realms/your-realm-name/protocol/openid_connect/token"
}
```

### User Information

```http
GET /api/v1/auth/me
Authorization: Bearer <keycloak-jwt-token>
```

Returns user information extracted from the Keycloak token.

## Frontend Integration

When using Keycloak authentication, the frontend should:

1. **Check Authentication Method**:
   ```javascript
   const authInfo = await fetch('/api/v1/auth/auth-info').then(r => r.json());
   if (authInfo.auth_method === 'keycloak') {
     // Use Keycloak authentication flow
   }
   ```

2. **Redirect to Keycloak**: Instead of showing a login form, redirect users to Keycloak:
   ```javascript
   const authUrl = `${authInfo.keycloak_auth_url}?client_id=${authInfo.keycloak_client_id}&redirect_uri=${encodeURIComponent(window.location.origin)}&response_type=code&scope=openid profile email`;
   window.location.href = authUrl;
   ```

3. **Handle Authorization Code**: Process the authorization code returned by Keycloak and exchange it for tokens.

## Security Considerations

### Token Validation
- All JWT tokens are validated against Keycloak's public keys
- Token expiration, issuer, and audience are strictly verified
- Invalid or expired tokens are rejected

### User Data Synchronization
- User information is synchronized on each authentication
- Role changes in Keycloak are reflected immediately
- Tenant associations are updated based on token claims

### Caching
- JWKS and realm information are cached for performance
- Cache can be cleared using the service's `clear_cache()` method
- Cache is automatically refreshed on validation failures

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure all required Keycloak environment variables are set
   - Verify `AUTH_METHOD=keycloak` is configured

2. **"Failed to fetch JWKS"**
   - Check network connectivity to Keycloak server
   - Verify `KEYCLOAK_SERVER_URL` is correct and accessible
   - Ensure Keycloak realm exists and is active

3. **"JWT validation failed"**
   - Verify token is not expired
   - Check that client ID matches configuration
   - Ensure token was issued by the correct Keycloak realm

4. **"No matching key found for kid"**
   - JWKS cache may be stale - restart the application
   - Verify Keycloak realm configuration
   - Check if Keycloak keys have been rotated

### Debugging

Enable debug logging to troubleshoot authentication issues:

```python
import logging
logging.getLogger('app.services.keycloak_service').setLevel(logging.DEBUG)
logging.getLogger('app.core.security').setLevel(logging.DEBUG)
```

### Testing Keycloak Integration

Use the provided test suite to verify Keycloak integration:

```bash
# Run Keycloak-specific tests
pytest apps/backend/tests/services/test_keycloak_service.py -v

# Run integration tests with Keycloak
pytest apps/backend/tests/integration/test_keycloak_auth.py -v
```

## Migration from Local Authentication

To migrate from local to Keycloak authentication:

1. **Set up Keycloak** with appropriate realm and client configuration
2. **Import existing users** into Keycloak (optional)
3. **Update environment variables** to use Keycloak
4. **Restart the application** to apply new configuration
5. **Update frontend** to use Keycloak authentication flow

Note: Existing local user accounts will remain in the database but will not be used for authentication when Keycloak mode is enabled.