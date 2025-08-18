/**
 * Cost dashboard filters component for filtering cost data
 */

import React from 'react';
import type { CostDashboardFilters } from '../../types/costs';

interface CostDashboardFiltersProps {
  filters: CostDashboardFilters;
  onFiltersChange: (filters: CostDashboardFilters) => void;
  clusters?: string[];
  namespaces?: string[];
  workloads?: string[];
  loading?: boolean;
  className?: string;
}

export function CostDashboardFilters({
  filters,
  onFiltersChange,
  clusters = [],
  namespaces = [],
  workloads = [],
  loading = false,
  className = ''
}: CostDashboardFiltersProps) {
  const handleFilterChange = (key: keyof CostDashboardFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  const handleTimeRangeChange = (key: 'from' | 'to', value: string) => {
    onFiltersChange({
      ...filters,
      timeRange: {
        ...filters.timeRange,
        [key]: value
      }
    });
  };

  const getPresetTimeRanges = () => {
    const now = new Date();
    const ranges = [
      {
        label: 'Last Hour',
        from: new Date(now.getTime() - 60 * 60 * 1000).toISOString(),
        to: now.toISOString()
      },
      {
        label: 'Last 6 Hours',
        from: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
        to: now.toISOString()
      },
      {
        label: 'Last 24 Hours',
        from: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString(),
        to: now.toISOString()
      },
      {
        label: 'Last 7 Days',
        from: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        to: now.toISOString()
      },
      {
        label: 'Last 30 Days',
        from: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        to: now.toISOString()
      }
    ];
    return ranges;
  };

  const applyPresetTimeRange = (preset: { from: string; to: string }) => {
    onFiltersChange({
      ...filters,
      timeRange: preset
    });
  };

  const formatDateTimeLocal = (isoString: string) => {
    const date = new Date(isoString);
    return date.toISOString().slice(0, 16); // Format for datetime-local input
  };

  const parseLocalDateTime = (localDateTime: string) => {
    return new Date(localDateTime).toISOString();
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Cluster Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cluster
          </label>
          <select
            value={filters.cluster || ''}
            onChange={(e) => handleFilterChange('cluster', e.target.value || undefined)}
            disabled={loading}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">All Clusters</option>
            {clusters.map(cluster => (
              <option key={cluster} value={cluster}>{cluster}</option>
            ))}
          </select>
        </div>

        {/* Namespace Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Namespace
          </label>
          <select
            value={filters.namespace || ''}
            onChange={(e) => handleFilterChange('namespace', e.target.value || undefined)}
            disabled={loading || !filters.cluster}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">All Namespaces</option>
            {namespaces.map(namespace => (
              <option key={namespace} value={namespace}>{namespace}</option>
            ))}
          </select>
        </div>

        {/* Workload Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Workload
          </label>
          <select
            value={filters.workload || ''}
            onChange={(e) => handleFilterChange('workload', e.target.value || undefined)}
            disabled={loading || !filters.namespace}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">All Workloads</option>
            {workloads.map(workload => (
              <option key={workload} value={workload}>{workload}</option>
            ))}
          </select>
        </div>

        {/* Group By Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Group By
          </label>
          <select
            value={filters.groupBy}
            onChange={(e) => handleFilterChange('groupBy', e.target.value as 'namespace' | 'workload' | 'service')}
            disabled={loading}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="namespace">Namespace</option>
            <option value="workload">Workload</option>
            <option value="service">Service</option>
          </select>
        </div>
      </div>

      {/* Time Range Section */}
      <div className="mt-6">
        <h4 className="text-md font-medium text-gray-900 mb-3">Time Range</h4>
        
        {/* Preset Time Ranges */}
        <div className="flex flex-wrap gap-2 mb-4">
          {getPresetTimeRanges().map((preset, index) => (
            <button
              key={index}
              onClick={() => applyPresetTimeRange(preset)}
              disabled={loading}
              className="px-3 py-1 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Custom Time Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From
            </label>
            <input
              type="datetime-local"
              value={formatDateTimeLocal(filters.timeRange.from)}
              onChange={(e) => handleTimeRangeChange('from', parseLocalDateTime(e.target.value))}
              disabled={loading}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To
            </label>
            <input
              type="datetime-local"
              value={formatDateTimeLocal(filters.timeRange.to)}
              onChange={(e) => handleTimeRangeChange('to', parseLocalDateTime(e.target.value))}
              disabled={loading}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 flex justify-between items-center">
        <button
          onClick={() => {
            const now = new Date();
            const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            onFiltersChange({
              cluster: undefined,
              namespace: undefined,
              workload: undefined,
              timeRange: {
                from: oneDayAgo.toISOString(),
                to: now.toISOString()
              },
              groupBy: 'namespace'
            });
          }}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Reset Filters
        </button>
        
        <div className="text-sm text-gray-500">
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          ) : (
            `Showing data from ${new Date(filters.timeRange.from).toLocaleDateString()} to ${new Date(filters.timeRange.to).toLocaleDateString()}`
          )}
        </div>
      </div>
    </div>
  );
}