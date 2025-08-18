/**
 * Hook for authenticated API client
 */

import { useEffect, useMemo } from 'react'
import { ApiClient } from '../lib/api-client'
import { useAuth } from '../auth'

/**
 * Hook that provides an authenticated API client
 */
export function useApiClient(): ApiClient {
  const { token, isAuthenticated } = useAuth()

  const apiClient = useMemo(() => {
    return new ApiClient({
      baseUrl: '/api',
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 1000
    })
  }, [])

  // Update auth token when it changes
  useEffect(() => {
    if (isAuthenticated && token) {
      apiClient.setAuthToken(token)
    } else {
      apiClient.clearAuthToken()
    }
  }, [apiClient, token, isAuthenticated])

  return apiClient
}

/**
 * Hook for making authenticated API requests with automatic retry
 */
export function useAuthenticatedRequest() {
  const apiClient = useApiClient()
  const { refreshAuth, isAuthenticated } = useAuth()

  const makeRequest = async <T>(
    requestFn: (client: ApiClient) => Promise<T>,
    retryOnAuth = true
  ): Promise<T> => {
    try {
      return await requestFn(apiClient)
    } catch (error: any) {
      // If we get a 401 and retry is enabled, try to refresh the token
      if (retryOnAuth && error?.status === 401 && isAuthenticated) {
        try {
          await refreshAuth()
          return await requestFn(apiClient)
        } catch (refreshError) {
          // If refresh fails, re-throw the original error
          throw error
        }
      }
      throw error
    }
  }

  return { makeRequest, apiClient }
}