import React from 'react'
import { SearchStats as SearchStatsType } from '../../types'
import { Badge } from '../ui'
import { ClockIcon, DocumentMagnifyingGlassIcon } from '@heroicons/react/24/outline'

export interface SearchStatsProps {
  stats: SearchStatsType
  className?: string
}

export function SearchStats({ stats, className }: SearchStatsProps) {
  const formatLatency = (latencyMs: number) => {
    if (latencyMs < 1000) {
      return `${latencyMs}ms`
    }
    return `${(latencyMs / 1000).toFixed(2)}s`
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }

  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <DocumentMagnifyingGlassIcon className="h-4 w-4" />
          <span>
            <strong>{formatNumber(stats.matched)}</strong> results
            {stats.scanned > stats.matched && (
              <span className="text-gray-500">
                {' '}from {formatNumber(stats.scanned)} scanned
              </span>
            )}
          </span>
        </div>
        
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <ClockIcon className="h-4 w-4" />
          <span>{formatLatency(stats.latencyMs)}</span>
        </div>
      </div>

      {/* Source breakdown */}
      {Object.keys(stats.sources).length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Sources:</span>
          <div className="flex gap-1">
            {Object.entries(stats.sources).map(([source, count]) => (
              <Badge key={source} variant="default" size="sm">
                {source}: {formatNumber(count)}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}