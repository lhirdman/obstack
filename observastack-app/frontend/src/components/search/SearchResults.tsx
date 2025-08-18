import React from 'react'
import { SearchResult, SearchItem } from '../../types'
import { Badge } from '../ui'
import { SearchResultCard } from './SearchResultCard'
import { SearchStats } from './SearchStats'
import { clsx } from 'clsx'

export interface SearchResultsProps {
  results: SearchResult
  loading?: boolean
  onResultClick?: (item: SearchItem) => void
  onCorrelationClick?: (correlationId: string) => void
  className?: string
}

export function SearchResults({
  results,
  loading = false,
  onResultClick,
  onCorrelationClick,
  className
}: SearchResultsProps) {
  if (loading) {
    return (
      <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200 p-6', className)}>
        <SearchResultsSkeleton />
      </div>
    )
  }

  if (!results.items || results.items.length === 0) {
    return (
      <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200 p-6', className)}>
        <EmptySearchResults />
      </div>
    )
  }

  return (
    <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200', className)}>
      {/* Search statistics */}
      <div className="p-4 border-b border-gray-200">
        <SearchStats stats={results.stats} />
      </div>

      {/* Results list */}
      <div className="divide-y divide-gray-200">
        {results.items.map((item, index) => (
          <SearchResultCard
            key={`${item.id}-${index}`}
            item={item}
            onClick={() => onResultClick?.(item)}
            {...(onCorrelationClick && { onCorrelationClick })}
          />
        ))}
      </div>

      {/* Load more indicator */}
      {results.nextToken && (
        <div className="p-4 border-t border-gray-200 text-center">
          <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
            Load more results
          </button>
        </div>
      )}
    </div>
  )
}

function SearchResultsSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-4 bg-gray-200 rounded w-48 animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-24 animate-pulse" />
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="space-y-3 p-4 border border-gray-200 rounded-md">
          <div className="flex items-center gap-2">
            <div className="h-5 bg-gray-200 rounded w-16 animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-32 animate-pulse" />
          </div>
          <div className="h-4 bg-gray-200 rounded w-full animate-pulse" />
          <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
        </div>
      ))}
    </div>
  )
}

function EmptySearchResults() {
  return (
    <div className="text-center py-12">
      <div className="mx-auto h-12 w-12 text-gray-400">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
      <h3 className="mt-4 text-sm font-medium text-gray-900">No results found</h3>
      <p className="mt-2 text-sm text-gray-500">
        Try adjusting your search terms or filters to find what you're looking for.
      </p>
      <div className="mt-4 space-y-2 text-sm text-gray-500">
        <p><strong>Tips:</strong></p>
        <ul className="text-left max-w-md mx-auto space-y-1">
          <li>• Use broader search terms</li>
          <li>• Check your time range</li>
          <li>• Remove some filters</li>
          <li>• Try searching across all sources</li>
        </ul>
      </div>
    </div>
  )
}