/**
 * Keycloak configuration and initialization
 */

import Keycloak from 'keycloak-js'
import type { KeycloakConfig } from './types'

// Default Keycloak configuration for development
export const defaultKeycloakConfig: KeycloakConfig = {
  url: process.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: process.env.VITE_KEYCLOAK_REALM || 'observastack',
  clientId: process.env.VITE_KEYCLOAK_CLIENT_ID || 'observastack-frontend'
}

/**
 * Initialize Keycloak instance with configuration
 */
export function createKeycloakInstance(config: KeycloakConfig): Keycloak {
  return new Keycloak({
    url: config.url,
    realm: config.realm,
    clientId: config.clientId
  })
}

/**
 * Keycloak initialization options
 */
export const keycloakInitOptions = {
  onLoad: 'check-sso' as const,
  silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
  checkLoginIframe: true,
  checkLoginIframeInterval: 30, // Check every 30 seconds
  enableLogging: process.env.NODE_ENV === 'development'
}

/**
 * Token refresh configuration
 */
export const tokenRefreshConfig = {
  minValidity: 30, // Refresh token if it expires in less than 30 seconds
  timeSkew: 0 // No time skew adjustment
}