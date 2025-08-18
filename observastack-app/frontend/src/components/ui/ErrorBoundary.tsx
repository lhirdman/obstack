import React, { Component, ErrorInfo, ReactNode } from 'react'
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { Button } from './Button'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
}

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo })
    
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
    
    // Call optional error handler
    this.props.onError?.(error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onRetry={this.handleRetry}
          showDetails={this.props.showDetails}
        />
      )
    }

    return this.props.children
  }
}

interface ErrorFallbackProps {
  error?: Error
  errorInfo?: ErrorInfo
  onRetry?: () => void
  showDetails?: boolean
  title?: string
  message?: string
}

export function ErrorFallback({
  error,
  errorInfo,
  onRetry,
  showDetails = false,
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.'
}: ErrorFallbackProps) {
  const [showErrorDetails, setShowErrorDetails] = React.useState(false)

  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] p-6 bg-white border border-red-200 rounded-lg">
      <div className="flex items-center justify-center w-12 h-12 mb-4 bg-red-100 rounded-full">
        <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
      </div>
      
      <h3 className="mb-2 text-lg font-medium text-gray-900">{title}</h3>
      <p className="mb-4 text-sm text-gray-600 text-center max-w-md">{message}</p>
      
      <div className="flex flex-col sm:flex-row gap-3">
        {onRetry && (
          <Button onClick={onRetry} className="flex items-center">
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        )}
        
        {showDetails && error && (
          <Button
            variant="outline"
            onClick={() => setShowErrorDetails(!showErrorDetails)}
          >
            {showErrorDetails ? 'Hide Details' : 'Show Details'}
          </Button>
        )}
      </div>
      
      {showErrorDetails && error && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-md w-full max-w-2xl">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Error Details</h4>
          <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-auto max-h-40">
            {error.message}
            {error.stack && `\n\nStack trace:\n${error.stack}`}
            {errorInfo?.componentStack && `\n\nComponent stack:${errorInfo.componentStack}`}
          </pre>
        </div>
      )}
    </div>
  )
}

interface AsyncErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error) => void
}

export function AsyncErrorBoundary({ children, fallback, onError }: AsyncErrorBoundaryProps) {
  const [error, setError] = React.useState<Error | null>(null)

  React.useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
      setError(error)
      onError?.(error)
    }

    window.addEventListener('unhandledrejection', handleUnhandledRejection)
    return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection)
  }, [onError])

  const handleRetry = () => {
    setError(null)
  }

  if (error) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <ErrorFallback
        error={error}
        onRetry={handleRetry}
        title="Async Operation Failed"
        message="An error occurred during an asynchronous operation. Please try again."
      />
    )
  }

  return <>{children}</>
}