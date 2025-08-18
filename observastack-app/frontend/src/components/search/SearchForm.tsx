import React, { useState, useCallback } from 'react'
import { MagnifyingGlassIcon, AdjustmentsHorizontalIcon, ClockIcon } from '@heroicons/react/24/outline'
import { Button, Input, Select } from '../ui'
import { SearchQuery, SearchFilter, TimeRange } from '../../types'
import { TimeRangeSelector } from './TimeRangeSelector'
import { SearchFilters } from './SearchFilters'
import { clsx } from 'clsx'

export interface SearchFormProps {
  onSearch: (query: SearchQuery) => void
  loading?: boolean
  initialQuery?: Partial<SearchQuery>
  className?: string
}

const searchTypeOptions = [
  { value: 'all', label: 'All Sources' },
  { value: 'logs', label: 'Logs' },
  { value: 'metrics', label: 'Metrics' },
  { value: 'traces', label: 'Traces' }
]

export function SearchForm({
  onSearch,
  loading = false,
  initialQuery,
  className
}: SearchFormProps) {
  const [freeText, setFreeText] = useState(initialQuery?.freeText || '')
  const [type, setType] = useState<SearchQuery['type']>(initialQuery?.type || 'all')
  const [timeRange, setTimeRange] = useState<TimeRange>(
    initialQuery?.timeRange || {
      from: 'now-1h',
      to: 'now'
    }
  )
  const [filters, setFilters] = useState<SearchFilter[]>(initialQuery?.filters || [])
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    
    if (!freeText.trim()) {
      return
    }

    const query: SearchQuery = {
      freeText: freeText.trim(),
      type,
      timeRange,
      filters,
      tenantId: '', // Will be set by the API client
      limit: 100
    }

    onSearch(query)
  }, [freeText, type, timeRange, filters, onSearch])

  const handleAddFilter = useCallback((filter: SearchFilter) => {
    setFilters(prev => [...prev, filter])
  }, [])

  const handleRemoveFilter = useCallback((index: number) => {
    setFilters(prev => prev.filter((_, i) => i !== index))
  }, [])

  const handleUpdateFilter = useCallback((index: number, filter: SearchFilter) => {
    setFilters(prev => prev.map((f, i) => i === index ? filter : f))
  }, [])

  return (
    <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200 p-6', className)}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main search input */}
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder="Search logs, metrics, and traces..."
              leftIcon={<MagnifyingGlassIcon />}
              className="text-base"
            />
          </div>
          <Select
            value={type}
            onChange={(value) => setType(value as SearchQuery['type'])}
            options={searchTypeOptions}
            className="w-40"
          />
          <Button
            type="submit"
            loading={loading}
            disabled={!freeText.trim()}
            className="px-6"
          >
            Search
          </Button>
        </div>

        {/* Advanced controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <TimeRangeSelector
              value={timeRange}
              onChange={setTimeRange}
            />
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={clsx(
                'inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                showAdvanced
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <AdjustmentsHorizontalIcon className="h-4 w-4" />
              Filters
              {filters.length > 0 && (
                <span className="bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center">
                  {filters.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Advanced filters */}
        {showAdvanced && (
          <div className="border-t border-gray-200 pt-4">
            <SearchFilters
              filters={filters}
              onAddFilter={handleAddFilter}
              onRemoveFilter={handleRemoveFilter}
              onUpdateFilter={handleUpdateFilter}
            />
          </div>
        )}
      </form>
    </div>
  )
}