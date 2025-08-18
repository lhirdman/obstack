/**
 * Alert list component with filtering, sorting, and bulk actions
 */

import React, { useState, useMemo } from 'react'
import { clsx } from 'clsx'
import { Button, Badge, Input } from '../ui'
import { AlertCard } from './AlertCard'
import { AlertFilters } from './AlertFilters'
import { AlertActionModal } from './AlertActionModal'
import { useAlerts, useAlertFilters, useAlertSort } from '../../hooks/useAlerts'
import type { Alert, AlertActionRequest } from '../../types/alerts'
import { SEVERITY_COLORS, STATUS_COLORS } from '../../types/alerts'

export interface AlertListProps {
  className?: string
  onAlertClick?: (alert: Alert) => void
  autoRefresh?: boolean
  refreshInterval?: number
}

export function AlertList({
  className,
  onAlertClick,
  autoRefresh = true,
  refreshInterval = 30000
}: AlertListProps) {
  const [selectedAlerts, setSelectedAlerts] = useState<Set<string>>(new Set())
  const [actionModal, setActionModal] = useState<{
    isOpen: boolean
    action: 'acknowledge' | 'resolve' | 'assign' | 'silence'
  }>({ isOpen: false, action: 'acknowledge' })

  const { filters, updateFilters, clearFilters, hasActiveFilters } = useAlertFilters()
  const { sort, updateSort } = useAlertSort()

  // Convert filters to query format
  const query = useMemo(() => {
    const result: any = {
      sortBy: sort.field,
      sortOrder: sort.direction,
      limit: 50,
      offset: 0
    }
    
    if (filters.status.length > 0) result.status = filters.status
    if (filters.severity.length > 0) result.severity = filters.severity
    if (filters.source.length > 0) result.source = filters.source
    if (filters.assignee) result.assignee = filters.assignee
    if (filters.timeRange.from !== 'now-24h') result.fromTime = filters.timeRange.from
    if (filters.timeRange.to !== 'now') result.toTime = filters.timeRange.to
    
    return result
  }, [filters, sort])

  const {
    alerts,
    total,
    loading,
    error,
    statistics,
    refetch,
    performAction
  } = useAlerts({
    initialQuery: query,
    autoRefresh,
    refreshInterval
  })

  // Filter alerts by search text (client-side)
  const filteredAlerts = useMemo(() => {
    if (!filters.searchText) return alerts

    const searchLower = filters.searchText.toLowerCase()
    return alerts.filter(alert =>
      alert.title.toLowerCase().includes(searchLower) ||
      alert.description.toLowerCase().includes(searchLower) ||
      Object.values(alert.labels).some(value => 
        value.toLowerCase().includes(searchLower)
      )
    )
  }, [alerts, filters.searchText])

  const handleSelectAlert = (alertId: string, selected: boolean) => {
    setSelectedAlerts(prev => {
      const newSet = new Set(prev)
      if (selected) {
        newSet.add(alertId)
      } else {
        newSet.delete(alertId)
      }
      return newSet
    })
  }

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedAlerts(new Set(filteredAlerts.map(alert => alert.id)))
    } else {
      setSelectedAlerts(new Set())
    }
  }

  const handleBulkAction = (action: typeof actionModal.action) => {
    if (selectedAlerts.size === 0) return
    setActionModal({ isOpen: true, action })
  }

  const handleActionConfirm = async (request: AlertActionRequest) => {
    try {
      await performAction(request)
      setSelectedAlerts(new Set())
      setActionModal({ isOpen: false, action: 'acknowledge' })
    } catch (error) {
      // Error is handled by the hook
      console.error('Action failed:', error)
    }
  }

  const selectedAlertsArray = filteredAlerts.filter(alert => 
    selectedAlerts.has(alert.id)
  )

  const allSelected = filteredAlerts.length > 0 && selectedAlerts.size === filteredAlerts.length
  const someSelected = selectedAlerts.size > 0 && selectedAlerts.size < filteredAlerts.length

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header with statistics */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Alerts</h2>
          {statistics && (
            <div className="flex items-center space-x-4 mt-2">
              <Badge variant="error" size="sm">
                {statistics.byStatus.active || 0} Active
              </Badge>
              <Badge variant="warning" size="sm">
                {statistics.byStatus.acknowledged || 0} Acknowledged
              </Badge>
              <Badge variant="success" size="sm">
                {statistics.byStatus.resolved || 0} Resolved
              </Badge>
              <span className="text-sm text-gray-500">
                Total: {statistics.total}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
          {autoRefresh && (
            <Badge variant="info" size="sm">
              Auto-refresh: {refreshInterval / 1000}s
            </Badge>
          )}
        </div>
      </div>

      {/* Filters */}
      <AlertFilters
        filters={filters}
        onFiltersChange={updateFilters}
        onClearFilters={clearFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Bulk actions */}
      {selectedAlerts.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedAlerts.size} alert{selectedAlerts.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction('acknowledge')}
              >
                Acknowledge
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction('resolve')}
              >
                Resolve
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction('assign')}
              >
                Assign
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction('silence')}
              >
                Silence
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedAlerts(new Set())}
              >
                Clear
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Alert list header */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-4 py-3 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                checked={allSelected}
                ref={input => {
                  if (input) input.indeterminate = someSelected
                }}
                onChange={(e) => handleSelectAll(e.target.checked)}
              />
              <span className="ml-2 text-sm text-gray-700">
                Select all
              </span>
            </label>
            
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Sort by:</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => updateSort('timestamp')}
                className={clsx(
                  sort.field === 'timestamp' && 'bg-gray-100'
                )}
              >
                Time {sort.field === 'timestamp' && (sort.direction === 'desc' ? '↓' : '↑')}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => updateSort('severity')}
                className={clsx(
                  sort.field === 'severity' && 'bg-gray-100'
                )}
              >
                Severity {sort.field === 'severity' && (sort.direction === 'desc' ? '↓' : '↑')}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => updateSort('status')}
                className={clsx(
                  sort.field === 'status' && 'bg-gray-100'
                )}
              >
                Status {sort.field === 'status' && (sort.direction === 'desc' ? '↓' : '↑')}
              </Button>
            </div>
          </div>
        </div>

        {/* Alert list content */}
        <div className="divide-y divide-gray-200">
          {error && (
            <div className="p-4 bg-red-50 border-l-4 border-red-400">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {loading && filteredAlerts.length === 0 && (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-500">Loading alerts...</p>
            </div>
          )}

          {!loading && filteredAlerts.length === 0 && !error && (
            <div className="p-8 text-center">
              <p className="text-gray-500">
                {hasActiveFilters ? 'No alerts match your filters' : 'No alerts found'}
              </p>
              {hasActiveFilters && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearFilters}
                  className="mt-2"
                >
                  Clear filters
                </Button>
              )}
            </div>
          )}

          {filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              selected={selectedAlerts.has(alert.id)}
              onSelect={(selected) => handleSelectAlert(alert.id, selected)}
              onClick={() => onAlertClick?.(alert)}
            />
          ))}
        </div>

        {/* Pagination info */}
        {filteredAlerts.length > 0 && (
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-700">
                Showing {filteredAlerts.length} of {total} alerts
              </p>
              {filteredAlerts.length < total && (
                <Button variant="outline" size="sm">
                  Load more
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action modal */}
      <AlertActionModal
        alerts={selectedAlertsArray}
        action={actionModal.action}
        isOpen={actionModal.isOpen}
        onClose={() => setActionModal({ isOpen: false, action: 'acknowledge' })}
        onConfirm={handleActionConfirm}
      />
    </div>
  )
}