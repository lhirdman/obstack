/**
 * Tests for user mapping utilities
 */

import { describe, it, expect } from 'vitest'
import { mapKeycloakUserToUser, hasRole, hasPermission, isAdmin, isTenantAdmin } from '../user-mapper'
import type { UserProfile } from '../types'
import type { User } from '../../types'

describe('user-mapper', () => {
  const mockKeycloakProfile: UserProfile = {
    sub: 'user-123',
    email: 'test@example.com',
    preferred_username: 'testuser',
    name: 'Test User',
    tenant_id: 'tenant-1',
    realm_access: {
      roles: ['user', 'search-user']
    },
    resource_access: {
      'observastack-frontend': {
        roles: ['alert-manager']
      }
    }
  }

  describe('mapKeycloakUserToUser', () => {
    it('should map Keycloak profile to User model', () => {
      const user = mapKeycloakUserToUser(mockKeycloakProfile)

      expect(user).toEqual({
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        tenantId: 'tenant-1',
        roles: expect.arrayContaining([
          expect.objectContaining({ name: 'user' }),
          expect.objectContaining({ name: 'search-user' }),
          expect.objectContaining({ name: 'alert-manager' })
        ]),
        preferences: expect.objectContaining({
          theme: 'system',
          timezone: expect.any(String),
          defaultTimeRange: {
            from: 'now-1h',
            to: 'now'
          }
        })
      })
    })

    it('should handle missing tenant_id with default', () => {
      const profileWithoutTenant = { ...mockKeycloakProfile }
      delete profileWithoutTenant.tenant_id

      const user = mapKeycloakUserToUser(profileWithoutTenant)
      expect(user.tenantId).toBe('default')
    })

    it('should filter out invalid roles', () => {
      const profileWithInvalidRoles: UserProfile = {
        ...mockKeycloakProfile,
        realm_access: {
          roles: ['user', 'invalid-role', 'another-invalid']
        },
        resource_access: {} // Remove resource access to test only realm roles
      }

      const user = mapKeycloakUserToUser(profileWithInvalidRoles)
      expect(user.roles).toHaveLength(1)
      expect(user.roles[0]?.name).toBe('user')
    })
  })

  describe('hasRole', () => {
    const mockUser: User = {
      id: 'user-123',
      username: 'testuser',
      email: 'test@example.com',
      tenantId: 'tenant-1',
      roles: [
        { id: 'user', name: 'user', permissions: [] },
        { id: 'admin', name: 'admin', permissions: [{ resource: '*', actions: ['*'] }] }
      ],
      preferences: {
        theme: 'system',
        timezone: 'UTC',
        defaultTimeRange: { from: 'now-1h', to: 'now' },
        dashboardLayout: {}
      }
    }

    it('should return true for existing role', () => {
      expect(hasRole(mockUser, 'user')).toBe(true)
      expect(hasRole(mockUser, 'admin')).toBe(true)
    })

    it('should return false for non-existing role', () => {
      expect(hasRole(mockUser, 'operator')).toBe(false)
    })
  })

  describe('hasPermission', () => {
    const mockUser: User = {
      id: 'user-123',
      username: 'testuser',
      email: 'test@example.com',
      tenantId: 'tenant-1',
      roles: [
        {
          id: 'search-user',
          name: 'search-user',
          permissions: [{ resource: 'search', actions: ['read'] }]
        },
        {
          id: 'admin',
          name: 'admin',
          permissions: [{ resource: '*', actions: ['*'] }]
        }
      ],
      preferences: {
        theme: 'system',
        timezone: 'UTC',
        defaultTimeRange: { from: 'now-1h', to: 'now' },
        dashboardLayout: {}
      }
    }

    it('should return true for specific permission', () => {
      expect(hasPermission(mockUser, 'search', 'read')).toBe(true)
    })

    it('should return true for wildcard resource permission', () => {
      expect(hasPermission(mockUser, 'alerts', 'write')).toBe(true)
    })

    it('should return false for missing permission', () => {
      const userWithoutAdmin = {
        ...mockUser,
        roles: mockUser.roles[0] ? [mockUser.roles[0]] : [] // Only search-user role
      }
      expect(hasPermission(userWithoutAdmin, 'alerts', 'write')).toBe(false)
    })
  })

  describe('isAdmin', () => {
    it('should return true for admin role', () => {
      const adminUser: User = {
        id: 'admin-123',
        username: 'admin',
        email: 'admin@example.com',
        tenantId: 'tenant-1',
        roles: [{ id: 'admin', name: 'admin', permissions: [] }],
        preferences: {
          theme: 'system',
          timezone: 'UTC',
          defaultTimeRange: { from: 'now-1h', to: 'now' },
          dashboardLayout: {}
        }
      }
      expect(isAdmin(adminUser)).toBe(true)
    })

    it('should return true for wildcard permissions', () => {
      const wildcardUser: User = {
        id: 'wildcard-123',
        username: 'wildcard',
        email: 'wildcard@example.com',
        tenantId: 'tenant-1',
        roles: [{
          id: 'custom-admin',
          name: 'custom-admin',
          permissions: [{ resource: '*', actions: ['*'] }]
        }],
        preferences: {
          theme: 'system',
          timezone: 'UTC',
          defaultTimeRange: { from: 'now-1h', to: 'now' },
          dashboardLayout: {}
        }
      }
      expect(isAdmin(wildcardUser)).toBe(true)
    })

    it('should return false for regular user', () => {
      const regularUser: User = {
        id: 'user-123',
        username: 'user',
        email: 'user@example.com',
        tenantId: 'tenant-1',
        roles: [{ id: 'user', name: 'user', permissions: [{ resource: 'search', actions: ['read'] }] }],
        preferences: {
          theme: 'system',
          timezone: 'UTC',
          defaultTimeRange: { from: 'now-1h', to: 'now' },
          dashboardLayout: {}
        }
      }
      expect(isAdmin(regularUser)).toBe(false)
    })
  })

  describe('isTenantAdmin', () => {
    it('should return true for tenant-admin role', () => {
      const tenantAdminUser: User = {
        id: 'tenant-admin-123',
        username: 'tenant-admin',
        email: 'tenant-admin@example.com',
        tenantId: 'tenant-1',
        roles: [{ id: 'tenant-admin', name: 'tenant-admin', permissions: [] }],
        preferences: {
          theme: 'system',
          timezone: 'UTC',
          defaultTimeRange: { from: 'now-1h', to: 'now' },
          dashboardLayout: {}
        }
      }
      expect(isTenantAdmin(tenantAdminUser)).toBe(true)
    })

    it('should return true for admin role', () => {
      const adminUser: User = {
        id: 'admin-123',
        username: 'admin',
        email: 'admin@example.com',
        tenantId: 'tenant-1',
        roles: [{ id: 'admin', name: 'admin', permissions: [] }],
        preferences: {
          theme: 'system',
          timezone: 'UTC',
          defaultTimeRange: { from: 'now-1h', to: 'now' },
          dashboardLayout: {}
        }
      }
      expect(isTenantAdmin(adminUser)).toBe(true)
    })
  })
})