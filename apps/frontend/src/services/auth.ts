/**
 * Authentication service that supports both local and Keycloak authentication.
 * Handles login, logout, and user authentication status.
 */

import { apiClient } from '../lib/api-client';
import { configService } from '../lib/config';
import { keycloakService, KeycloakUserInfo } from './keycloak';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string | number;
  username: string;
  email: string;
  tenant_id?: number;
  roles: string[];
  created_at?: string;
  firstName?: string | undefined;
  lastName?: string | undefined;
}

export interface LogoutResponse {
  message: string;
}

export class AuthService {
  private authMethod: 'local' | 'keycloak';

  constructor() {
    this.authMethod = configService.getAuthMethod();
  }

  /**
   * Initialize authentication service
   */
  async init(): Promise<boolean> {
    if (this.authMethod === 'keycloak') {
      try {
        return await keycloakService.init();
      } catch (error) {
        console.error('Failed to initialize Keycloak:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Login user with email and password (local auth) or redirect to Keycloak.
   */
  async login(credentials?: LoginRequest): Promise<LoginResponse | void> {
    if (this.authMethod === 'keycloak') {
      // For Keycloak, redirect to login page
      await keycloakService.login();
      return; // No return value as this redirects
    } else {
      // Local authentication
      if (!credentials) {
        throw new Error('Credentials required for local authentication');
      }
      return apiClient.post<LoginResponse>('/auth/login', credentials);
    }
  }

  /**
   * Logout user by clearing the HttpOnly cookie or logging out from Keycloak.
   */
  async logout(): Promise<LogoutResponse | void> {
    if (this.authMethod === 'keycloak') {
      await keycloakService.logout();
      return; // No return value as this redirects
    } else {
      return apiClient.post<LogoutResponse>('/auth/logout');
    }
  }

  /**
   * Get current authenticated user information.
   */
  async getCurrentUser(): Promise<UserResponse> {
    if (this.authMethod === 'keycloak') {
      const keycloakUser = await keycloakService.getCurrentUser();
      return this.mapKeycloakUserToUserResponse(keycloakUser);
    } else {
      return apiClient.get<UserResponse>('/auth/me');
    }
  }

  /**
   * Check if user is currently authenticated.
   */
  async isAuthenticated(): Promise<boolean> {
    if (this.authMethod === 'keycloak') {
      return keycloakService.isAuthenticated();
    } else {
      try {
        await this.getCurrentUser();
        return true;
      } catch (error) {
        return false;
      }
    }
  }

  /**
   * Get the current authentication method
   */
  getAuthMethod(): 'local' | 'keycloak' {
    return this.authMethod;
  }

  /**
   * Get JWT token (for Keycloak auth)
   */
  getToken(): string | undefined {
    if (this.authMethod === 'keycloak') {
      return keycloakService.getToken();
    }
    return undefined;
  }

  /**
   * Update token if needed (for Keycloak auth)
   */
  async updateToken(): Promise<boolean> {
    if (this.authMethod === 'keycloak') {
      return keycloakService.updateToken();
    }
    return false;
  }

  /**
   * Map Keycloak user info to UserResponse format
   */
  private mapKeycloakUserToUserResponse(keycloakUser: KeycloakUserInfo): UserResponse {
    return {
      id: keycloakUser.id,
      username: keycloakUser.username,
      email: keycloakUser.email,
      firstName: keycloakUser.firstName,
      lastName: keycloakUser.lastName,
      roles: keycloakUser.roles,
    };
  }
}

// Export a default instance
export const authService = new AuthService();

// Export the class for custom instances
export default AuthService;