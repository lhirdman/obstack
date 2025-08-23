import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChartBarIcon, ClockIcon, PlayIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../lib/api-client';
import TimeRangeSelector from '../components/TimeRangeSelector';
import MetricsChart from '../components/MetricsChart';
import QueryBuilder from '../components/QueryBuilder';

interface MetricsQueryRequest {
  query: string;
  time?: string;
}

interface MetricsRangeQueryRequest {
  query: string;
  start: string;
  end: string;
  step: string;
}

interface MetricsResponse {
  status: string;
  data: {
    resultType: string;
    result: any[];
  };
}

const MetricsPage: React.FC = () => {
  const [query, setQuery] = useState('up');
  const [timeRange, setTimeRange] = useState({
    start: new Date(Date.now() - 3600000), // 1 hour ago
    end: new Date(),
    step: '15s'
  });
  const [queryType, setQueryType] = useState<'instant' | 'range'>('range');
  const [executeQuery, setExecuteQuery] = useState(false);

  // Query for metrics data
  const { data: metricsData, isLoading, error, refetch } = useQuery({
    queryKey: ['metrics', query, timeRange, queryType],
    queryFn: async (): Promise<MetricsResponse> => {
      if (queryType === 'instant') {
        const request: MetricsQueryRequest = {
          query,
          time: timeRange.end.toISOString()
        };
        return apiClient.post('/metrics/query', request);
      } else {
        const request: MetricsRangeQueryRequest = {
          query,
          start: timeRange.start.toISOString(),
          end: timeRange.end.toISOString(),
          step: timeRange.step
        };
        return apiClient.post('/metrics/query_range', request);
      }
    },
    enabled: executeQuery && !!query.trim(),
    retry: false,
    staleTime: 30000, // 30 seconds
  });

  const handleExecuteQuery = () => {
    setExecuteQuery(true);
    refetch();
  };

  const handleTimeRangeChange = (newTimeRange: typeof timeRange) => {
    setTimeRange(newTimeRange);
    if (executeQuery) {
      // Auto-refresh if query was already executed
      setTimeout(() => refetch(), 100);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Metrics</h1>
          </div>
          <p className="mt-2 text-gray-600">
            Query and visualize metrics from your observability stack
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Query Configuration</h2>
          </div>
          <div className="p-6 space-y-6">
            {/* Query Type Selector */}
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">
                Query Type
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="instant"
                    checked={queryType === 'instant'}
                    onChange={(e) => setQueryType(e.target.value as 'instant' | 'range')}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <span className="ml-2 text-sm text-gray-700">Instant Query</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="range"
                    checked={queryType === 'range'}
                    onChange={(e) => setQueryType(e.target.value as 'instant' | 'range')}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <span className="ml-2 text-sm text-gray-700">Range Query</span>
                </label>
              </div>
            </div>

            {/* Query Builder */}
            <QueryBuilder
              query={query}
              onQueryChange={setQuery}
              onExecute={handleExecuteQuery}
            />

            {/* Time Range Selector */}
            <TimeRangeSelector
              timeRange={timeRange}
              onTimeRangeChange={handleTimeRangeChange}
              showStep={queryType === 'range'}
            />

            {/* Execute Button */}
            <div className="flex justify-end">
              <button
                onClick={handleExecuteQuery}
                disabled={!query.trim() || isLoading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Executing...
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Execute Query
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">Results</h2>
              {metricsData && (
                <div className="flex items-center text-sm text-gray-500">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  Last updated: {new Date().toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
          <div className="p-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Query Error
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      {error instanceof Error ? error.message : 'An error occurred while executing the query'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!executeQuery && (
              <div className="text-center py-12">
                <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No query executed</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Enter a PromQL query above and click "Execute Query" to see results.
                </p>
              </div>
            )}

            {executeQuery && isLoading && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-sm text-gray-500">Executing query...</p>
              </div>
            )}

            {executeQuery && !isLoading && !error && metricsData && (
              <MetricsChart
                data={metricsData}
                queryType={queryType}
                query={query}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsPage;