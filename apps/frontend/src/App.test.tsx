import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { authService } from './services/auth';
import { configService } from './lib/config';

// Mock the auth service
vi.mock('./services/auth', () => ({
  authService: {
    init: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

// Mock the config service
vi.mock('./lib/config', () => ({
  configService: {
    getAuthMethod: vi.fn(),
  },
}));

// Mock the components that might cause issues
vi.mock('./components/auth/AuthPage', () => ({
  default: () => <div data-testid="auth-page">Auth Page</div>,
}));

vi.mock('./components/auth/KeycloakCallback', () => ({
  default: () => <div data-testid="keycloak-callback">Keycloak Callback</div>,
}));

vi.mock('./components/auth/ProtectedRoute', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="protected-route">{children}</div>,
}));

vi.mock('./components/Dashboard', () => ({
  default: () => <div data-testid="dashboard">Dashboard</div>,
}));

vi.mock('./components/Navbar', () => ({
  default: () => <div data-testid="navbar">Navbar</div>,
}));

const mockedAuthService = vi.mocked(authService);
const mockedConfigService = vi.mocked(configService);

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAuthService.init.mockResolvedValue(true);
    mockedConfigService.getAuthMethod.mockReturnValue('local');
  });

  it('renders loading state initially', () => {
    mockedAuthService.getCurrentUser.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<App />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders auth page when user is not authenticated', async () => {
    mockedAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-page')).toBeInTheDocument();
    });
  });

  it('renders dashboard when user is authenticated', async () => {
    mockedAuthService.getCurrentUser.mockResolvedValue({
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      tenant_id: 1,
      roles: ['user'],
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByTestId('navbar')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });
});