import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, afterEach } from 'vitest';
import Navbar from './Navbar';
import { authService } from '../services/auth';

vi.mock('../services/auth', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    authService: {
      ...actual.authService,
      logout: vi.fn(),
    },
  };
});

const mockedLogout = vi.mocked(authService.logout);

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

describe('Navbar', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders the navbar with ObservaStack title', () => {
    renderWithQueryClient(<Navbar />);
    expect(screen.getByText('ObservaStack')).toBeInTheDocument();
  });

  it('renders the logout button', () => {
    renderWithQueryClient(<Navbar />);
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    expect(logoutButton).toBeInTheDocument();
  });

  it('calls logout service and onLogout callback when logout button is clicked', async () => {
    mockedLogout.mockResolvedValueOnce({ message: 'Successfully logged out' });
    const mockOnLogout = vi.fn();

    renderWithQueryClient(<Navbar onLogout={mockOnLogout} />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockedLogout).toHaveBeenCalled();
      expect(mockOnLogout).toHaveBeenCalled();
    });
  });

  it('shows loading state while logout is pending', async () => {
    mockedLogout.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({ message: 'Successfully logged out' }), 100))
    );

    renderWithQueryClient(<Navbar />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);

    await screen.findByText('Logging out...');
    expect(logoutButton).toBeDisabled();
  });

  it('calls onLogout even when logout API fails', async () => {
    mockedLogout.mockRejectedValueOnce(new Error('Network error'));
    const mockOnLogout = vi.fn();

    renderWithQueryClient(<Navbar onLogout={mockOnLogout} />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockOnLogout).toHaveBeenCalled();
    });
  });

  it('clears query cache on successful logout', async () => {
    mockedLogout.mockResolvedValueOnce({ message: 'Successfully logged out' });
    const queryClient = createQueryClient();
    const clearSpy = vi.spyOn(queryClient, 'clear');

    render(
      <QueryClientProvider client={queryClient}>
        <Navbar />
      </QueryClientProvider>
    );
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(clearSpy).toHaveBeenCalled();
    });
  });
});