# Authentication System Documentation

## Overview

The ObservaStack frontend uses Keycloak for authentication and authorization. This system provides:

- **Single Sign-On (SSO)** integration with Keycloak
- **Multi-tenant** user isolation
- **Role-Based Access Control (RBAC)** with fine-grained permissions
- **Automatic token refresh** and session management
- **Protected routes** with role and permission checking

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │    Keycloak     │    │   FastAPI BFF   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │AuthProvider │◄┼────┼►│   Server    │ │    │ │   Auth      │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │ Middleware  │ │
│                 │    │                 │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │ Protected   │ │    │ │   Realm     │ │    │ ┌─────────────┐ │
│ │   Routes    │ │    │ │ observastack│ │    │ │   API       │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │ Endpoints   │ │
└─────────────────┘    └─────────────────┘    │ └─────────────┘ │
                                              └─────────────────┘
```

## Components

### AuthProvider

The main authentication context provider that wraps the entire application.

```tsx
import { AuthProvider, defaultKeycloakConfig } from './auth'

function App() {
  return (
    <AuthProvider config={defaultKeycloakConfig}>
      <YourApp />
    </AuthProvider>
  )
}
```

### Protected Routes

Components that require authentication and/or specific roles:

```tsx
import { ProtectedRoute, AdminRoute, PermissionRoute } from './auth'

// Basic authentication required
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

// Admin role required
<AdminRoute>
  <AdminPanel />
</AdminRoute>

// Specific permission required
<PermissionRoute resource="alerts" action="write">
  <AlertManagement />
</PermissionRoute>
```

### Hooks

#### useAuth()

Main authentication hook providing access to auth state and methods:

```tsx
import { useAuth } from './auth'

function MyComponent() {
  const { 
    isAuthenticated, 
    isLoading, 
    user, 
    login, 
    logout, 
    hasRole, 
    hasPermission 
  } = useAuth()

  if (isLoading) return <div>Loading...</div>
  if (!isAuthenticated) return <div>Please log in</div>

  return (
    <div>
      <h1>Welcome, {user?.username}!</h1>
      {hasRole('admin') && <AdminButton />}
      {hasPermission('alerts', 'write') && <CreateAlertButton />}
    </div>
  )
}
```

#### useUser()

Simplified hook for accessing user information:

```tsx
import { useUser } from './auth'

function UserProfile() {
  const { user, isAuthenticated, isLoading } = useUser()
  
  if (!isAuthenticated) return null
  
  return (
    <div>
      <h2>{user?.username}</h2>
      <p>Tenant: {user?.tenantId}</p>
      <p>Roles: {user?.roles.map(r => r.name).join(', ')}</p>
    </div>
  )
}
```

#### useRole() and usePermission()

Hooks for checking specific roles or permissions:

```tsx
import { useRole, usePermission } from './auth'

function AdminSection() {
  const { hasRole } = useRole('admin')
  
  if (!hasRole) return null
  
  return <AdminControls />
}

function AlertActions() {
  const { hasPermission } = usePermission('alerts', 'write')
  
  return (
    <div>
      <button>View Alerts</button>
      {hasPermission && <button>Create Alert</button>}
    </div>
  )
}
```

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=observastack
VITE_KEYCLOAK_CLIENT_ID=observastack-frontend
```

### Keycloak Configuration

The Keycloak client should be configured with:

- **Client ID**: `observastack-frontend`
- **Client Protocol**: `openid-connect`
- **Access Type**: `public`
- **Valid Redirect URIs**: `http://localhost:3000/*`
- **Web Origins**: `http://localhost:3000`

## User Roles and Permissions

### Built-in Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | System administrator | All permissions (`*:*`) |
| `tenant-admin` | Tenant administrator | Tenant management, user management |
| `operator` | Operations user | Search, alerts, insights, dashboards |
| `user` | Regular user | Search, alerts (read), insights (read) |
| `viewer` | Read-only user | Search (read), dashboards (read) |
| `search-user` | Search-only user | Search (read) |
| `alert-manager` | Alert management | Alerts (read, write) |
| `insights-viewer` | Insights viewer | Insights (read) |

### Permission System

Permissions follow the format `resource:action`:

- **Resources**: `search`, `alerts`, `insights`, `dashboards`, `tenant`, `users`
- **Actions**: `read`, `write`, `delete`
- **Wildcards**: `*` for all resources or all actions

## Token Management

### Automatic Refresh

Tokens are automatically refreshed when:
- They expire within 60 seconds
- An API request returns a 401 status
- The user performs an action requiring authentication

### Storage

Tokens are stored in `localStorage` with:
- Automatic expiration checking
- Secure storage practices
- Cleanup on logout

### Security Features

- **Silent SSO checks** for seamless authentication
- **Token validation** on every request
- **Automatic logout** on token expiration
- **CSRF protection** through proper token handling

## Error Handling

### Authentication Errors

The system handles various authentication scenarios:

```tsx
function handleAuthError(error: string) {
  console.error('Authentication error:', error)
  // Show user-friendly error message
  // Optionally redirect to login
}

<AuthProvider config={config} onAuthError={handleAuthError}>
  <App />
</AuthProvider>
```

### Common Error Scenarios

1. **Network errors** - Automatic retry with exponential backoff
2. **Token expiration** - Automatic refresh or redirect to login
3. **Permission denied** - Show access denied page with clear messaging
4. **Keycloak unavailable** - Graceful degradation with error messaging

## Testing

### Unit Tests

Test authentication utilities:

```bash
npm run test auth/
```

### Integration Tests

Test authentication flows:

```bash
npm run test:e2e
```

### Mock Authentication

For development and testing:

```tsx
// Mock auth provider for testing
import { MockAuthProvider } from './auth/testing'

<MockAuthProvider user={mockUser}>
  <ComponentUnderTest />
</MockAuthProvider>
```

## Troubleshooting

### Common Issues

1. **"Keycloak not initialized"**
   - Check Keycloak server is running
   - Verify configuration values
   - Check network connectivity

2. **"Access denied" for valid users**
   - Verify user roles in Keycloak
   - Check role mapping configuration
   - Ensure client roles are properly assigned

3. **Token refresh failures**
   - Check token expiration settings
   - Verify refresh token configuration
   - Check for clock skew issues

4. **Silent SSO not working**
   - Ensure `silent-check-sso.html` is accessible
   - Check iframe configuration
   - Verify same-origin policy compliance

### Debug Mode

Enable debug logging:

```env
VITE_DEV_MODE=true
```

This will log authentication events to the browser console.

## Best Practices

### Security

1. **Never store sensitive data** in localStorage beyond tokens
2. **Always validate permissions** on both frontend and backend
3. **Use HTTPS** in production environments
4. **Implement proper CORS** policies
5. **Regular token rotation** and security updates

### Performance

1. **Lazy load** protected components
2. **Cache user permissions** appropriately
3. **Minimize token refresh** frequency
4. **Use React.memo** for auth-dependent components

### User Experience

1. **Show loading states** during authentication
2. **Provide clear error messages** for auth failures
3. **Preserve user's intended destination** after login
4. **Implement graceful degradation** for auth failures

## Migration Guide

### From Basic Auth

If migrating from a basic authentication system:

1. Replace authentication context with `AuthProvider`
2. Update protected routes to use new components
3. Replace role checks with new permission system
4. Update API client to use token authentication
5. Test all authentication flows thoroughly

### Keycloak Upgrade

When upgrading Keycloak versions:

1. Check compatibility with `keycloak-js` version
2. Test all authentication flows
3. Verify token format compatibility
4. Update configuration if needed
5. Test in staging environment first