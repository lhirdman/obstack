/**
 * Individual alert card component
 */

import React from 'react'
import { clsx } from 'clsx'
import { Badge } from '../ui'
import type { Alert } from '../../types/alerts'
import { SEVERITY_COLORS, STATUS_COLORS, SEVERITY_ICONS, STATUS_ICONS } from '../../types/alerts'

export interface AlertCardProps {
  alert: Alert
  selected?: boolean
  onSelect?: (selected: boolean) => void
  onClick?: () => void
  className?: string
}

export function AlertCard({
  alert,
  selected = false,
  onSelect,
  onClick,
  className
}: AlertCardProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleDateString()
  }

  const getDuration = () => {
    if (!alert.endsAt) return null
    
    const start = new Date(alert.startsAt)
    const end = new Date(alert.endsAt)
    const durationMs = end.getTime() - start.getTime()
    const durationMins = Math.floor(durationMs / (1000 * 60))
    const durationHours = Math.floor(durationMins / 60)
    
    if (durationMins < 60) return `${durationMins}m`
    return `${durationHours}h ${durationMins % 60}m`
  }

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger card click if clicking on checkbox
    if ((e.target as HTMLInputElement).type === 'checkbox') return
    onClick?.()
  }

  const handleSelectChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation()
    onSelect?.(e.target.checked)
  }

  return (
    <div
      className={clsx(
        'p-4 hover:bg-gray-50 cursor-pointer transition-colors',
        selected && 'bg-blue-50 border-l-4 border-l-blue-500',
        className
      )}
      onClick={handleCardClick}
    >
      <div className="flex items-start space-x-3">
        {/* Selection checkbox */}
        {onSelect && (
          <div className="flex items-center pt-1">
            <input
              type="checkbox"
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={selected}
              onChange={handleSelectChange}
            />
          </div>
        )}

        {/* Alert content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {/* Title and badges */}
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="text-sm font-medium text-gray-900 truncate">
                  {alert.title}
                </h3>
                <Badge
                  variant={SEVERITY_COLORS[alert.severity]}
                  size="sm"
                >
                  {SEVERITY_ICONS[alert.severity]} {alert.severity.toUpperCase()}
                </Badge>
                <Badge
                  variant={STATUS_COLORS[alert.status]}
                  size="sm"
                >
                  {STATUS_ICONS[alert.status]} {alert.status.toUpperCase()}
                </Badge>
              </div>

              {/* Description */}
              {alert.description && (
                <p className="text-sm text-gray-600 mb-2" style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  {alert.description}
                </p>
              )}

              {/* Labels */}
              {Object.keys(alert.labels).length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {Object.entries(alert.labels).slice(0, 3).map(([key, value]) => (
                    <span
                      key={key}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {key}: {value}
                    </span>
                  ))}
                  {Object.keys(alert.labels).length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{Object.keys(alert.labels).length - 3} more
                    </span>
                  )}
                </div>
              )}

              {/* Metadata */}
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>Source: {alert.source}</span>
                <span>Started: {formatTimestamp(alert.startsAt)}</span>
                {alert.endsAt && (
                  <span>Duration: {getDuration()}</span>
                )}
                {alert.assignee && (
                  <span>Assigned to: {alert.assignee}</span>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2 ml-4">
              {alert.generatorUrl && (
                <a
                  href={alert.generatorUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-xs"
                  onClick={(e) => e.stopPropagation()}
                >
                  View Source
                </a>
              )}
              
              {alert.silenceId && (
                <Badge variant="default" size="sm">
                  Silenced
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}