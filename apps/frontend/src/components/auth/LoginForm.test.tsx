import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginForm from './LoginForm';
import { authService } from '../../services/auth';

vi.mock('../../services/auth', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    authService: {
      ...actual.authService,
      login: vi.fn(),
    },
  };
});

const mockedLogin = vi.mocked(authService.login);

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('LoginForm', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form with all required fields', () => {
    renderWithQueryClient(<LoginForm />);
    
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('allows user to type in email and password fields', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<LoginForm />);
    
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    
    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('submits form with correct data on successful login', async () => {
    const user = userEvent.setup();
    const mockOnSuccess = vi.fn();
    
    mockedLogin.mockResolvedValueOnce({
      access_token: 'mock-token',
      token_type: 'bearer',
    });

    renderWithQueryClient(<LoginForm onSuccess={mockOnSuccess} />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });
});