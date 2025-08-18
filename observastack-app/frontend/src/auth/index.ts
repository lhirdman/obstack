/**
 * Authentication module exports
 */

// Context and hooks
export { AuthProvider, useAuth, useUser, useRole, usePermission } from './AuthContext'

// Protected route components
export {
  ProtectedRoute,
  AdminRoute,
  OperatorRoute,
  UserRoute,
  PermissionRoute,
  ConditionalRender
} from './ProtectedRoute'

// Login page
export { LoginPage } from './LoginPage'

// Configuration
export { defaultKeycloakConfig, createKeycloakInstance } from './keycloak-config'

// Token storage
export { TokenStorage } from './token-storage'

// User mapping utilities
export {
  mapKeycloakUserToUser,
  hasRole,
  hasPermission,
  isAdmin,
  isTenantAdmin,
  getUserDisplayName
} from './user-mapper'

// Types
export type {
  AuthState,
  AuthContextValue,
  KeycloakConfig,
  AuthProviderProps,
  ProtectedRouteProps,
  TokenInfo,
  UserProfile
} from './types'