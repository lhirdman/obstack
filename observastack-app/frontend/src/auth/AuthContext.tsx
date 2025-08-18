/**
 * Authentication context using Keycloak
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type Keycloak from 'keycloak-js'
import type { AuthContextValue, AuthState, AuthProviderProps, KeycloakConfig, TokenInfo } from './types'
import type { User } from '../types'
import { createKeycloakInstance, keycloakInitOptions, tokenRefreshConfig } from './keycloak-config'
import { TokenStorage } from './token-storage'
import { mapKeycloakUserToUser, hasRole, hasPermission } from './user-mapper'

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children, config, onAuthError }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    token: null,
    refreshToken: null,
    error: null
  })

  const [keycloak, setKeycloak] = useState<Keycloak | null>(null)
  const tokenStorage = TokenStorage.getInstance()

  /**
   * Initialize Keycloak and set up authentication
   */
  const initializeAuth = useCallback(async () => {
    try {
      const kc = createKeycloakInstance(config)
      setKeycloak(kc)

      // Initialize Keycloak
      const authenticated = await kc.init(keycloakInitOptions)

      if (authenticated) {
        await handleAuthSuccess(kc)
      } else {
        // Check for stored tokens
        const storedTokens = tokenStorage.getTokens()
        if (storedTokens && tokenStorage.hasValidTokens()) {
          // Try to use stored tokens
          kc.token = storedTokens.accessToken
          kc.refreshToken = storedTokens.refreshToken
          
          try {
            await kc.updateToken(tokenRefreshConfig.minValidity)
            await handleAuthSuccess(kc)
          } catch (error) {
            console.warn('Failed to refresh stored token:', error)
            tokenStorage.clearTokens()
            setAuthState(prev => ({ ...prev, isLoading: false }))
          }
        } else {
          setAuthState(prev => ({ ...prev, isLoading: false }))
        }
      }

      // Set up token refresh callback
      tokenStorage.onTokenRefreshNeeded(async (tokens) => {
        try {
          await kc.updateToken(tokenRefreshConfig.minValidity)
          if (kc.token && kc.refreshToken) {
            const newTokens: TokenInfo = {
              accessToken: kc.token,
              refreshToken: kc.refreshToken,
              ...(kc.idToken && { idToken: kc.idToken }),
              expiresIn: kc.tokenParsed?.exp ? kc.tokenParsed.exp - Math.floor(Date.now() / 1000) : 0,
              refreshExpiresIn: kc.refreshTokenParsed?.exp ? kc.refreshTokenParsed.exp - Math.floor(Date.now() / 1000) : 0,
              tokenType: 'Bearer'
            }
            tokenStorage.setTokens(newTokens)
          }
        } catch (error) {
          console.error('Token refresh failed:', error)
          await handleLogout()
        }
      })

      // Set up token expiration callback
      tokenStorage.onTokenExpiration(() => {
        handleLogout()
      })

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Authentication initialization failed'
      console.error('Keycloak initialization failed:', error)
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }))
      onAuthError?.(errorMessage)
    }
  }, [config, onAuthError])

  /**
   * Handle successful authentication
   */
  const handleAuthSuccess = useCallback(async (kc: Keycloak) => {
    try {
      if (!kc.token || !kc.tokenParsed) {
        throw new Error('No valid token received')
      }

      // Load user profile
      const profile = await kc.loadUserProfile()
      const user = mapKeycloakUserToUser({
        ...profile,
        ...kc.tokenParsed,
        sub: kc.tokenParsed?.sub || profile.id || '',
        tenant_id: kc.tokenParsed?.tenant_id,
        tenant_name: kc.tokenParsed?.tenant_name
      })

      // Store tokens
      const tokens: TokenInfo = {
        accessToken: kc.token,
        refreshToken: kc.refreshToken || '',
        ...(kc.idToken && { idToken: kc.idToken }),
        expiresIn: kc.tokenParsed?.exp ? kc.tokenParsed.exp - Math.floor(Date.now() / 1000) : 3600,
        refreshExpiresIn: kc.refreshTokenParsed?.exp ? kc.refreshTokenParsed.exp - Math.floor(Date.now() / 1000) : 0,
        tokenType: 'Bearer'
      }
      tokenStorage.setTokens(tokens)

      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        user,
        token: kc.token,
        refreshToken: kc.refreshToken || null,
        error: null
      })

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load user profile'
      console.error('Auth success handling failed:', error)
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }))
      onAuthError?.(errorMessage)
    }
  }, [onAuthError])

  /**
   * Handle logout
   */
  const handleLogout = useCallback(async () => {
    try {
      tokenStorage.clearTokens()
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        token: null,
        refreshToken: null,
        error: null
      })
      
      if (keycloak) {
        await keycloak.logout({
          redirectUri: window.location.origin
        })
      }
    } catch (error) {
      console.error('Logout failed:', error)
      // Force logout even if Keycloak logout fails
      window.location.href = '/'
    }
  }, [keycloak])

  /**
   * Initiate login
   */
  const login = useCallback(async () => {
    if (!keycloak) {
      throw new Error('Keycloak not initialized')
    }

    try {
      await keycloak.login({
        redirectUri: window.location.origin
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed'
      console.error('Login failed:', error)
      setAuthState(prev => ({ ...prev, error: errorMessage }))
      onAuthError?.(errorMessage)
    }
  }, [keycloak, onAuthError])

  /**
   * Refresh authentication
   */
  const refreshAuth = useCallback(async () => {
    if (!keycloak) {
      throw new Error('Keycloak not initialized')
    }

    try {
      const refreshed = await keycloak.updateToken(tokenRefreshConfig.minValidity)
      if (refreshed && keycloak.token) {
        const tokens: TokenInfo = {
          accessToken: keycloak.token,
          refreshToken: keycloak.refreshToken || '',
          ...(keycloak.idToken && { idToken: keycloak.idToken }),
          expiresIn: keycloak.tokenParsed?.exp ? keycloak.tokenParsed.exp - Math.floor(Date.now() / 1000) : 0,
          refreshExpiresIn: keycloak.refreshTokenParsed?.exp ? keycloak.refreshTokenParsed.exp - Math.floor(Date.now() / 1000) : 0,
          tokenType: 'Bearer'
        }
        tokenStorage.setTokens(tokens)
        
        setAuthState(prev => ({
          ...prev,
          token: keycloak.token || null,
          refreshToken: keycloak.refreshToken || null
        }))
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      await handleLogout()
    }
  }, [keycloak, handleLogout])

  /**
   * Check if user has specific role
   */
  const userHasRole = useCallback((role: string): boolean => {
    return authState.user ? hasRole(authState.user, role) : false
  }, [authState.user])

  /**
   * Check if user has specific permission
   */
  const userHasPermission = useCallback((resource: string, action: string): boolean => {
    return authState.user ? hasPermission(authState.user, resource, action) : false
  }, [authState.user])

  // Initialize authentication on mount
  useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  // Set up automatic token refresh
  useEffect(() => {
    if (!keycloak || !authState.isAuthenticated) return

    const interval = setInterval(async () => {
      try {
        await keycloak.updateToken(tokenRefreshConfig.minValidity)
      } catch (error) {
        console.error('Automatic token refresh failed:', error)
        await handleLogout()
      }
    }, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [keycloak, authState.isAuthenticated, handleLogout])

  const contextValue: AuthContextValue = {
    ...authState,
    login,
    logout: handleLogout,
    refreshAuth,
    hasRole: userHasRole,
    hasPermission: userHasPermission,
    keycloak
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to use authentication context
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/**
 * Hook to get current user
 */
export function useUser() {
  const { user, isAuthenticated, isLoading } = useAuth()
  return { user, isAuthenticated, isLoading }
}

/**
 * Hook to check roles
 */
export function useRole(role: string) {
  const { hasRole, isAuthenticated, isLoading } = useAuth()
  return {
    hasRole: isAuthenticated ? hasRole(role) : false,
    isAuthenticated,
    isLoading
  }
}

/**
 * Hook to check permissions
 */
export function usePermission(resource: string, action: string) {
  const { hasPermission, isAuthenticated, isLoading } = useAuth()
  return {
    hasPermission: isAuthenticated ? hasPermission(resource, action) : false,
    isAuthenticated,
    isLoading
  }
}