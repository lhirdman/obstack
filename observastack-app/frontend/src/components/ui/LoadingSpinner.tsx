import React from 'react'
import { clsx } from 'clsx'

export interface LoadingSpinnerProps extends React.SVGAttributes<SVGElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'white' | 'gray'
  className?: string
}

export function LoadingSpinner({ 
  size = 'md', 
  color = 'primary', 
  className,
  ...props
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  }

  const colorClasses = {
    primary: 'text-blue-600',
    secondary: 'text-gray-600',
    white: 'text-white',
    gray: 'text-gray-400'
  }

  return (
    <svg
      className={clsx(
        'animate-spin',
        sizeClasses[size],
        colorClasses[color],
        className
      )}
      fill="none"
      viewBox="0 0 24 24"
      {...props}
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )
}

export interface LoadingOverlayProps {
  loading: boolean
  children: React.ReactNode
  message?: string
  className?: string
}

export function LoadingOverlay({ 
  loading, 
  children, 
  message = 'Loading...', 
  className 
}: LoadingOverlayProps) {
  return (
    <div className={clsx('relative', className)}>
      {children}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <div className="flex flex-col items-center space-y-3">
            <LoadingSpinner size="lg" />
            <p className="text-sm text-gray-600">{message}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export interface LoadingStateProps {
  loading: boolean
  error?: Error | string | null
  children: React.ReactNode
  loadingComponent?: React.ReactNode
  errorComponent?: React.ReactNode
  onRetry?: () => void
}

export function LoadingState({
  loading,
  error,
  children,
  loadingComponent,
  errorComponent,
  onRetry
}: LoadingStateProps) {
  if (loading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>
    }

    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <LoadingSpinner size="lg" />
          <p className="text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    if (errorComponent) {
      return <>{errorComponent}</>
    }

    const errorMessage = error instanceof Error ? error.message : String(error)

    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Something went wrong</h3>
        <p className="text-gray-600 mb-4 max-w-md">{errorMessage}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Try Again
          </button>
        )}
      </div>
    )
  }

  return <>{children}</>
}