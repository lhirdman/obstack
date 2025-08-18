/**
 * Custom hook for alert management
 */

import { useState, useEffect, useCallback } from 'react'
import { alertService } from '../services/alert-service'
import type {
  Alert,
  AlertQuery,
  AlertsResponse,
  AlertActionRequest,
  AlertStatistics,
  AlertFilters,
  AlertSortConfig
} from '../types/alerts'

export interface UseAlertsOptions {
  initialQuery?: AlertQuery
  autoRefresh?: boolean
  refreshInterval?: number
}

export interface UseAlertsResult {
  alerts: Alert[]
  total: number
  loading: boolean
  error: string | null
  statistics: AlertStatistics | null
  
  // Actions
  refetch: () => Promise<void>
  performAction: (request: AlertActionRequest) => Promise<void>
  updateQuery: (query: Partial<AlertQuery>) => void
  
  // Current state
  query: AlertQuery
}

export function useAlerts(options: UseAlertsOptions = {}): UseAlertsResult {
  const {
    initialQuery = {},
    autoRefresh = false,
    refreshInterval = 30000 // 30 seconds
  } = options

  const [alerts, setAlerts] = useState<Alert[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statistics, setStatistics] = useState<AlertStatistics | null>(null)
  const [query, setQuery] = useState<AlertQuery>(initialQuery)

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await alertService.getAlerts(query)
      setAlerts(response.alerts)
      setTotal(response.total)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch alerts'
      setError(errorMessage)
      console.error('Failed to fetch alerts:', err)
    } finally {
      setLoading(false)
    }
  }, [query])

  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await alertService.getStatistics()
      setStatistics(stats)
    } catch (err) {
      console.error('Failed to fetch alert statistics:', err)
    }
  }, [])

  const performAction = useCallback(async (request: AlertActionRequest) => {
    try {
      setError(null)
      await alertService.performAction(request)
      
      // Refresh alerts after action
      await fetchAlerts()
      await fetchStatistics()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to perform action'
      setError(errorMessage)
      throw err
    }
  }, [fetchAlerts, fetchStatistics])

  const updateQuery = useCallback((newQuery: Partial<AlertQuery>) => {
    setQuery(prev => ({ ...prev, ...newQuery }))
  }, [])

  const refetch = useCallback(async () => {
    await Promise.all([fetchAlerts(), fetchStatistics()])
  }, [fetchAlerts, fetchStatistics])

  // Initial fetch
  useEffect(() => {
    refetch()
  }, [refetch])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      refetch()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refetch])

  // Refetch when query changes
  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  return {
    alerts,
    total,
    loading,
    error,
    statistics,
    refetch,
    performAction,
    updateQuery,
    query
  }
}

export interface UseAlertFiltersResult {
  filters: AlertFilters
  updateFilters: (updates: Partial<AlertFilters>) => void
  clearFilters: () => void
  hasActiveFilters: boolean
}

export function useAlertFilters(initialFilters?: Partial<AlertFilters>): UseAlertFiltersResult {
  const defaultFilters: AlertFilters = {
    status: [],
    severity: [],
    source: [],
    assignee: '',
    timeRange: {
      from: 'now-24h',
      to: 'now'
    },
    searchText: ''
  }

  const [filters, setFilters] = useState<AlertFilters>({
    ...defaultFilters,
    ...initialFilters
  })

  const updateFilters = useCallback((updates: Partial<AlertFilters>) => {
    setFilters(prev => ({ ...prev, ...updates }))
  }, [])

  const clearFilters = useCallback(() => {
    setFilters(defaultFilters)
  }, [])

  const hasActiveFilters = 
    filters.status.length > 0 ||
    filters.severity.length > 0 ||
    filters.source.length > 0 ||
    filters.assignee !== '' ||
    filters.searchText !== '' ||
    filters.timeRange.from !== 'now-24h' ||
    filters.timeRange.to !== 'now'

  return {
    filters,
    updateFilters,
    clearFilters,
    hasActiveFilters
  }
}

export interface UseAlertSortResult {
  sort: AlertSortConfig
  updateSort: (field: AlertSortConfig['field']) => void
}

export function useAlertSort(initialSort?: AlertSortConfig): UseAlertSortResult {
  const [sort, setSort] = useState<AlertSortConfig>(
    initialSort || { field: 'timestamp', direction: 'desc' }
  )

  const updateSort = useCallback((field: AlertSortConfig['field']) => {
    setSort(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }))
  }, [])

  return {
    sort,
    updateSort
  }
}