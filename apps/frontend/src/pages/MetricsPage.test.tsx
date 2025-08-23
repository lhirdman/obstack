import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MetricsPage from './MetricsPage';
import { apiClient } from '../lib/api-client';

// Mock the API client
vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Mock ECharts component
vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: any }) => (
    <div data-testid="echarts-mock">
      {option?.title?.text && <div data-testid="chart-title">{option.title.text}</div>}
      {option?.series && <div data-testid="chart-series">{JSON.stringify(option.series)}</div>}
    </div>
  ),
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

describe('MetricsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the metrics page with initial state', () => {
    render(<MetricsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Metrics')).toBeInTheDocument();
    expect(screen.getByText('Query and visualize metrics from your observability stack')).toBeInTheDocument();
    expect(screen.getByText('No query executed')).toBeInTheDocument();
    expect(screen.getByDisplayValue('up')).toBeInTheDocument(); // Default query
  });

  it('allows changing query type between instant and range', () => {
    render(<MetricsPage />, { wrapper: createWrapper() });

    const instantRadio = screen.getByLabelText('Instant Query');
    const rangeRadio = screen.getByLabelText('Range Query');

    expect(rangeRadio).toBeChecked(); // Default is range
    expect(instantRadio).not.toBeChecked();

    fireEvent.click(instantRadio);
    expect(instantRadio).toBeChecked();
    expect(rangeRadio).not.toBeChecked();
  });

  it('allows editing the query', () => {
    render(<MetricsPage />, { wrapper: createWrapper() });

    const queryTextarea = screen.getByDisplayValue('up');
    fireEvent.change(queryTextarea, { target: { value: 'cpu_usage' } });

    expect(screen.getByDisplayValue('cpu_usage')).toBeInTheDocument();
  });

  it('executes range query when execute button is clicked', async () => {
    const mockResponse = {
      status: 'success',
      data: {
        resultType: 'matrix',
        result: [
          {
            metric: { __name__: 'up', job: 'prometheus' },
            values: [
              [1640995200, '1'],
              [1640995260, '1'],
            ],
          },
        ],
      },
    };

    (apiClient.post as any).mockResolvedValue(mockResponse);

    render(<MetricsPage />, { wrapper: createWrapper() });

    const executeButton = screen.getByText('Execute Query');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/metrics/query_range', {
        query: 'up',
        start: expect.any(String),
        end: expect.any(String),
        step: '15s',
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId('chart-title')).toHaveTextContent('Range Query: up');
    });
  });

  it('executes instant query when query type is instant', async () => {
    const mockResponse = {
      status: 'success',
      data: {
        resultType: 'vector',
        result: [
          {
            metric: { __name__: 'up', job: 'prometheus' },
            value: [1640995200, '1'],
          },
        ],
      },
    };

    (apiClient.post as any).mockResolvedValue(mockResponse);

    render(<MetricsPage />, { wrapper: createWrapper() });

    // Switch to instant query
    const instantRadio = screen.getByLabelText('Instant Query');
    fireEvent.click(instantRadio);

    const executeButton = screen.getByText('Execute Query');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/metrics/query', {
        query: 'up',
        time: expect.any(String),
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId('chart-title')).toHaveTextContent('Instant Query: up');
    });
  });

  it('displays error when query fails', async () => {
    const mockError = new Error('Query failed');
    (apiClient.post as any).mockRejectedValue(mockError);

    render(<MetricsPage />, { wrapper: createWrapper() });

    const executeButton = screen.getByText('Execute Query');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByText('Query Error')).toBeInTheDocument();
      expect(screen.getByText('Query failed')).toBeInTheDocument();
    });
  });

  it('shows loading state during query execution', async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    (apiClient.post as any).mockReturnValue(mockPromise);

    render(<MetricsPage />, { wrapper: createWrapper() });

    const executeButton = screen.getByText('Execute Query');
    fireEvent.click(executeButton);

    // Should show loading state
    expect(screen.getByText('Executing...')).toBeInTheDocument();
    expect(screen.getByText('Executing query...')).toBeInTheDocument();

    // Resolve the promise
    resolvePromise!({
      status: 'success',
      data: { resultType: 'vector', result: [] },
    });

    await waitFor(() => {
      expect(screen.queryByText('Executing...')).not.toBeInTheDocument();
    });
  });

  it('disables execute button when query is empty', () => {
    render(<MetricsPage />, { wrapper: createWrapper() });

    const queryTextarea = screen.getByDisplayValue('up');
    fireEvent.change(queryTextarea, { target: { value: '' } });

    const executeButton = screen.getByText('Execute Query');
    expect(executeButton).toBeDisabled();
  });

  it('shows time range controls for range queries', () => {
    render(<MetricsPage />, { wrapper: createWrapper() });

    // Should show step selector for range queries
    expect(screen.getByText('Resolution (Step)')).toBeInTheDocument();
    expect(screen.getByText('15s')).toBeInTheDocument(); // Default step
  });

  it('hides step controls for instant queries', () => {
    render(<MetricsPage />, { wrapper: createWrapper() });

    // Switch to instant query
    const instantRadio = screen.getByLabelText('Instant Query');
    fireEvent.click(instantRadio);

    // Step selector should not be visible
    expect(screen.queryByText('Resolution (Step)')).not.toBeInTheDocument();
  });
});