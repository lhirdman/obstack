/**
 * Keycloak authentication service using keycloak-js library.
 * Handles OIDC authentication flow with Keycloak.
 */

import Keycloak from 'keycloak-js';
import { configService, KeycloakConfig } from '../lib/config';

export interface KeycloakUserInfo {
  id: string;
  username: string;
  email: string;
  firstName?: string | undefined;
  lastName?: string | undefined;
  roles: string[];
}

export class KeycloakService {
  private keycloak: Keycloak | null = null;
  private initialized = false;

  /**
   * Initialize Keycloak instance with configuration
   */
  async init(): Promise<boolean> {
    if (this.initialized) {
      return this.keycloak?.authenticated || false;
    }

    const keycloakConfig = configService.getKeycloakConfig();
    if (!keycloakConfig) {
      throw new Error('Keycloak configuration not found');
    }

    this.keycloak = new Keycloak({
      url: keycloakConfig.url,
      realm: keycloakConfig.realm,
      clientId: keycloakConfig.clientId,
    });

    try {
      const authenticated = await this.keycloak.init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        checkLoginIframe: false, // Disable iframe check for better compatibility
      });

      this.initialized = true;
      return authenticated;
    } catch (error) {
      console.error('Failed to initialize Keycloak:', error);
      throw error;
    }
  }

  /**
   * Redirect to Keycloak login page
   */
  async login(): Promise<void> {
    if (!this.keycloak) {
      throw new Error('Keycloak not initialized');
    }

    try {
      await this.keycloak.login({
        redirectUri: window.location.origin + '/auth/callback',
      });
    } catch (error) {
      console.error('Failed to initiate Keycloak login:', error);
      throw error;
    }
  }

  /**
   * Logout from Keycloak
   */
  async logout(): Promise<void> {
    if (!this.keycloak) {
      throw new Error('Keycloak not initialized');
    }

    try {
      await this.keycloak.logout({
        redirectUri: window.location.origin,
      });
    } catch (error) {
      console.error('Failed to logout from Keycloak:', error);
      throw error;
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<KeycloakUserInfo> {
    if (!this.keycloak || !this.keycloak.authenticated) {
      throw new Error('User not authenticated');
    }

    try {
      await this.keycloak.loadUserProfile();
      const profile = this.keycloak.profile;
      const tokenParsed = this.keycloak.tokenParsed;

      if (!profile || !tokenParsed) {
        throw new Error('Failed to load user profile');
      }

      return {
        id: profile.id || tokenParsed.sub || '',
        username: profile.username || tokenParsed.preferred_username || '',
        email: profile.email || tokenParsed.email || '',
        firstName: profile.firstName,
        lastName: profile.lastName,
        roles: tokenParsed.realm_access?.roles || [],
      };
    } catch (error) {
      console.error('Failed to get current user:', error);
      throw error;
    }
  }

  /**
   * Get the current JWT token
   */
  getToken(): string | undefined {
    return this.keycloak?.token;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.keycloak?.authenticated || false;
  }

  /**
   * Update token if it's about to expire
   */
  async updateToken(): Promise<boolean> {
    if (!this.keycloak) {
      return false;
    }

    try {
      // Refresh token if it expires within 30 seconds
      const refreshed = await this.keycloak.updateToken(30);
      return refreshed;
    } catch (error) {
      console.error('Failed to update token:', error);
      return false;
    }
  }

  /**
   * Get Keycloak instance (for advanced usage)
   */
  getKeycloakInstance(): Keycloak | null {
    return this.keycloak;
  }
}

// Export a default instance
export const keycloakService = new KeycloakService();

// Export the class for custom instances
export default KeycloakService;