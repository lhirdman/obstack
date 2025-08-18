import { useState, useCallback, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { SearchQuery, SearchResult, SearchItem } from '../types'
import { useApiClient } from './useApiClient'
import { SearchHistoryItem } from '../components/search/SearchHistory'

export interface SearchState {
  results: SearchResult | null
  loading: boolean
  error: Error | null
  query: SearchQuery | null
}

export interface UseSearchOptions {
  enableHistory?: boolean
  enableAutoSearch?: boolean
  debounceMs?: number
}

export function useSearch(options: UseSearchOptions = {}) {
  const {
    enableHistory = true,
    enableAutoSearch = false,
    debounceMs = 300
  } = options

  const apiClient = useApiClient()
  const queryClient = useQueryClient()
  const debounceRef = useRef<NodeJS.Timeout | null>(null)
  
  const [state, setState] = useState<SearchState>({
    results: null,
    loading: false,
    error: null,
    query: null
  })

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: async (query: SearchQuery): Promise<SearchResult> => {
      const response = await apiClient.post<SearchResult>('/search', query)
      return response
    },
    onMutate: (query) => {
      setState(prev => ({
        ...prev,
        loading: true,
        error: null,
        query
      }))
    },
    onSuccess: (results, query) => {
      setState(prev => ({
        ...prev,
        results,
        loading: false,
        error: null
      }))

      // Add to search history
      if (enableHistory) {
        addToHistory(query, results)
      }
    },
    onError: (error: Error) => {
      setState(prev => ({
        ...prev,
        loading: false,
        error
      }))
    }
  })

  // Search function with debouncing
  const search = useCallback((query: SearchQuery, immediate = false) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    const executeSearch = () => {
      searchMutation.mutate(query)
    }

    if (immediate || !enableAutoSearch) {
      executeSearch()
    } else {
      debounceRef.current = setTimeout(executeSearch, debounceMs)
    }
  }, [searchMutation, enableAutoSearch, debounceMs])

  // Search history management
  const getSearchHistory = useCallback((): SearchHistoryItem[] => {
    if (!enableHistory) return []
    
    try {
      const history = localStorage.getItem('observastack-search-history')
      return history ? JSON.parse(history) : []
    } catch {
      return []
    }
  }, [enableHistory])

  const addToHistory = useCallback((query: SearchQuery, results: SearchResult) => {
    if (!enableHistory) return

    try {
      const history = getSearchHistory()
      const newItem: SearchHistoryItem = {
        id: Date.now().toString(),
        query,
        timestamp: new Date().toISOString(),
        resultCount: results.items.length
      }

      // Remove duplicate queries and limit history size
      const filteredHistory = history
        .filter(item => 
          item.query.freeText !== query.freeText || 
          item.query.type !== query.type
        )
        .slice(0, 49) // Keep last 49 items + new one = 50 total

      const updatedHistory = [newItem, ...filteredHistory]
      localStorage.setItem('observastack-search-history', JSON.stringify(updatedHistory))
    } catch (error) {
      console.error('Failed to save search history:', error)
    }
  }, [enableHistory, getSearchHistory])

  const saveSearch = useCallback((item: SearchHistoryItem, name: string) => {
    if (!enableHistory) return

    try {
      const history = getSearchHistory()
      const updatedHistory = history.map(h => 
        h.id === item.id ? { ...h, saved: true, name } : h
      )
      localStorage.setItem('observastack-search-history', JSON.stringify(updatedHistory))
    } catch (error) {
      console.error('Failed to save search:', error)
      throw error
    }
  }, [enableHistory, getSearchHistory])

  const deleteFromHistory = useCallback((id: string) => {
    if (!enableHistory) return

    try {
      const history = getSearchHistory()
      const updatedHistory = history.filter(h => h.id !== id)
      localStorage.setItem('observastack-search-history', JSON.stringify(updatedHistory))
    } catch (error) {
      console.error('Failed to delete from history:', error)
      throw error
    }
  }, [enableHistory, getSearchHistory])

  // Clear search results
  const clearResults = useCallback(() => {
    setState(prev => ({
      ...prev,
      results: null,
      error: null,
      query: null
    }))
  }, [])

  // Cancel ongoing search
  const cancelSearch = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    searchMutation.reset()
    setState(prev => ({
      ...prev,
      loading: false
    }))
  }, [searchMutation])

  return {
    // State
    ...state,
    
    // Actions
    search,
    clearResults,
    cancelSearch,
    
    // History management
    getSearchHistory,
    saveSearch,
    deleteFromHistory,
    
    // Utilities
    isSearching: searchMutation.isPending
  }
}

// Hook for cross-signal navigation
export function useCrossSignalNavigation() {
  const apiClient = useApiClient()

  const navigateToCorrelatedData = useCallback(async (
    correlationId: string,
    targetType: 'logs' | 'metrics' | 'traces'
  ) => {
    try {
      const query: SearchQuery = {
        freeText: correlationId,
        type: targetType,
        timeRange: { from: 'now-1h', to: 'now' },
        filters: [
          { field: 'correlation_id', operator: 'equals', value: correlationId }
        ],
        tenantId: '' // Will be set by API client
      }

      const results = await apiClient.post<SearchResult>('/search', query)
      return results
    } catch (error) {
      console.error('Failed to navigate to correlated data:', error)
      throw error
    }
  }, [apiClient])

  const findRelatedTraces = useCallback(async (logItem: SearchItem) => {
    // Extract trace ID from log content or labels
    const logContent = logItem.content as any
    const traceId = logContent.labels?.trace_id || logContent.fields?.trace_id
    
    if (!traceId) {
      throw new Error('No trace ID found in log item')
    }

    return navigateToCorrelatedData(traceId, 'traces')
  }, [navigateToCorrelatedData])

  const findRelatedLogs = useCallback(async (traceItem: SearchItem) => {
    const traceContent = traceItem.content as any
    const traceId = traceContent.traceId
    
    if (!traceId) {
      throw new Error('No trace ID found in trace item')
    }

    return navigateToCorrelatedData(traceId, 'logs')
  }, [navigateToCorrelatedData])

  return {
    navigateToCorrelatedData,
    findRelatedTraces,
    findRelatedLogs
  }
}