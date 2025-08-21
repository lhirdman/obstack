import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AuthService, authService } from './auth';

describe('AuthService', () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let service: AuthService;

  beforeEach(() => {
    mockFetch = vi.fn();
    global.fetch = mockFetch;
    service = new AuthService();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('successfully logs in a user', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => mockResponse,
      });

      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      const result = await service.login(credentials);

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(credentials),
      });

      expect(result).toEqual(mockResponse);
    });

    it('throws error on login failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Invalid credentials' }),
      });

      const credentials = {
        email: 'test@example.com',
        password: 'wrongpassword',
      };

      await expect(service.login(credentials)).rejects.toThrow('Invalid credentials');
    });

    it('throws generic error when error response has no detail', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({}),
      });

      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      await expect(service.login(credentials)).rejects.toThrow('HTTP 500: Internal Server Error');
    });

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      await expect(service.login(credentials)).rejects.toThrow('Network error');
    });
  });

  describe('logout', () => {
    it('successfully logs out a user', async () => {
      const mockResponse = {
        message: 'Successfully logged out',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => mockResponse,
      });

      const result = await service.logout();

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      expect(result).toEqual(mockResponse);
    });

    it('throws error on logout failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Logout failed' }),
      });

      await expect(service.logout()).rejects.toThrow('Logout failed');
    });
  });

  describe('getCurrentUser', () => {
    it('successfully gets current user', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        tenant_id: 1,
        roles: ['user'],
        created_at: '2023-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => mockUser,
      });

      const result = await service.getCurrentUser();

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/me', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      expect(result).toEqual(mockUser);
    });

    it('throws error when user is not authenticated', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Could not validate credentials' }),
      });

      await expect(service.getCurrentUser()).rejects.toThrow('Could not validate credentials');
    });
  });

  describe('isAuthenticated', () => {
    it('returns true when user is authenticated', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        tenant_id: 1,
        roles: ['user'],
        created_at: '2023-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => mockUser,
      });

      const result = await service.isAuthenticated();

      expect(result).toBe(true);
    });

    it('returns false when user is not authenticated', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Could not validate credentials' }),
      });

      const result = await service.isAuthenticated();

      expect(result).toBe(false);
    });

    it('returns false on network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await service.isAuthenticated();

      expect(result).toBe(false);
    });
  });

  describe('API client integration', () => {
    it('includes credentials in all requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ message: 'success' }),
      });

      await service.logout();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('sets correct content-type header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({ message: 'success' }),
      });

      await service.getCurrentUser();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('handles non-JSON responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'text/plain']]),
        text: async () => 'Success',
        json: async () => { throw new Error('Not JSON'); },
      });

      const result = await service.logout();

      expect(result).toBe('Success');
    });
  });

  describe('default instance', () => {
    it('exports a default auth service instance', () => {
      expect(authService).toBeInstanceOf(AuthService);
    });

    it('default instance works correctly', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => mockResponse,
      });

      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      const result = await authService.login(credentials);

      expect(result).toEqual(mockResponse);
    });
  });
});