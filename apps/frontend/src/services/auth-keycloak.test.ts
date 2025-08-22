import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthService } from './auth';
import { keycloakService } from './keycloak';
import { configService } from '../lib/config';
import { apiClient } from '../lib/api-client';

vi.mock('./keycloak', () => ({
  keycloakService: {
    init: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
    getToken: vi.fn(),
    updateToken: vi.fn(),
  },
}));

vi.mock('../lib/config', () => ({
  configService: {
    getAuthMethod: vi.fn(),
  },
}));

vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('AuthService - Keycloak Integration', () => {
  let authService: AuthService;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(configService.getAuthMethod).mockReturnValue('keycloak');
    authService = new AuthService();
  });

  describe('init', () => {
    it('should initialize Keycloak service', async () => {
      vi.mocked(keycloakService.init).mockResolvedValue(true);

      const result = await authService.init();

      expect(result).toBe(true);
      expect(keycloakService.init).toHaveBeenCalled();
    });

    it('should handle Keycloak initialization failure', async () => {
      vi.mocked(keycloakService.init).mockRejectedValue(new Error('Init failed'));

      const result = await authService.init();

      expect(result).toBe(false);
    });

    it('should return false for local auth', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();

      const result = await authService.init();

      expect(result).toBe(false);
    });
  });

  describe('login', () => {
    it('should redirect to Keycloak login', async () => {
      vi.mocked(keycloakService.login).mockResolvedValue(undefined);

      await authService.login();

      expect(keycloakService.login).toHaveBeenCalled();
    });

    it('should use API client for local auth', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();
      
      const credentials = { email: 'test@example.com', password: 'password' };
      const mockResponse = { access_token: 'token', token_type: 'Bearer' };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.login(credentials);

      expect(result).toEqual(mockResponse);
      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', credentials);
    });

    it('should throw error for local auth without credentials', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();

      await expect(authService.login()).rejects.toThrow('Credentials required for local authentication');
    });
  });

  describe('logout', () => {
    it('should logout from Keycloak', async () => {
      vi.mocked(keycloakService.logout).mockResolvedValue(undefined);

      await authService.logout();

      expect(keycloakService.logout).toHaveBeenCalled();
    });

    it('should use API client for local auth', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();
      
      const mockResponse = { message: 'Logged out' };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.logout();

      expect(result).toEqual(mockResponse);
      expect(apiClient.post).toHaveBeenCalledWith('/auth/logout');
    });
  });

  describe('getCurrentUser', () => {
    it('should get user from Keycloak', async () => {
      const mockKeycloakUser = {
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        roles: ['user'],
      };

      vi.mocked(keycloakService.getCurrentUser).mockResolvedValue(mockKeycloakUser);

      const result = await authService.getCurrentUser();

      expect(result).toEqual({
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        roles: ['user'],
      });
    });

    it('should get user from API for local auth', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();
      
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        tenant_id: 1,
        roles: ['user'],
        created_at: '2023-01-01T00:00:00Z',
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockUser);

      const result = await authService.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
    });
  });

  describe('isAuthenticated', () => {
    it('should check Keycloak authentication status', async () => {
      vi.mocked(keycloakService.isAuthenticated).mockReturnValue(true);

      const result = await authService.isAuthenticated();

      expect(result).toBe(true);
      expect(keycloakService.isAuthenticated).toHaveBeenCalled();
    });

    it('should check local authentication by calling getCurrentUser', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();
      
      vi.mocked(apiClient.get).mockResolvedValue({ id: 1, username: 'test' });

      const result = await authService.isAuthenticated();

      expect(result).toBe(true);
    });

    it('should return false for local auth when getCurrentUser fails', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();
      
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Unauthorized'));

      const result = await authService.isAuthenticated();

      expect(result).toBe(false);
    });
  });

  describe('getAuthMethod', () => {
    it('should return keycloak auth method', () => {
      const result = authService.getAuthMethod();
      expect(result).toBe('keycloak');
    });
  });

  describe('getToken', () => {
    it('should return Keycloak token', () => {
      vi.mocked(keycloakService.getToken).mockReturnValue('test-token');

      const result = authService.getToken();

      expect(result).toBe('test-token');
      expect(keycloakService.getToken).toHaveBeenCalled();
    });

    it('should return undefined for local auth', () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();

      const result = authService.getToken();

      expect(result).toBeUndefined();
    });
  });

  describe('updateToken', () => {
    it('should update Keycloak token', async () => {
      vi.mocked(keycloakService.updateToken).mockResolvedValue(true);

      const result = await authService.updateToken();

      expect(result).toBe(true);
      expect(keycloakService.updateToken).toHaveBeenCalled();
    });

    it('should return false for local auth', async () => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
      authService = new AuthService();

      const result = await authService.updateToken();

      expect(result).toBe(false);
    });
  });
});