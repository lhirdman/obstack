/**
 * User profile mapping utilities for Keycloak integration
 */

import type { User, Role, Permission } from '../types'
import type { UserProfile } from './types'

/**
 * Map Keycloak user profile to application User model
 */
export function mapKeycloakUserToUser(profile: UserProfile): User {
  // Extract tenant information from token claims
  const tenantId = profile.tenant_id || 'default'
  
  // Map roles from Keycloak realm and resource access
  const roles = mapKeycloakRoles(profile)
  
  // Create user preferences with defaults
  const preferences = {
    theme: 'system' as const,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    defaultTimeRange: {
      from: 'now-1h',
      to: 'now'
    },
    dashboardLayout: {}
  }

  return {
    id: profile.sub,
    username: profile.preferred_username || profile.email || profile.sub,
    email: profile.email || '',
    tenantId,
    roles,
    preferences
  }
}

/**
 * Map Keycloak roles to application Role model
 */
function mapKeycloakRoles(profile: UserProfile): Role[] {
  const roles: Role[] = []
  
  // Extract realm roles
  const realmRoles = profile.realm_access?.roles || []
  realmRoles.forEach(roleName => {
    if (isObservaStackRole(roleName)) {
      roles.push(createRoleFromName(roleName))
    }
  })
  
  // Extract client-specific roles
  const resourceAccess = profile.resource_access || {}
  Object.entries(resourceAccess).forEach(([clientId, access]) => {
    if (clientId.includes('observastack')) {
      access.roles.forEach(roleName => {
        if (isObservaStackRole(roleName) && !roles.some(r => r.name === roleName)) {
          roles.push(createRoleFromName(roleName))
        }
      })
    }
  })
  
  return roles
}

/**
 * Check if role name is a valid ObservaStack role
 */
function isObservaStackRole(roleName: string): boolean {
  const validRoles = [
    'admin',
    'user',
    'viewer',
    'operator',
    'tenant-admin',
    'search-user',
    'alert-manager',
    'insights-viewer'
  ]
  return validRoles.includes(roleName)
}

/**
 * Create Role object from role name with appropriate permissions
 */
function createRoleFromName(roleName: string): Role {
  const rolePermissions = getRolePermissions(roleName)
  
  return {
    id: roleName,
    name: roleName,
    permissions: rolePermissions
  }
}

/**
 * Get permissions for a specific role
 */
function getRolePermissions(roleName: string): Permission[] {
  const permissionMap: Record<string, Permission[]> = {
    admin: [
      { resource: '*', actions: ['*'] }
    ],
    'tenant-admin': [
      { resource: 'tenant', actions: ['read', 'write', 'delete'] },
      { resource: 'users', actions: ['read', 'write', 'delete'] },
      { resource: 'search', actions: ['read'] },
      { resource: 'alerts', actions: ['read', 'write'] },
      { resource: 'insights', actions: ['read'] },
      { resource: 'dashboards', actions: ['read', 'write', 'delete'] }
    ],
    operator: [
      { resource: 'search', actions: ['read'] },
      { resource: 'alerts', actions: ['read', 'write'] },
      { resource: 'insights', actions: ['read'] },
      { resource: 'dashboards', actions: ['read', 'write'] }
    ],
    user: [
      { resource: 'search', actions: ['read'] },
      { resource: 'alerts', actions: ['read'] },
      { resource: 'insights', actions: ['read'] },
      { resource: 'dashboards', actions: ['read'] }
    ],
    viewer: [
      { resource: 'search', actions: ['read'] },
      { resource: 'dashboards', actions: ['read'] }
    ],
    'search-user': [
      { resource: 'search', actions: ['read'] }
    ],
    'alert-manager': [
      { resource: 'alerts', actions: ['read', 'write'] }
    ],
    'insights-viewer': [
      { resource: 'insights', actions: ['read'] }
    ]
  }
  
  return permissionMap[roleName] || []
}

/**
 * Check if user has specific role
 */
export function hasRole(user: User, roleName: string): boolean {
  return user.roles.some(role => role.name === roleName)
}

/**
 * Check if user has specific permission
 */
export function hasPermission(user: User, resource: string, action: string): boolean {
  return user.roles.some(role =>
    role.permissions.some(permission =>
      (permission.resource === '*' || permission.resource === resource) &&
      (permission.actions.includes('*') || permission.actions.includes(action))
    )
  )
}

/**
 * Check if user is admin (has admin role or wildcard permissions)
 */
export function isAdmin(user: User): boolean {
  return hasRole(user, 'admin') || 
         user.roles.some(role => 
           role.permissions.some(p => p.resource === '*' && p.actions.includes('*'))
         )
}

/**
 * Check if user is tenant admin
 */
export function isTenantAdmin(user: User): boolean {
  return hasRole(user, 'tenant-admin') || isAdmin(user)
}

/**
 * Get user's display name
 */
export function getUserDisplayName(user: User): string {
  return user.username || user.email || user.id
}