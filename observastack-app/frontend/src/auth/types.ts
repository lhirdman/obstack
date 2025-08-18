/**
 * Authentication types for Keycloak integration
 */

import type Keycloak from 'keycloak-js'
import type { User, Role } from '../types'

export interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  token: string | null
  refreshToken: string | null
  error: string | null
}

export interface AuthContextValue extends AuthState {
  login: () => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
  hasRole: (role: string) => boolean
  hasPermission: (resource: string, action: string) => boolean
  keycloak: Keycloak | null
}

export interface KeycloakConfig {
  url: string
  realm: string
  clientId: string
}

export interface AuthProviderProps {
  children: React.ReactNode
  config: KeycloakConfig
  onAuthError?: (error: string) => void
}

export interface ProtectedRouteProps {
  children: React.ReactNode
  roles?: string[]
  permissions?: Array<{ resource: string; action: string }>
  fallback?: React.ReactNode
}

export interface TokenInfo {
  accessToken: string
  refreshToken: string
  idToken?: string
  expiresIn: number
  refreshExpiresIn: number
  tokenType: 'Bearer'
}

export interface UserProfile {
  sub: string
  email?: string
  email_verified?: boolean
  name?: string
  preferred_username?: string
  given_name?: string
  family_name?: string
  realm_access?: {
    roles: string[]
  }
  resource_access?: Record<string, {
    roles: string[]
  }>
  tenant_id?: string
  tenant_name?: string
}