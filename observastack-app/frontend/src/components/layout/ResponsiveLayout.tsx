import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'

export interface ResponsiveLayoutProps {
  sidebar: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function ResponsiveLayout({
  sidebar,
  children,
  className
}: ResponsiveLayoutProps) {
  const [isMobile, setIsMobile] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      if (!mobile) {
        setSidebarOpen(false) // Close mobile sidebar when switching to desktop
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  return (
    <div className={clsx('flex h-screen bg-gray-50', className)}>
      {/* Desktop sidebar */}
      {!isMobile && (
        <div className="hidden md:flex md:flex-shrink-0">
          {sidebar}
        </div>
      )}

      {/* Mobile sidebar */}
      {isMobile && sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black bg-opacity-25 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl md:hidden">
            {sidebar}
          </div>
        </>
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Mobile header */}
        {isMobile && (
          <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 md:hidden">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 -ml-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            >
              <span className="sr-only">Open sidebar</span>
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-lg font-medium text-gray-900">ObservaStack</h1>
            <div className="w-10" /> {/* Spacer for centering */}
          </div>
        )}

        {/* Main content area */}
        <main className="flex-1 overflow-auto focus:outline-none">
          {children}
        </main>
      </div>
    </div>
  )
}

export interface TouchFriendlyButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'secondary' | 'ghost'
}

export function TouchFriendlyButton({
  children,
  size = 'md',
  variant = 'primary',
  className,
  ...props
}: TouchFriendlyButtonProps) {
  const sizeClasses = {
    sm: 'min-h-[40px] px-3 py-2 text-sm', // Minimum 40px for touch
    md: 'min-h-[44px] px-4 py-2 text-base', // Minimum 44px for touch
    lg: 'min-h-[48px] px-6 py-3 text-lg' // Minimum 48px for touch
  }

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 active:bg-gray-400',
    ghost: 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
  }

  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center font-medium rounded-md transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed',
        sizeClasses[size],
        variantClasses[variant],
        // Touch-friendly styles
        'touch-manipulation select-none',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export interface TouchFriendlyCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  interactive?: boolean
  padding?: 'sm' | 'md' | 'lg'
}

export function TouchFriendlyCard({
  children,
  interactive = false,
  padding = 'md',
  className,
  ...props
}: TouchFriendlyCardProps) {
  const paddingClasses = {
    sm: 'p-3',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8'
  }

  return (
    <div
      className={clsx(
        'bg-white rounded-lg border border-gray-200 shadow-sm',
        paddingClasses[padding],
        interactive && 'cursor-pointer hover:shadow-md active:shadow-lg transition-shadow duration-150 ease-in-out touch-manipulation',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}