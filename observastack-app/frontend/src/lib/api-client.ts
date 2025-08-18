// API client utilities with error handling

import {
  ApiError,
  ObservaStackError,
  AuthenticationError,
  AuthorizationError,
  ValidationError,
  NetworkError,
  TimeoutError,
  ServiceUnavailableError,
  RateLimitError,
  HTTP_STATUS_CODES
} from '../types/errors'

export interface ApiClientConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
  retryDelay: number
}

export const defaultConfig: ApiClientConfig = {
  baseUrl: '/api',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000
}

export class ApiClient {
  private config: ApiClientConfig
  private abortController: AbortController | null = null
  private authToken: string | null = null

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type')
    const isJson = contentType?.includes('application/json')

    let data: any
    try {
      data = isJson ? await response.json() : await response.text()
    } catch (error) {
      throw new NetworkError('Failed to parse response', {
        status: response.status,
        statusText: response.statusText
      })
    }

    if (!response.ok) {
      // Handle structured error responses
      if (isJson && data.error) {
        const apiError: ApiError = data
        throw ObservaStackError.fromApiError(apiError)
      }

      // Handle HTTP status codes
      switch (response.status) {
        case HTTP_STATUS_CODES.UNAUTHORIZED:
          throw new AuthenticationError('Authentication required')
        case HTTP_STATUS_CODES.FORBIDDEN:
          throw new AuthorizationError('Access denied')
        case HTTP_STATUS_CODES.UNPROCESSABLE_ENTITY:
          throw new ValidationError('Validation failed', data.validationErrors || [])
        case HTTP_STATUS_CODES.TOO_MANY_REQUESTS:
          const retryAfter = response.headers.get('Retry-After')
          throw new RateLimitError(
            'Rate limit exceeded',
            retryAfter ? parseInt(retryAfter) : undefined
          )
        case HTTP_STATUS_CODES.SERVICE_UNAVAILABLE:
          throw new ServiceUnavailableError('Service temporarily unavailable')
        default:
          throw new ObservaStackError(
            data.message || response.statusText || 'Request failed',
            'HTTP_ERROR',
            { status: response.status, statusText: response.statusText }
          )
      }
    }

    return data
  }

  private async makeRequest<T>(
    url: string,
    options: RequestInit = {},
    attempt: number = 1
  ): Promise<T> {
    this.abortController = new AbortController()
    
    const timeoutId = setTimeout(() => {
      this.abortController?.abort()
    }, this.config.timeout)

    // Prepare headers with authentication
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>
    }

    // Add authorization header if token is available
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`
    }

    try {
      const response = await fetch(`${this.config.baseUrl}${url}`, {
        ...options,
        signal: this.abortController.signal,
        headers
      })

      clearTimeout(timeoutId)
      return await this.handleResponse<T>(response)
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof ObservaStackError) {
        throw error
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new TimeoutError('Request timed out')
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        // Network error
        if (attempt < this.config.retryAttempts) {
          await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * attempt))
          return this.makeRequest<T>(url, options, attempt + 1)
        }
        throw new NetworkError('Network request failed')
      }

      throw new ObservaStackError(
        error instanceof Error ? error.message : 'Unknown error occurred',
        'UNKNOWN_ERROR'
      )
    }
  }

  async get<T>(url: string, options: RequestInit = {}): Promise<T> {
    return this.makeRequest<T>(url, { ...options, method: 'GET' })
  }

  async post<T>(url: string, data?: any, options: RequestInit = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : null
    })
  }

  async put<T>(url: string, data?: any, options: RequestInit = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : null
    })
  }

  async patch<T>(url: string, data?: any, options: RequestInit = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : null
    })
  }

  async delete<T>(url: string, options: RequestInit = {}): Promise<T> {
    return this.makeRequest<T>(url, { ...options, method: 'DELETE' })
  }

  abort(): void {
    this.abortController?.abort()
  }

  setAuthToken(token: string | null): void {
    this.authToken = token
  }

  getAuthToken(): string | null {
    return this.authToken
  }

  clearAuthToken(): void {
    this.authToken = null
  }
}

// Default API client instance
export const apiClient = new ApiClient()

// Utility functions for common API patterns
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error
      
      // Don't retry on certain error types
      if (
        error instanceof AuthenticationError ||
        error instanceof AuthorizationError ||
        error instanceof ValidationError
      ) {
        throw error
      }

      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delay * attempt))
      }
    }
  }

  throw lastError!
}

export function isRetryableError(error: unknown): boolean {
  return (
    error instanceof NetworkError ||
    error instanceof TimeoutError ||
    error instanceof ServiceUnavailableError ||
    (error instanceof ObservaStackError && error.code === 'EXTERNAL_SERVICE_ERROR')
  )
}