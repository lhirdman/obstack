// Error handling types for ObservaStack frontend

export interface ApiError {
  error: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
  requestId: string
}

export interface ValidationError {
  field: string
  message: string
  code: string
}

export interface ErrorResponse {
  error: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
  requestId: string
  validationErrors?: ValidationError[]
}

export class ObservaStackError extends Error {
  public readonly code: string
  public readonly details?: Record<string, unknown>
  public readonly requestId?: string
  public readonly timestamp: string

  constructor(
    message: string,
    code: string = 'UNKNOWN_ERROR',
    details?: Record<string, unknown>,
    requestId?: string
  ) {
    super(message)
    this.name = 'ObservaStackError'
    this.code = code
    this.details = details || {}
    this.requestId = requestId || ''
    this.timestamp = new Date().toISOString()
  }

  static fromApiError(apiError: ApiError): ObservaStackError {
    return new ObservaStackError(
      apiError.message,
      apiError.error,
      apiError.details,
      apiError.requestId
    )
  }
}

export class AuthenticationError extends ObservaStackError {
  constructor(message: string = 'Authentication failed', details?: Record<string, unknown>) {
    super(message, 'AUTHENTICATION_ERROR', details)
    this.name = 'AuthenticationError'
  }
}

export class AuthorizationError extends ObservaStackError {
  constructor(message: string = 'Access denied', details?: Record<string, unknown>) {
    super(message, 'AUTHORIZATION_ERROR', details)
    this.name = 'AuthorizationError'
  }
}

export class ValidationError extends ObservaStackError {
  public readonly validationErrors: ValidationError[]

  constructor(
    message: string = 'Validation failed',
    validationErrors: ValidationError[] = [],
    details?: Record<string, unknown>
  ) {
    super(message, 'VALIDATION_ERROR', details)
    this.name = 'ValidationError'
    this.validationErrors = validationErrors
  }
}

export class NetworkError extends ObservaStackError {
  constructor(message: string = 'Network error occurred', details?: Record<string, unknown>) {
    super(message, 'NETWORK_ERROR', details)
    this.name = 'NetworkError'
  }
}

export class TimeoutError extends ObservaStackError {
  constructor(message: string = 'Request timed out', details?: Record<string, unknown>) {
    super(message, 'TIMEOUT_ERROR', details)
    this.name = 'TimeoutError'
  }
}

export class ServiceUnavailableError extends ObservaStackError {
  constructor(message: string = 'Service temporarily unavailable', details?: Record<string, unknown>) {
    super(message, 'SERVICE_UNAVAILABLE', details)
    this.name = 'ServiceUnavailableError'
  }
}

export class RateLimitError extends ObservaStackError {
  public readonly retryAfter?: number

  constructor(
    message: string = 'Rate limit exceeded',
    retryAfter?: number,
    details?: Record<string, unknown>
  ) {
    super(message, 'RATE_LIMIT_ERROR', details)
    this.name = 'RateLimitError'
    this.retryAfter = retryAfter || 0
  }
}

export class TenantError extends ObservaStackError {
  constructor(message: string = 'Tenant access error', details?: Record<string, unknown>) {
    super(message, 'TENANT_ERROR', details)
    this.name = 'TenantError'
  }
}

export class SearchError extends ObservaStackError {
  constructor(message: string = 'Search operation failed', details?: Record<string, unknown>) {
    super(message, 'SEARCH_ERROR', details)
    this.name = 'SearchError'
  }
}

export class AlertError extends ObservaStackError {
  constructor(message: string = 'Alert operation failed', details?: Record<string, unknown>) {
    super(message, 'ALERT_ERROR', details)
    this.name = 'AlertError'
  }
}

export class InsightsError extends ObservaStackError {
  constructor(message: string = 'Insights operation failed', details?: Record<string, unknown>) {
    super(message, 'INSIGHTS_ERROR', details)
    this.name = 'InsightsError'
  }
}

// Error boundary state
export interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: {
    componentStack: string
  }
}

// Error context for React error boundaries
export interface ErrorContextValue {
  error?: ObservaStackError
  clearError: () => void
  reportError: (error: ObservaStackError) => void
}

// HTTP status code mappings
export const HTTP_STATUS_CODES = {
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const

// Error code mappings
export const ERROR_CODES = {
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  RATE_LIMIT_ERROR: 'RATE_LIMIT_ERROR',
  TENANT_ERROR: 'TENANT_ERROR',
  SEARCH_ERROR: 'SEARCH_ERROR',
  ALERT_ERROR: 'ALERT_ERROR',
  INSIGHTS_ERROR: 'INSIGHTS_ERROR',
} as const

// Utility functions for error handling
export function isObservaStackError(error: unknown): error is ObservaStackError {
  return error instanceof ObservaStackError
}

export function isNetworkError(error: unknown): error is NetworkError {
  return error instanceof NetworkError
}

export function isAuthenticationError(error: unknown): error is AuthenticationError {
  return error instanceof AuthenticationError
}

export function isAuthorizationError(error: unknown): error is AuthorizationError {
  return error instanceof AuthorizationError
}

export function isValidationError(error: unknown): error is ValidationError {
  return error instanceof ValidationError
}

export function isRateLimitError(error: unknown): error is RateLimitError {
  return error instanceof RateLimitError
}

export function getErrorMessage(error: unknown): string {
  if (isObservaStackError(error)) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}

export function getErrorCode(error: unknown): string {
  if (isObservaStackError(error)) {
    return error.code
  }
  return ERROR_CODES.UNKNOWN_ERROR
}

// Error reporting configuration
export interface ErrorReportingConfig {
  enabled: boolean
  endpoint?: string
  apiKey?: string
  environment: string
  userId?: string
  tenantId?: string
}