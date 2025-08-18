/**
 * Alert filters component
 */

import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Button, Input, Select } from '../ui'
import type { AlertFilters as AlertFiltersType } from '../../types/alerts'

export interface AlertFiltersProps {
  filters: AlertFiltersType
  onFiltersChange: (updates: Partial<AlertFiltersType>) => void
  onClearFilters: () => void
  hasActiveFilters: boolean
  className?: string
}

const SEVERITY_OPTIONS = [
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
  { value: 'info', label: 'Info' }
]

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'silenced', label: 'Silenced' }
]

const SOURCE_OPTIONS = [
  { value: 'prometheus', label: 'Prometheus' },
  { value: 'loki', label: 'Loki' },
  { value: 'tempo', label: 'Tempo' },
  { value: 'opensearch', label: 'OpenSearch' },
  { value: 'external', label: 'External' }
]

const TIME_RANGE_OPTIONS = [
  { value: 'now-1h', label: 'Last hour' },
  { value: 'now-6h', label: 'Last 6 hours' },
  { value: 'now-24h', label: 'Last 24 hours' },
  { value: 'now-7d', label: 'Last 7 days' },
  { value: 'now-30d', label: 'Last 30 days' },
  { value: 'custom', label: 'Custom range' }
]

export function AlertFilters({
  filters,
  onFiltersChange,
  onClearFilters,
  hasActiveFilters,
  className
}: AlertFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [customTimeRange, setCustomTimeRange] = useState({
    from: '',
    to: ''
  })

  const handleMultiSelectChange = (
    field: 'status' | 'severity' | 'source',
    value: string,
    checked: boolean
  ) => {
    const currentValues = filters[field]
    const newValues = checked
      ? [...currentValues, value]
      : currentValues.filter(v => v !== value)
    
    onFiltersChange({ [field]: newValues })
  }

  const handleTimeRangeChange = (value: string) => {
    if (value === 'custom') {
      setIsExpanded(true)
      return
    }
    
    onFiltersChange({
      timeRange: {
        from: value,
        to: 'now'
      }
    })
  }

  const handleCustomTimeRangeApply = () => {
    if (customTimeRange.from && customTimeRange.to) {
      onFiltersChange({
        timeRange: {
          from: customTimeRange.from,
          to: customTimeRange.to
        }
      })
    }
  }

  const isCustomTimeRange = !TIME_RANGE_OPTIONS.some(
    option => option.value === filters.timeRange.from && filters.timeRange.to === 'now'
  )

  return (
    <div className={clsx('bg-white border border-gray-200 rounded-lg p-4', className)}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        <div className="flex items-center space-x-2">
          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={onClearFilters}
            >
              Clear all
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <Input
          placeholder="Search alerts..."
          value={filters.searchText}
          onChange={(e) => onFiltersChange({ searchText: e.target.value })}
          leftIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
        />
      </div>

      {/* Quick filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {/* Status filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <div className="space-y-1">
            {STATUS_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={filters.status.includes(option.value)}
                  onChange={(e) => handleMultiSelectChange('status', option.value, e.target.checked)}
                />
                <span className="ml-2 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Severity filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity
          </label>
          <div className="space-y-1">
            {SEVERITY_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={filters.severity.includes(option.value)}
                  onChange={(e) => handleMultiSelectChange('severity', option.value, e.target.checked)}
                />
                <span className="ml-2 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Source filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Source
          </label>
          <div className="space-y-1">
            {SOURCE_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={filters.source.includes(option.value)}
                  onChange={(e) => handleMultiSelectChange('source', option.value, e.target.checked)}
                />
                <span className="ml-2 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Time range filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Time Range
          </label>
          <Select
            value={isCustomTimeRange ? 'custom' : filters.timeRange.from}
            onChange={handleTimeRangeChange}
            options={TIME_RANGE_OPTIONS}
          />
        </div>
      </div>

      {/* Expanded filters */}
      {isExpanded && (
        <div className="border-t border-gray-200 pt-4 space-y-4">
          {/* Assignee filter */}
          <div>
            <Input
              label="Assignee"
              placeholder="Filter by assignee..."
              value={filters.assignee}
              onChange={(e) => onFiltersChange({ assignee: e.target.value })}
            />
          </div>

          {/* Custom time range */}
          {(isCustomTimeRange || filters.timeRange.from === 'custom') && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Input
                  label="From"
                  type="datetime-local"
                  value={customTimeRange.from}
                  onChange={(e) => setCustomTimeRange(prev => ({ ...prev, from: e.target.value }))}
                />
              </div>
              <div>
                <Input
                  label="To"
                  type="datetime-local"
                  value={customTimeRange.to}
                  onChange={(e) => setCustomTimeRange(prev => ({ ...prev, to: e.target.value }))}
                />
              </div>
              <div className="flex items-end">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleCustomTimeRangeApply}
                  disabled={!customTimeRange.from || !customTimeRange.to}
                >
                  Apply
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Active filters summary */}
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            {filters.status.map(status => (
              <span
                key={status}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                Status: {status}
                <button
                  type="button"
                  className="ml-1 text-blue-600 hover:text-blue-800"
                  onClick={() => handleMultiSelectChange('status', status, false)}
                >
                  ×
                </button>
              </span>
            ))}
            {filters.severity.map(severity => (
              <span
                key={severity}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
              >
                Severity: {severity}
                <button
                  type="button"
                  className="ml-1 text-yellow-600 hover:text-yellow-800"
                  onClick={() => handleMultiSelectChange('severity', severity, false)}
                >
                  ×
                </button>
              </span>
            ))}
            {filters.source.map(source => (
              <span
                key={source}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
              >
                Source: {source}
                <button
                  type="button"
                  className="ml-1 text-green-600 hover:text-green-800"
                  onClick={() => handleMultiSelectChange('source', source, false)}
                >
                  ×
                </button>
              </span>
            ))}
            {filters.assignee && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Assignee: {filters.assignee}
                <button
                  type="button"
                  className="ml-1 text-purple-600 hover:text-purple-800"
                  onClick={() => onFiltersChange({ assignee: '' })}
                >
                  ×
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}