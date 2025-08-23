import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RegisterForm from './RegisterForm';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

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

describe('RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders registration form with all required fields', () => {
    renderWithQueryClient(<RegisterForm />);
    
    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization name/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('allows user to type in all form fields', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email address/i);
    const tenantInput = screen.getByLabelText(/organization name/i);
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@example.com');
    await user.clear(tenantInput);
    await user.type(tenantInput, 'test-org');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');
    
    expect(usernameInput).toHaveValue('testuser');
    expect(emailInput).toHaveValue('test@example.com');
    expect(tenantInput).toHaveValue('test-org');
    expect(passwordInput).toHaveValue('password123');
    expect(confirmPasswordInput).toHaveValue('password123');
  });

  it('toggles password visibility for both password fields', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const toggleButtons = screen.getAllByRole('button', { name: '' }); // Eye icon buttons
    
    // Initially passwords should be hidden
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(confirmPasswordInput).toHaveAttribute('type', 'password');
    
    // Click to show first password
    await user.click(toggleButtons[0]!);
    expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click to show second password
    await user.click(toggleButtons[1]!);
    expect(confirmPasswordInput).toHaveAttribute('type', 'text');
  });

  it('validates password length', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const passwordInput = screen.getByLabelText('Password');
    
    await user.type(passwordInput, 'short');
    
    expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    expect(passwordInput).toHaveClass('border-red-300');
  });

  it('validates password confirmation match', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'different123');
    
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(confirmPasswordInput).toHaveClass('border-red-300');
  });

  it('submits form with correct data on successful registration', async () => {
    const user = userEvent.setup();
    const mockOnSuccess = vi.fn();
    
    const mockResponse = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      tenant_id: 1,
      roles: ['user'],
      created_at: '2023-01-01T00:00:00Z',
    };
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });
    
    renderWithQueryClient(<RegisterForm onSuccess={mockOnSuccess} />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email address/i);
    const tenantInput = screen.getByLabelText(/organization name/i);
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@example.com');
    await user.clear(tenantInput);
    await user.type(tenantInput, 'test-org');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'testuser',
          email: 'test@example.com',
          password: 'password123',
          tenant_name: 'test-org',
        }),
      });
    });
    
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it('displays error message on failed registration', async () => {
    const user = userEvent.setup();
    const mockOnError = vi.fn();
    
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({
        detail: 'Email already registered',
      }),
    });
    
    renderWithQueryClient(<RegisterForm onError={mockOnError} />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'existing@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Email already registered')).toBeInTheDocument();
      expect(mockOnError).toHaveBeenCalledWith('Email already registered');
    });
  });

  it('prevents submission when passwords do not match', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'different123');
    
    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('prevents submission when password is too short', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await user.type(passwordInput, 'short');
    
    expect(await screen.findByText('Password must be at least 8 characters long')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('disables submit button when form is invalid', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);
    
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await user.type(passwordInput, 'short');
    await user.type(confirmPasswordInput, 'different');
    
    expect(submitButton).toBeDisabled();
  });

  it('has default tenant name', () => {
    renderWithQueryClient(<RegisterForm />);
    
    const tenantInput = screen.getByLabelText(/organization name/i);
    expect(tenantInput).toHaveValue('default');
  });

  it('requires username and email fields', () => {
    renderWithQueryClient(<RegisterForm />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    expect(usernameInput).toBeRequired();
    expect(emailInput).toBeRequired();
    expect(passwordInput).toBeRequired();
    expect(confirmPasswordInput).toBeRequired();
  });

  it('validates email format', () => {
    renderWithQueryClient(<RegisterForm />);
    
    const emailInput = screen.getByLabelText(/email address/i);
    expect(emailInput).toHaveAttribute('type', 'email');
  });
});