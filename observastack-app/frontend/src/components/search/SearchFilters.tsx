import React, { useState } from 'react'
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { Button, Input, Select } from '../ui'
import { SearchFilter } from '../../types'
import { clsx } from 'clsx'

export interface SearchFiltersProps {
  filters: SearchFilter[]
  onAddFilter: (filter: SearchFilter) => void
  onRemoveFilter: (index: number) => void
  onUpdateFilter: (index: number, filter: SearchFilter) => void
  className?: string
}

const operatorOptions = [
  { value: 'equals', label: 'Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'regex', label: 'Regex' },
  { value: 'range', label: 'Range' },
  { value: 'exists', label: 'Exists' }
]

const commonFields = [
  { value: 'service', label: 'Service' },
  { value: 'level', label: 'Log Level' },
  { value: 'status', label: 'Status' },
  { value: 'method', label: 'HTTP Method' },
  { value: 'path', label: 'Path' },
  { value: 'user_id', label: 'User ID' },
  { value: 'trace_id', label: 'Trace ID' },
  { value: 'span_id', label: 'Span ID' },
  { value: 'error', label: 'Error' },
  { value: 'duration', label: 'Duration' }
]

interface FilterRowProps {
  filter: SearchFilter
  onUpdate: (filter: SearchFilter) => void
  onRemove: () => void
}

function FilterRow({ filter, onUpdate, onRemove }: FilterRowProps) {
  const handleFieldChange = (field: string) => {
    onUpdate({ ...filter, field })
  }

  const handleOperatorChange = (operator: SearchFilter['operator']) => {
    onUpdate({ ...filter, operator })
  }

  const handleValueChange = (value: string) => {
    // Handle range values
    if (filter.operator === 'range') {
      const parts = value.split(',').map(p => parseFloat(p.trim())).filter(n => !isNaN(n))
      if (parts.length === 2 && parts[0] !== undefined && parts[1] !== undefined) {
        onUpdate({ ...filter, value: [parts[0], parts[1]] })
      }
    } else {
      onUpdate({ ...filter, value })
    }
  }

  const getValuePlaceholder = () => {
    switch (filter.operator) {
      case 'equals':
        return 'Enter exact value'
      case 'contains':
        return 'Enter text to search for'
      case 'regex':
        return 'Enter regular expression'
      case 'range':
        return 'Enter min,max (e.g., 100,500)'
      case 'exists':
        return 'Leave empty to check existence'
      default:
        return 'Enter value'
    }
  }

  const formatValue = () => {
    if (filter.operator === 'range' && Array.isArray(filter.value)) {
      return filter.value.join(',')
    }
    return String(filter.value || '')
  }

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
      <Select
        value={filter.field}
        onChange={handleFieldChange}
        options={commonFields}
        placeholder="Select field"
        className="w-40"
      />
      <Select
        value={filter.operator}
        onChange={(value) => handleOperatorChange(value as SearchFilter['operator'])}
        options={operatorOptions}
        className="w-32"
      />
      {filter.operator !== 'exists' && (
        <Input
          value={formatValue()}
          onChange={(e) => handleValueChange(e.target.value)}
          placeholder={getValuePlaceholder()}
          className="flex-1"
        />
      )}
      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="text-red-600 hover:text-red-700 hover:bg-red-50"
      >
        <XMarkIcon className="h-4 w-4" />
      </Button>
    </div>
  )
}

export function SearchFilters({
  filters,
  onAddFilter,
  onRemoveFilter,
  onUpdateFilter,
  className
}: SearchFiltersProps) {
  const [newFilter, setNewFilter] = useState<Partial<SearchFilter>>({
    field: '',
    operator: 'equals',
    value: ''
  })

  const handleAddFilter = () => {
    if (newFilter.field && newFilter.operator) {
      onAddFilter({
        field: newFilter.field,
        operator: newFilter.operator,
        value: newFilter.value || ''
      })
      setNewFilter({
        field: '',
        operator: 'equals',
        value: ''
      })
    }
  }

  return (
    <div className={clsx('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Search Filters</h3>
        {filters.length > 0 && (
          <span className="text-xs text-gray-500">
            {filters.length} filter{filters.length !== 1 ? 's' : ''} applied
          </span>
        )}
      </div>

      {/* Existing filters */}
      {filters.length > 0 && (
        <div className="space-y-2">
          {filters.map((filter, index) => (
            <FilterRow
              key={index}
              filter={filter}
              onUpdate={(updatedFilter) => onUpdateFilter(index, updatedFilter)}
              onRemove={() => onRemoveFilter(index)}
            />
          ))}
        </div>
      )}

      {/* Add new filter */}
      <div className="flex items-center gap-3 p-3 border-2 border-dashed border-gray-300 rounded-md">
        <Select
          value={newFilter.field || ''}
          onChange={(field) => setNewFilter(prev => ({ ...prev, field }))}
          options={commonFields}
          placeholder="Select field"
          className="w-40"
        />
        <Select
          value={newFilter.operator || 'equals'}
          onChange={(operator) => setNewFilter(prev => ({ ...prev, operator: operator as SearchFilter['operator'] }))}
          options={operatorOptions}
          className="w-32"
        />
        {newFilter.operator !== 'exists' && (
          <Input
            value={String(newFilter.value || '')}
            onChange={(e) => setNewFilter(prev => ({ ...prev, value: e.target.value }))}
            placeholder="Enter value"
            className="flex-1"
          />
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={handleAddFilter}
          disabled={!newFilter.field}
          className="gap-1"
        >
          <PlusIcon className="h-4 w-4" />
          Add
        </Button>
      </div>

      {filters.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">
          No filters applied. Add filters to refine your search results.
        </p>
      )}
    </div>
  )
}