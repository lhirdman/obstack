/**
 * Authentication service using the API client.
 * Handles login, logout, and user authentication status.
 */

import { apiClient } from '../lib/api-client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  tenant_id: number;
  roles: string[];
  created_at: string;
}

export interface LogoutResponse {
  message: string;
}

export class AuthService {
  /**
   * Login user with email and password.
   * The JWT token will be automatically stored in an HttpOnly cookie by the backend.
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/auth/login', credentials);
  }

  /**
   * Logout user by clearing the HttpOnly cookie.
   */
  async logout(): Promise<LogoutResponse> {
    return apiClient.post<LogoutResponse>('/auth/logout');
  }

  /**
   * Get current authenticated user information.
   * This will automatically include the HttpOnly cookie for authentication.
   */
  async getCurrentUser(): Promise<UserResponse> {
    return apiClient.get<UserResponse>('/auth/me');
  }

  /**
   * Check if user is currently authenticated.
   * Returns true if the user has a valid session, false otherwise.
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Export a default instance
export const authService = new AuthService();

// Export the class for custom instances
export default AuthService;