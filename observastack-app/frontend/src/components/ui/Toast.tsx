import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { clsx } from 'clsx'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon, 
  XCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  clearToasts: () => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

interface ToastProviderProps {
  children: React.ReactNode
  maxToasts?: number
}

export function ToastProvider({ children, maxToasts = 5 }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000
    }

    setToasts(prev => {
      const updated = [newToast, ...prev]
      return updated.slice(0, maxToasts)
    })

    // Auto-remove toast after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }

    return id
  }, [maxToasts])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const clearToasts = useCallback(() => {
    setToasts([])
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  )
}

function ToastContainer() {
  const { toasts } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}

interface ToastItemProps {
  toast: Toast
}

function ToastItem({ toast }: ToastItemProps) {
  const { removeToast } = useToast()
  const [isVisible, setIsVisible] = useState(false)
  const [isLeaving, setIsLeaving] = useState(false)

  useEffect(() => {
    // Trigger enter animation
    const timer = setTimeout(() => setIsVisible(true), 10)
    return () => clearTimeout(timer)
  }, [])

  const handleClose = () => {
    setIsLeaving(true)
    setTimeout(() => removeToast(toast.id), 150)
  }

  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon
  }

  const colors = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  }

  const iconColors = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400'
  }

  const Icon = icons[toast.type]

  return (
    <div
      className={clsx(
        'relative flex items-start p-4 border rounded-lg shadow-lg transition-all duration-300 ease-in-out transform',
        colors[toast.type],
        {
          'translate-x-0 opacity-100': isVisible && !isLeaving,
          'translate-x-full opacity-0': !isVisible || isLeaving
        }
      )}
    >
      <div className="flex-shrink-0">
        <Icon className={clsx('w-5 h-5', iconColors[toast.type])} />
      </div>
      
      <div className="ml-3 flex-1">
        <h4 className="text-sm font-medium">{toast.title}</h4>
        {toast.message && (
          <p className="mt-1 text-sm opacity-90">{toast.message}</p>
        )}
        
        {toast.action && (
          <div className="mt-2">
            <button
              onClick={toast.action.onClick}
              className="text-sm font-medium underline hover:no-underline focus:outline-none"
            >
              {toast.action.label}
            </button>
          </div>
        )}
      </div>
      
      <button
        onClick={handleClose}
        className="ml-4 flex-shrink-0 p-1 rounded-md hover:bg-black hover:bg-opacity-10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current"
        aria-label="Close notification"
      >
        <XMarkIcon className="w-4 h-4" />
      </button>
    </div>
  )
}

// Convenience hooks for different toast types
export function useToastHelpers() {
  const { addToast } = useToast()

  const success = useCallback((title: string, message?: string, options?: Partial<Toast>) => {
    return addToast({ type: 'success', title, message, ...options })
  }, [addToast])

  const error = useCallback((title: string, message?: string, options?: Partial<Toast>) => {
    return addToast({ type: 'error', title, message, ...options })
  }, [addToast])

  const warning = useCallback((title: string, message?: string, options?: Partial<Toast>) => {
    return addToast({ type: 'warning', title, message, ...options })
  }, [addToast])

  const info = useCallback((title: string, message?: string, options?: Partial<Toast>) => {
    return addToast({ type: 'info', title, message, ...options })
  }, [addToast])

  return { success, error, warning, info }
}