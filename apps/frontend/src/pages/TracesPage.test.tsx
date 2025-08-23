import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TracesPage from './TracesPage';
import { apiClient } from '../lib/api-client';

// Mock the API client
vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('TracesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the traces page with initial state', () => {
    render(<TracesPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Traces')).toBeInTheDocument();
    expect(screen.getByText('Search and visualize distributed traces to understand request flows and performance')).toBeInTheDocument();
    expect(screen.getByText('No trace selected')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)')).toBeInTheDocument();
  });

  it('allows entering a trace ID', () => {
    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });

    expect(traceIdInput).toHaveValue('1234567890abcdef');
  });

  it('validates trace ID format', () => {
    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    
    // Invalid trace ID
    fireEvent.change(traceIdInput, { target: { value: 'invalid-trace-id' } });
    expect(screen.getByText('Trace ID should be a hexadecimal string (16-32 characters)')).toBeInTheDocument();

    // Valid trace ID
    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    expect(screen.getByText('Valid trace ID format')).toBeInTheDocument();
  });

  it('searches for a trace when form is submitted', async () => {
    const mockTraceData = {
      batches: [
        {
          resource: {
            attributes: [
              {
                key: 'service.name',
                value: { stringValue: 'frontend' }
              }
            ]
          },
          scopeSpans: [
            {
              spans: [
                {
                  traceId: '1234567890abcdef',
                  spanId: 'abcdef1234567890',
                  name: 'GET /api/users',
                  startTimeUnixNano: '1640995200000000000',
                  endTimeUnixNano: '1640995201000000000',
                  attributes: [
                    {
                      key: 'http.method',
                      value: { stringValue: 'GET' }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    };

    (apiClient.get as any).mockResolvedValue(mockTraceData);

    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    const searchButton = screen.getByText('Search Trace');

    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/traces/1234567890abcdef');
    });

    await waitFor(() => {
      expect(screen.getByText('1 spans')).toBeInTheDocument();
    });
  });

  it('handles trace not found error', async () => {
    const mockError = new Error('Trace not found');
    (apiClient.get as any).mockRejectedValue(mockError);

    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    const searchButton = screen.getByText('Search Trace');

    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Trace Not Found')).toBeInTheDocument();
      expect(screen.getByText('Trace not found')).toBeInTheDocument();
    });
  });

  it('shows loading state during search', async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    (apiClient.get as any).mockReturnValue(mockPromise);

    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    const searchButton = screen.getByText('Search Trace');

    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.click(searchButton);

    // Should show loading state
    expect(screen.getByText('Searching...')).toBeInTheDocument();
    expect(screen.getByText('Loading trace...')).toBeInTheDocument();

    // Resolve the promise
    resolvePromise!({
      batches: []
    });

    await waitFor(() => {
      expect(screen.queryByText('Searching...')).not.toBeInTheDocument();
    });
  });

  it('disables search button when trace ID is empty', () => {
    render(<TracesPage />, { wrapper: createWrapper() });

    const searchButton = screen.getByText('Search Trace');
    expect(searchButton).toBeDisabled();

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });

    expect(searchButton).not.toBeDisabled();
  });

  it('can search by pressing Enter', async () => {
    const mockTraceData = {
      batches: [
        {
          resource: {
            attributes: [
              {
                key: 'service.name',
                value: { stringValue: 'frontend' }
              }
            ]
          },
          scopeSpans: [
            {
              spans: [
                {
                  traceId: '1234567890abcdef',
                  spanId: 'abcdef1234567890',
                  name: 'GET /api/users',
                  startTimeUnixNano: '1640995200000000000',
                  endTimeUnixNano: '1640995201000000000',
                  attributes: []
                }
              ]
            }
          ]
        }
      ]
    };

    (apiClient.get as any).mockResolvedValue(mockTraceData);

    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.submit(traceIdInput.closest('form')!);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/traces/1234567890abcdef');
    });
  });

  it('shows search history', async () => {
    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    const searchButton = screen.getByText('Search Trace');

    // First search
    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Recent Searches')).toBeInTheDocument();
      expect(screen.getByText('1234567890abcdef')).toBeInTheDocument();
    });
  });

  it('shows span details when span is selected', async () => {
    const mockTraceData = {
      batches: [
        {
          resource: {
            attributes: [
              {
                key: 'service.name',
                value: { stringValue: 'frontend' }
              }
            ]
          },
          scopeSpans: [
            {
              spans: [
                {
                  traceId: '1234567890abcdef',
                  spanId: 'abcdef1234567890',
                  name: 'GET /api/users',
                  startTimeUnixNano: '1640995200000000000',
                  endTimeUnixNano: '1640995201000000000',
                  attributes: [
                    {
                      key: 'http.method',
                      value: { stringValue: 'GET' }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    };

    (apiClient.get as any).mockResolvedValue(mockTraceData);

    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    const searchButton = screen.getByText('Search Trace');

    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('GET /api/users')).toBeInTheDocument();
    });

    // Initially should show "click on a span" message
    expect(screen.getByText('Click on a span in the waterfall to view its details')).toBeInTheDocument();

    // Click on the span
    const spanElement = screen.getByText('GET /api/users').closest('div[role="button"], div[class*="cursor-pointer"]') || 
                       screen.getByText('GET /api/users').closest('div');
    if (spanElement) {
      fireEvent.click(spanElement);
      
      await waitFor(() => {
        expect(screen.getByText('Span Overview')).toBeInTheDocument();
      });
    }
  });

  it('handles empty trace data', async () => {
    const mockTraceData = {
      batches: []
    };

    (apiClient.get as any).mockResolvedValue(mockTraceData);

    render(<TracesPage />, { wrapper: createWrapper() });

    const traceIdInput = screen.getByPlaceholderText('Enter trace ID (e.g., 1234567890abcdef)');
    const searchButton = screen.getByText('Search Trace');

    fireEvent.change(traceIdInput, { target: { value: '1234567890abcdef' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('No spans found')).toBeInTheDocument();
      expect(screen.getByText('The trace exists but contains no span data.')).toBeInTheDocument();
    });
  });
});