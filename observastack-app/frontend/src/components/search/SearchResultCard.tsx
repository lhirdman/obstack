import React from 'react'
import { SearchItem, LogItem, MetricItem, TraceItem } from '../../types'
import { Badge } from '../ui'
import { 
  DocumentTextIcon, 
  ChartBarIcon, 
  MapIcon,
  LinkIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { format, parseISO } from 'date-fns'
import { clsx } from 'clsx'

export interface SearchResultCardProps {
  item: SearchItem
  onClick?: () => void
  onCorrelationClick?: (correlationId: string) => void
  className?: string
}

function getSourceIcon(source: SearchItem['source']) {
  switch (source) {
    case 'logs':
      return <DocumentTextIcon className="h-4 w-4" />
    case 'metrics':
      return <ChartBarIcon className="h-4 w-4" />
    case 'traces':
      return <MapIcon className="h-4 w-4" />
    default:
      return <DocumentTextIcon className="h-4 w-4" />
  }
}

function getSourceColor(source: SearchItem['source']) {
  switch (source) {
    case 'logs':
      return 'info'
    case 'metrics':
      return 'success'
    case 'traces':
      return 'warning'
    default:
      return 'default'
  }
}

function LogContent({ content }: { content: LogItem }) {
  const getLevelColor = (level: LogItem['level']) => {
    switch (level) {
      case 'error':
      case 'fatal':
        return 'error'
      case 'warn':
        return 'warning'
      case 'info':
        return 'info'
      case 'debug':
        return 'default'
      default:
        return 'default'
    }
  }

  const getLevelIcon = (level: LogItem['level']) => {
    switch (level) {
      case 'error':
      case 'fatal':
        return <XCircleIcon className="h-4 w-4" />
      case 'warn':
        return <ExclamationTriangleIcon className="h-4 w-4" />
      case 'info':
        return <CheckCircleIcon className="h-4 w-4" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Badge variant={getLevelColor(content.level)} className="gap-1">
          {getLevelIcon(content.level)}
          {content.level.toUpperCase()}
        </Badge>
      </div>
      <p className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded">
        {content.message}
      </p>
      {Object.keys(content.labels).length > 0 && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(content.labels).map(([key, value]) => (
            <Badge key={key} variant="default" size="sm">
              {key}: {value}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

function MetricContent({ content }: { content: MetricItem }) {
  const formatValue = (value: number, unit: string) => {
    if (unit === 'bytes') {
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(value) / Math.log(1024))
      return `${(value / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
    }
    if (unit === 'seconds') {
      if (value < 1) {
        return `${(value * 1000).toFixed(2)} ms`
      }
      return `${value.toFixed(2)} s`
    }
    return `${value} ${unit}`
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">{content.name}</h4>
        <span className="text-lg font-mono text-blue-600">
          {formatValue(content.value, content.unit)}
        </span>
      </div>
      <Badge variant="success" size="sm">
        {content.type}
      </Badge>
      {Object.keys(content.labels).length > 0 && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(content.labels).map(([key, value]) => (
            <Badge key={key} variant="default" size="sm">
              {key}: {value}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

function TraceContent({ content }: { content: TraceItem }) {
  const getStatusColor = (status: TraceItem['status']) => {
    switch (status) {
      case 'ok':
        return 'success'
      case 'error':
        return 'error'
      case 'timeout':
        return 'warning'
      default:
        return 'default'
    }
  }

  const formatDuration = (duration: number) => {
    if (duration < 1000) {
      return `${duration.toFixed(2)} μs`
    }
    if (duration < 1000000) {
      return `${(duration / 1000).toFixed(2)} ms`
    }
    return `${(duration / 1000000).toFixed(2)} s`
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">{content.operationName}</h4>
        <div className="flex items-center gap-2">
          <Badge variant={getStatusColor(content.status)}>
            {content.status.toUpperCase()}
          </Badge>
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <ClockIcon className="h-3 w-3" />
            {formatDuration(content.duration)}
          </span>
        </div>
      </div>
      <div className="text-xs text-gray-500 font-mono">
        Trace: {content.traceId} | Span: {content.spanId}
      </div>
      {Object.keys(content.tags).length > 0 && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(content.tags).map(([key, value]) => (
            <Badge key={key} variant="default" size="sm">
              {key}: {value}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

export function SearchResultCard({
  item,
  onClick,
  onCorrelationClick,
  className
}: SearchResultCardProps) {
  const formatTimestamp = (timestamp: string) => {
    try {
      return format(parseISO(timestamp), 'MMM d, HH:mm:ss.SSS')
    } catch {
      return timestamp
    }
  }

  const renderContent = () => {
    switch (item.source) {
      case 'logs':
        return <LogContent content={item.content as LogItem} />
      case 'metrics':
        return <MetricContent content={item.content as MetricItem} />
      case 'traces':
        return <TraceContent content={item.content as TraceItem} />
      default:
        return <div>Unknown content type</div>
    }
  }

  return (
    <div
      className={clsx(
        'p-4 hover:bg-gray-50 transition-colors cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant={getSourceColor(item.source)} className="gap-1">
              {getSourceIcon(item.source)}
              {item.source}
            </Badge>
            <span className="text-sm font-medium text-gray-700">{item.service}</span>
            {item.correlationId && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onCorrelationClick && item.correlationId && onCorrelationClick(item.correlationId)
                }}
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
              >
                <LinkIcon className="h-3 w-3" />
                Correlated
              </button>
            )}
          </div>
          <span className="text-xs text-gray-500">
            {formatTimestamp(item.timestamp)}
          </span>
        </div>

        {/* Content */}
        {renderContent()}
      </div>
    </div>
  )
}