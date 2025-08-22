import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import LoginForm from './LoginForm';
import { configService } from '../../lib/config';
import { authService } from '../../services/auth';

// Mock dependencies
vi.mock('../../lib/config', () => ({
  configService: {
    getAuthMethod: vi.fn(),
  },
}));

vi.mock('../../services/auth', () => ({
  authService: {
    init: vi.fn(),
    login: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('LoginForm - Keycloak Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Keycloak Authentication Mode', () => {
    beforeEach(() => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('keycloak');
      vi.mocked(authService.init).mockResolvedValue(false); // Not already authenticated
    });

    it('should show Keycloak login UI when auth method is keycloak', async () => {
      render(<LoginForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Sign in with your corporate credentials')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sign In with SSO' })).toBeInTheDocument();
      });

      // Should not show local login form elements
      expect(screen.queryByLabelText('Email Address')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Password')).not.toBeInTheDocument();
    });

    it('should show loading state during initialization', () => {
      render(<LoginForm />, { wrapper: createWrapper() });

      expect(screen.getByText('Initializing authentication...')).toBeInTheDocument();
    });

    it('should call authService.login when SSO button is clicked', async () => {
      vi.mocked(authService.login).mockResolvedValue(undefined);

      render(<LoginForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Sign In with SSO' })).toBeInTheDocument();
      });

      const ssoButton = screen.getByRole('button', { name: 'Sign In with SSO' });
      fireEvent.click(ssoButton);

      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith();
      });
    });

    it('should show loading state when login is in progress', async () => {
      vi.mocked(authService.login).mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<LoginForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Sign In with SSO' })).toBeInTheDocument();
      });

      const ssoButton = screen.getByRole('button', { name: 'Sign In with SSO' });
      fireEvent.click(ssoButton);

      await waitFor(() => {
        expect(screen.getByText('Redirecting...')).toBeInTheDocument();
        expect(ssoButton).toBeDisabled();
      });
    });

    it('should handle login errors', async () => {
      const mockError = new Error('Keycloak login failed');
      vi.mocked(authService.login).mockRejectedValue(mockError);

      const onError = vi.fn();
      render(<LoginForm onError={onError} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Sign In with SSO' })).toBeInTheDocument();
      });

      const ssoButton = screen.getByRole('button', { name: 'Sign In with SSO' });
      fireEvent.click(ssoButton);

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Keycloak login failed');
      });
    });

    it('should call onSuccess if already authenticated during init', async () => {
      vi.mocked(authService.init).mockResolvedValue(true); // Already authenticated
      const onSuccess = vi.fn();

      render(<LoginForm onSuccess={onSuccess} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });
    });

    it('should handle initialization errors', async () => {
      vi.mocked(authService.init).mockRejectedValue(new Error('Init failed'));
      const onError = vi.fn();

      render(<LoginForm onError={onError} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Failed to initialize authentication system');
      });
    });
  });

  describe('Local Authentication Mode', () => {
    beforeEach(() => {
      vi.mocked(configService.getAuthMethod).mockReturnValue('local');
    });

    it('should show local login form when auth method is local', async () => {
      render(<LoginForm />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
      });

      // Should not show Keycloak UI
      expect(screen.queryByText('Sign in with your corporate credentials')).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Sign In with SSO' })).not.toBeInTheDocument();
    });

    it('should submit form data for local authentication', async () => {
      const mockResponse = { access_token: 'token', token_type: 'Bearer' };
      vi.mocked(authService.login).mockResolvedValue(mockResponse);

      const onSuccess = vi.fn();
      render(<LoginForm onSuccess={onSuccess} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
      });

      // Fill in the form
      fireEvent.change(screen.getByLabelText('Email Address'), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText('Password'), {
        target: { value: 'password123' },
      });

      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
        expect(onSuccess).toHaveBeenCalled();
      });
    });
  });
});