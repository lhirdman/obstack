import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MetricsChart from './MetricsChart';

// Mock ECharts component
vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: any }) => (
    <div data-testid="echarts-mock">
      {option?.title?.text && <div data-testid="chart-title">{option.title.text}</div>}
      {option?.series && <div data-testid="chart-series">{JSON.stringify(option.series)}</div>}
      {option?.xAxis && <div data-testid="chart-xaxis">{JSON.stringify(option.xAxis)}</div>}
      {option?.yAxis && <div data-testid="chart-yaxis">{JSON.stringify(option.yAxis)}</div>}
    </div>
  ),
}));

describe('MetricsChart', () => {
  const mockInstantData = {
    status: 'success',
    data: {
      resultType: 'vector',
      result: [
        {
          metric: { __name__: 'up', job: 'prometheus' },
          value: [1640995200, '1'],
        },
        {
          metric: { __name__: 'up', job: 'node-exporter' },
          value: [1640995200, '0'],
        },
      ],
    },
  };

  const mockRangeData = {
    status: 'success',
    data: {
      resultType: 'matrix',
      result: [
        {
          metric: { __name__: 'cpu_usage', instance: 'server1' },
          values: [
            [1640995200, '0.5'],
            [1640995260, '0.6'],
            [1640995320, '0.4'],
          ],
        },
        {
          metric: { __name__: 'cpu_usage', instance: 'server2' },
          values: [
            [1640995200, '0.3'],
            [1640995260, '0.4'],
            [1640995320, '0.2'],
          ],
        },
      ],
    },
  };

  it('renders instant query as bar chart', () => {
    render(
      <MetricsChart
        data={mockInstantData}
        queryType="instant"
        query="up"
      />
    );

    expect(screen.getByTestId('chart-title')).toHaveTextContent('Instant Query: up');
    expect(screen.getByTestId('echarts-mock')).toBeInTheDocument();
    
    // Check summary information
    expect(screen.getByText('Query Results Summary')).toBeInTheDocument();
    expect(screen.getByText('vector')).toBeInTheDocument(); // Result type
    expect(screen.getByText('2')).toBeInTheDocument(); // Series count
    expect(screen.getByText('success')).toBeInTheDocument(); // Status
  });

  it('renders range query as line chart', () => {
    render(
      <MetricsChart
        data={mockRangeData}
        queryType="range"
        query="cpu_usage"
      />
    );

    expect(screen.getByTestId('chart-title')).toHaveTextContent('Range Query: cpu_usage');
    expect(screen.getByTestId('echarts-mock')).toBeInTheDocument();
    
    // Check summary information
    expect(screen.getByText('Query Results Summary')).toBeInTheDocument();
    expect(screen.getByText('matrix')).toBeInTheDocument(); // Result type
    expect(screen.getByText('2')).toBeInTheDocument(); // Series count
    expect(screen.getByText('6')).toBeInTheDocument(); // Total data points (3 + 3)
  });

  it('shows no data message when result is empty', () => {
    const emptyData = {
      status: 'success',
      data: {
        resultType: 'vector',
        result: [],
      },
    };

    render(
      <MetricsChart
        data={emptyData}
        queryType="instant"
        query="up"
      />
    );

    expect(screen.getByText('No data')).toBeInTheDocument();
    expect(screen.getByText('The query returned no results. Try adjusting your query or time range.')).toBeInTheDocument();
  });

  it('shows error message when data is invalid', () => {
    render(
      <MetricsChart
        data={null as any}
        queryType="instant"
        query="up"
      />
    );

    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  it('formats metric names correctly', () => {
    const dataWithLabels = {
      status: 'success',
      data: {
        resultType: 'vector',
        result: [
          {
            metric: { 
              __name__: 'http_requests_total',
              method: 'GET',
              status: '200',
              instance: 'server1:8080'
            },
            value: [1640995200, '100'],
          },
        ],
      },
    };

    render(
      <MetricsChart
        data={dataWithLabels}
        queryType="instant"
        query="http_requests_total"
      />
    );

    // The chart should be rendered (metric name formatting is internal)
    expect(screen.getByTestId('echarts-mock')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Series count
  });

  it('handles metrics without __name__ field', () => {
    const dataWithoutName = {
      status: 'success',
      data: {
        resultType: 'vector',
        result: [
          {
            metric: { 
              job: 'prometheus',
              instance: 'localhost:9090'
            },
            value: [1640995200, '1'],
          },
        ],
      },
    };

    render(
      <MetricsChart
        data={dataWithoutName}
        queryType="instant"
        query="some_metric"
      />
    );

    expect(screen.getByTestId('echarts-mock')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Series count
  });

  it('displays correct summary for range queries', () => {
    render(
      <MetricsChart
        data={mockRangeData}
        queryType="range"
        query="cpu_usage"
      />
    );

    // Check all summary fields
    expect(screen.getByText('Result Type:')).toBeInTheDocument();
    expect(screen.getByText('Series Count:')).toBeInTheDocument();
    expect(screen.getByText('Data Points:')).toBeInTheDocument();
    expect(screen.getByText('Status:')).toBeInTheDocument();
  });

  it('displays correct summary for instant queries', () => {
    render(
      <MetricsChart
        data={mockInstantData}
        queryType="instant"
        query="up"
      />
    );

    // Check summary fields (no data points for instant queries)
    expect(screen.getByText('Result Type:')).toBeInTheDocument();
    expect(screen.getByText('Series Count:')).toBeInTheDocument();
    expect(screen.getByText('Status:')).toBeInTheDocument();
    expect(screen.queryByText('Data Points:')).not.toBeInTheDocument();
  });
});