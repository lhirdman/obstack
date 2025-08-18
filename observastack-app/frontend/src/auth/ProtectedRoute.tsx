/**
 * Protected route components with role and permission checking
 */

import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { ProtectedRouteProps } from './types'

/**
 * Loading component displayed during authentication check
 */
function AuthLoadingSpinner() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      flexDirection: 'column',
      gap: '16px'
    }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
      <div style={{ color: '#666', fontSize: '14px' }}>
        Authenticating...
      </div>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

/**
 * Access denied component
 */
function AccessDenied({ requiredRoles, requiredPermissions }: {
  requiredRoles?: string[]
  requiredPermissions?: Array<{ resource: string; action: string }>
}) {
  const { user, logout } = useAuth()

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      flexDirection: 'column',
      gap: '24px',
      padding: '24px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '48px' }}>🔒</div>
      <div>
        <h2 style={{ margin: '0 0 8px 0', color: '#e74c3c' }}>Access Denied</h2>
        <p style={{ margin: '0 0 16px 0', color: '#666', maxWidth: '400px' }}>
          You don't have the required permissions to access this page.
        </p>
        {user && (
          <div style={{ fontSize: '14px', color: '#888', marginBottom: '16px' }}>
            Logged in as: <strong>{user.username}</strong> ({user.tenantId})
          </div>
        )}
        {requiredRoles && requiredRoles.length > 0 && (
          <div style={{ fontSize: '14px', color: '#888', marginBottom: '8px' }}>
            Required roles: {requiredRoles.join(', ')}
          </div>
        )}
        {requiredPermissions && requiredPermissions.length > 0 && (
          <div style={{ fontSize: '14px', color: '#888', marginBottom: '16px' }}>
            Required permissions: {requiredPermissions.map(p => `${p.resource}:${p.action}`).join(', ')}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', gap: '12px' }}>
        <button
          onClick={() => window.history.back()}
          style={{
            padding: '8px 16px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            background: 'white',
            cursor: 'pointer'
          }}
        >
          Go Back
        </button>
        <button
          onClick={logout}
          style={{
            padding: '8px 16px',
            border: '1px solid #e74c3c',
            borderRadius: '4px',
            background: '#e74c3c',
            color: 'white',
            cursor: 'pointer'
          }}
        >
          Logout
        </button>
      </div>
    </div>
  )
}

/**
 * Protected route component that requires authentication
 */
export function ProtectedRoute({ 
  children, 
  roles = [], 
  permissions = [], 
  fallback 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, hasRole, hasPermission } = useAuth()
  const location = useLocation()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return <AuthLoadingSpinner />
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check role requirements
  if (roles.length > 0 && !roles.some(role => hasRole(role))) {
    return fallback || <AccessDenied requiredRoles={roles} />
  }

  // Check permission requirements
  if (permissions.length > 0 && !permissions.some(perm => hasPermission(perm.resource, perm.action))) {
    return fallback || <AccessDenied requiredPermissions={permissions} />
  }

  return <>{children}</>
}

/**
 * Admin-only route component
 */
export function AdminRoute({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <ProtectedRoute 
      roles={['admin', 'tenant-admin']} 
      fallback={fallback}
    >
      {children}
    </ProtectedRoute>
  )
}

/**
 * Operator route component (admin or operator roles)
 */
export function OperatorRoute({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <ProtectedRoute 
      roles={['admin', 'tenant-admin', 'operator']} 
      fallback={fallback}
    >
      {children}
    </ProtectedRoute>
  )
}

/**
 * User route component (any authenticated user)
 */
export function UserRoute({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <ProtectedRoute fallback={fallback}>
      {children}
    </ProtectedRoute>
  )
}

/**
 * Permission-based route component
 */
export function PermissionRoute({ 
  children, 
  resource, 
  action, 
  fallback 
}: { 
  children: React.ReactNode
  resource: string
  action: string
  fallback?: React.ReactNode 
}) {
  return (
    <ProtectedRoute 
      permissions={[{ resource, action }]} 
      fallback={fallback}
    >
      {children}
    </ProtectedRoute>
  )
}

/**
 * Conditional component that renders children only if user has required roles/permissions
 */
export function ConditionalRender({
  children,
  roles = [],
  permissions = [],
  fallback = null
}: {
  children: React.ReactNode
  roles?: string[]
  permissions?: Array<{ resource: string; action: string }>
  fallback?: React.ReactNode
}) {
  const { isAuthenticated, hasRole, hasPermission } = useAuth()

  if (!isAuthenticated) {
    return <>{fallback}</>
  }

  // Check role requirements
  if (roles.length > 0 && !roles.some(role => hasRole(role))) {
    return <>{fallback}</>
  }

  // Check permission requirements
  if (permissions.length > 0 && !permissions.some(perm => hasPermission(perm.resource, perm.action))) {
    return <>{fallback}</>
  }

  return <>{children}</>
}