import React, { useState, useEffect } from 'react'
import { ClockIcon, BookmarkIcon, TrashIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid'
import { Button, Badge } from '../ui'
import { SearchQuery } from '../../types'
import { format, parseISO } from 'date-fns'
import { clsx } from 'clsx'

export interface SearchHistoryItem {
  id: string
  query: SearchQuery
  timestamp: string
  resultCount?: number
  saved?: boolean
  name?: string
}

export interface SearchHistoryProps {
  onSelectQuery: (query: SearchQuery) => void
  onSaveQuery?: (item: SearchHistoryItem, name: string) => void
  onDeleteQuery?: (id: string) => void
  className?: string
}

// Mock data for demonstration - in real app this would come from localStorage or API
const mockHistory: SearchHistoryItem[] = [
  {
    id: '1',
    query: {
      freeText: 'error rate',
      type: 'logs',
      timeRange: { from: 'now-1h', to: 'now' },
      filters: [{ field: 'level', operator: 'equals', value: 'error' }],
      tenantId: 'tenant1'
    },
    timestamp: '2025-08-16T07:30:00Z',
    resultCount: 42,
    saved: true,
    name: 'Error Rate Analysis'
  },
  {
    id: '2',
    query: {
      freeText: 'authentication failed',
      type: 'all',
      timeRange: { from: 'now-24h', to: 'now' },
      filters: [],
      tenantId: 'tenant1'
    },
    timestamp: '2025-08-16T06:15:00Z',
    resultCount: 15
  },
  {
    id: '3',
    query: {
      freeText: 'cpu usage',
      type: 'metrics',
      timeRange: { from: 'now-6h', to: 'now' },
      filters: [{ field: 'service', operator: 'equals', value: 'api-server' }],
      tenantId: 'tenant1'
    },
    timestamp: '2025-08-16T05:45:00Z',
    resultCount: 128
  }
]

export function SearchHistory({
  onSelectQuery,
  onSaveQuery,
  onDeleteQuery,
  className
}: SearchHistoryProps) {
  const [history, setHistory] = useState<SearchHistoryItem[]>(mockHistory)
  const [filter, setFilter] = useState<'all' | 'saved'>('all')
  const [savingId, setSavingId] = useState<string | null>(null)

  const filteredHistory = history.filter(item => 
    filter === 'all' || (filter === 'saved' && item.saved)
  )

  const handleSaveQuery = async (item: SearchHistoryItem) => {
    if (!onSaveQuery) return
    
    setSavingId(item.id)
    const name = prompt('Enter a name for this saved search:', item.query.freeText)
    
    if (name) {
      try {
        await onSaveQuery(item, name)
        setHistory(prev => prev.map(h => 
          h.id === item.id ? { ...h, saved: true, name } : h
        ))
      } catch (error) {
        console.error('Failed to save query:', error)
      }
    }
    
    setSavingId(null)
  }

  const handleDeleteQuery = async (id: string) => {
    if (!onDeleteQuery) return
    
    if (confirm('Are you sure you want to delete this search?')) {
      try {
        await onDeleteQuery(id)
        setHistory(prev => prev.filter(h => h.id !== id))
      } catch (error) {
        console.error('Failed to delete query:', error)
      }
    }
  }

  const formatTimeRange = (timeRange: SearchQuery['timeRange']) => {
    if (timeRange.from.startsWith('now')) {
      return `${timeRange.from} to ${timeRange.to}`
    }
    try {
      const from = format(parseISO(timeRange.from), 'MMM d, HH:mm')
      const to = format(parseISO(timeRange.to), 'MMM d, HH:mm')
      return `${from} - ${to}`
    } catch {
      return `${timeRange.from} to ${timeRange.to}`
    }
  }

  return (
    <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200', className)}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <ClockIcon className="h-5 w-5" />
            Search History
          </h3>
          <div className="flex border border-gray-300 rounded-md">
            <button
              onClick={() => setFilter('all')}
              className={clsx(
                'px-3 py-1 text-sm font-medium rounded-l-md transition-colors',
                filter === 'all'
                  ? 'bg-blue-100 text-blue-700 border-blue-300'
                  : 'text-gray-700 hover:bg-gray-50'
              )}
            >
              All
            </button>
            <button
              onClick={() => setFilter('saved')}
              className={clsx(
                'px-3 py-1 text-sm font-medium rounded-r-md border-l transition-colors',
                filter === 'saved'
                  ? 'bg-blue-100 text-blue-700 border-blue-300'
                  : 'text-gray-700 hover:bg-gray-50 border-gray-300'
              )}
            >
              Saved
            </button>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {filteredHistory.length === 0 ? (
          <div className="p-8 text-center">
            <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-sm font-medium text-gray-900">
              {filter === 'saved' ? 'No saved searches' : 'No search history'}
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              {filter === 'saved' 
                ? 'Save searches to quickly access them later.'
                : 'Your recent searches will appear here.'
              }
            </p>
          </div>
        ) : (
          filteredHistory.map((item) => (
            <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    {item.saved && (
                      <BookmarkSolidIcon className="h-4 w-4 text-yellow-500" />
                    )}
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {item.name || item.query.freeText}
                    </h4>
                    <Badge variant="default" size="sm">
                      {item.query.type}
                    </Badge>
                  </div>
                  
                  {item.name && (
                    <p className="text-sm text-gray-600 mb-1 font-mono">
                      {item.query.freeText}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{format(parseISO(item.timestamp), 'MMM d, HH:mm')}</span>
                    <span>{formatTimeRange(item.query.timeRange)}</span>
                    {item.resultCount !== undefined && (
                      <span>{item.resultCount} results</span>
                    )}
                    {item.query.filters.length > 0 && (
                      <span>{item.query.filters.length} filters</span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-1 ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onSelectQuery(item.query)}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <MagnifyingGlassIcon className="h-4 w-4" />
                  </Button>
                  
                  {!item.saved && onSaveQuery && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSaveQuery(item)}
                      disabled={savingId === item.id}
                      className="text-yellow-600 hover:text-yellow-700"
                    >
                      <BookmarkIcon className="h-4 w-4" />
                    </Button>
                  )}
                  
                  {onDeleteQuery && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteQuery(item.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}