import { describe, it, expect, vi, beforeEach } from 'vitest';
import { keycloakService, KeycloakService } from './keycloak';
import { configService } from '../lib/config';

// Mock Keycloak
const mockKeycloak = {
  init: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  loadUserProfile: vi.fn(),
  updateToken: vi.fn(),
  authenticated: false,
  token: undefined as string | undefined,
  tokenParsed: undefined as any,
  profile: undefined as any,
};

vi.mock('keycloak-js', () => {
  return {
    default: vi.fn(() => mockKeycloak),
  };
});

vi.mock('../lib/config', () => ({
  configService: {
    getKeycloakConfig: vi.fn(),
  },
}));

describe('KeycloakService', () => {
  let service: KeycloakService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new KeycloakService();
    
    // Mock config
    vi.mocked(configService.getKeycloakConfig).mockReturnValue({
      url: 'http://localhost:8080',
      realm: 'test-realm',
      clientId: 'test-client',
    });
  });

  describe('init', () => {
    it('should initialize Keycloak successfully', async () => {
      mockKeycloak.init.mockResolvedValue(true);
      mockKeycloak.authenticated = true;

      const result = await service.init();

      expect(result).toBe(true);
      expect(mockKeycloak.init).toHaveBeenCalledWith({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        checkLoginIframe: false,
      });
    });

    it('should handle initialization failure', async () => {
      mockKeycloak.init.mockRejectedValue(new Error('Init failed'));

      await expect(service.init()).rejects.toThrow('Init failed');
    });

    it('should throw error if no Keycloak config', async () => {
      vi.mocked(configService.getKeycloakConfig).mockReturnValue(undefined);

      await expect(service.init()).rejects.toThrow('Keycloak configuration not found');
    });
  });

  describe('login', () => {
    beforeEach(async () => {
      mockKeycloak.init.mockResolvedValue(true);
      await service.init();
    });

    it('should redirect to Keycloak login', async () => {
      mockKeycloak.login.mockResolvedValue(undefined);

      await service.login();

      expect(mockKeycloak.login).toHaveBeenCalledWith({
        redirectUri: window.location.origin + '/auth/callback',
      });
    });

    it('should handle login failure', async () => {
      mockKeycloak.login.mockRejectedValue(new Error('Login failed'));

      await expect(service.login()).rejects.toThrow('Login failed');
    });
  });

  describe('logout', () => {
    beforeEach(async () => {
      mockKeycloak.init.mockResolvedValue(true);
      await service.init();
    });

    it('should logout from Keycloak', async () => {
      mockKeycloak.logout.mockResolvedValue(undefined);

      await service.logout();

      expect(mockKeycloak.logout).toHaveBeenCalledWith({
        redirectUri: window.location.origin,
      });
    });
  });

  describe('getCurrentUser', () => {
    beforeEach(async () => {
      mockKeycloak.init.mockResolvedValue(true);
      mockKeycloak.authenticated = true;
      await service.init();
    });

    it('should return user information', async () => {
      const mockProfile = {
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
      };

      const mockTokenParsed = {
        sub: 'user-123',
        preferred_username: 'testuser',
        email: 'test@example.com',
        realm_access: {
          roles: ['user', 'admin'],
        },
      };

      mockKeycloak.loadUserProfile.mockResolvedValue(undefined);
      (mockKeycloak as any).profile = mockProfile;
      (mockKeycloak as any).tokenParsed = mockTokenParsed;

      const user = await service.getCurrentUser();

      expect(user).toEqual({
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        roles: ['user', 'admin'],
      });
    });

    it('should throw error if not authenticated', async () => {
      mockKeycloak.authenticated = false;

      await expect(service.getCurrentUser()).rejects.toThrow('User not authenticated');
    });
  });

  describe('isAuthenticated', () => {
    it('should return authentication status', () => {
      mockKeycloak.authenticated = true;
      expect(service.isAuthenticated()).toBe(true);

      mockKeycloak.authenticated = false;
      expect(service.isAuthenticated()).toBe(false);
    });
  });

  describe('getToken', () => {
    it('should return current token', () => {
      (mockKeycloak as any).token = 'test-token';
      expect(service.getToken()).toBe('test-token');
    });
  });

  describe('updateToken', () => {
    beforeEach(async () => {
      mockKeycloak.init.mockResolvedValue(true);
      await service.init();
    });

    it('should update token successfully', async () => {
      mockKeycloak.updateToken.mockResolvedValue(true);

      const result = await service.updateToken();

      expect(result).toBe(true);
      expect(mockKeycloak.updateToken).toHaveBeenCalledWith(30);
    });

    it('should handle token update failure', async () => {
      mockKeycloak.updateToken.mockRejectedValue(new Error('Update failed'));

      const result = await service.updateToken();

      expect(result).toBe(false);
    });
  });
});