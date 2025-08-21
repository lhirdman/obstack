import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ProtectedRoute from './ProtectedRoute';
import { authService } from '../../services/auth';

vi.mock('../../services/auth', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    authService: {
      ...actual.authService,
      getCurrentUser: vi.fn(),
    },
  };
});

const mockedGetCurrentUser = vi.mocked(authService.getCurrentUser);

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('ProtectedRoute', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders children when user is authenticated', async () => {
    mockedGetCurrentUser.mockResolvedValueOnce({
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      tenant_id: 1,
      roles: ['user'],
      created_at: '2023-01-01T00:00:00Z'
    });

    renderWithQueryClient(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('shows loading fallback while checking authentication', () => {
    mockedGetCurrentUser.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        tenant_id: 1,
        roles: ['user'],
        created_at: '2023-01-01T00:00:00Z'
      }), 100))
    );

    renderWithQueryClient(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
  });

  it('shows custom fallback while checking authentication', () => {
    mockedGetCurrentUser.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        tenant_id: 1,
        roles: ['user'],
        created_at: '2023-01-01T00:00:00Z'
      }), 100))
    );

    renderWithQueryClient(
      <ProtectedRoute fallback={<div>Custom Loading...</div>}>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Custom Loading...')).toBeInTheDocument();
  });

  it('returns null when user is not authenticated', async () => {
    mockedGetCurrentUser.mockRejectedValueOnce(new Error('Not authenticated'));

    const { container } = renderWithQueryClient(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('uses stale time for caching authentication status', async () => {
    mockedGetCurrentUser.mockResolvedValue({
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      tenant_id: 1,
      roles: ['user'],
      created_at: '2023-01-01T00:00:00Z'
    });

    const queryClient = createQueryClient();

    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    rerender(
      <QueryClientProvider client={queryClient}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </QueryClientProvider>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
    expect(mockedGetCurrentUser).toHaveBeenCalledTimes(1);
  });
});