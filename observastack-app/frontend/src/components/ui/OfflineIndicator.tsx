import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { WifiIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

export interface OfflineIndicatorProps {
  className?: string
  showWhenOnline?: boolean
}

export function OfflineIndicator({ className, showWhenOnline = false }: OfflineIndicatorProps) {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [showIndicator, setShowIndicator] = useState(false)

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      if (showWhenOnline) {
        setShowIndicator(true)
        // Hide the "back online" indicator after 3 seconds
        setTimeout(() => setShowIndicator(false), 3000)
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      setShowIndicator(true)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Show indicator initially if offline
    if (!navigator.onLine) {
      setShowIndicator(true)
    }

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [showWhenOnline])

  if (!showIndicator) return null

  return (
    <div
      className={clsx(
        'fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-4 py-2 rounded-lg shadow-lg transition-all duration-300',
        {
          'bg-red-100 border border-red-200 text-red-800': !isOnline,
          'bg-green-100 border border-green-200 text-green-800': isOnline
        },
        className
      )}
    >
      <div className="flex items-center space-x-2">
        {isOnline ? (
          <WifiIcon className="w-5 h-5 text-green-600" />
        ) : (
          <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
        )}
        <span className="text-sm font-medium">
          {isOnline ? 'Back online' : 'You are offline'}
        </span>
      </div>
    </div>
  )
}

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}

interface OfflineWrapperProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  className?: string
}

export function OfflineWrapper({ children, fallback, className }: OfflineWrapperProps) {
  const isOnline = useOnlineStatus()

  if (!isOnline && fallback) {
    return <div className={className}>{fallback}</div>
  }

  if (!isOnline) {
    return (
      <div className={clsx('flex flex-col items-center justify-center p-8 text-center', className)}>
        <ExclamationTriangleIcon className="w-12 h-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">You're offline</h3>
        <p className="text-gray-600 max-w-md">
          This feature requires an internet connection. Please check your connection and try again.
        </p>
      </div>
    )
  }

  return <>{children}</>
}