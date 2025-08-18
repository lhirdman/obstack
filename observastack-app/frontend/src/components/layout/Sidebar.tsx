import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'

export interface SidebarProps {
  children: React.ReactNode
  className?: string
  collapsible?: boolean
  defaultCollapsed?: boolean
}

export function Sidebar({
  children,
  className,
  collapsible = true,
  defaultCollapsed = false
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed)
  const [isMobile, setIsMobile] = useState(false)

  // Check if we're on mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      // Auto-collapse on mobile
      if (window.innerWidth < 768) {
        setIsCollapsed(true)
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed)
  }

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && !isCollapsed && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsCollapsed(true)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed md:static inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-gray-200 transition-all duration-300 ease-in-out',
          {
            // Mobile styles
            'w-64 translate-x-0': !isCollapsed && isMobile,
            'w-64 -translate-x-full': isCollapsed && isMobile,
            // Desktop styles
            'w-64': !isCollapsed && !isMobile,
            'w-16': isCollapsed && !isMobile,
          },
          className
        )}
      >
        {/* Toggle button */}
        {collapsible && (
          <button
            onClick={toggleSidebar}
            className={clsx(
              'absolute top-4 -right-3 z-10 flex items-center justify-center w-6 h-6 bg-white border border-gray-200 rounded-full shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
              {
                'md:block': !isMobile,
                'block': isMobile
              }
            )}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <Bars3Icon className="w-4 h-4 text-gray-600" />
            ) : (
              <XMarkIcon className="w-4 h-4 text-gray-600" />
            )}
          </button>
        )}

        {/* Sidebar content */}
        <div className={clsx(
          'flex-1 flex flex-col overflow-hidden',
          {
            'px-3 py-4': (!isCollapsed) || isMobile,
            'px-2 py-4': isCollapsed && !isMobile,
          }
        )}>
          {children}
        </div>
      </aside>
    </>
  )
}

export interface SidebarHeaderProps {
  title: string
  collapsed?: boolean
  className?: string
}

export function SidebarHeader({ title, collapsed, className }: SidebarHeaderProps) {
  return (
    <div className={clsx('mb-6', className)}>
      {collapsed ? (
        <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
          <span className="text-white font-bold text-sm">
            {title.charAt(0)}
          </span>
        </div>
      ) : (
        <h1 className="text-lg font-bold text-gray-900 truncate">
          {title}
        </h1>
      )}
    </div>
  )
}

export interface SidebarNavProps {
  children: React.ReactNode
  collapsed?: boolean
  className?: string
}

export function SidebarNav({ children, collapsed, className }: SidebarNavProps) {
  return (
    <nav className={clsx(
      'flex-1 space-y-1 overflow-y-auto',
      className
    )}>
      {children}
    </nav>
  )
}

export interface SidebarNavItemProps {
  href?: string
  icon?: React.ReactNode
  children: React.ReactNode
  active?: boolean
  collapsed?: boolean
  onClick?: () => void
  className?: string
}

export function SidebarNavItem({
  href,
  icon,
  children,
  active = false,
  collapsed = false,
  onClick,
  className
}: SidebarNavItemProps) {
  const baseClasses = 'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-150 ease-in-out'
  const activeClasses = active
    ? 'bg-blue-100 text-blue-900'
    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'

  const content = (
    <>
      {icon && (
        <div className={clsx(
          'flex-shrink-0',
          collapsed ? 'mr-0' : 'mr-3',
          active ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
        )}>
          {icon}
        </div>
      )}
      {!collapsed && (
        <span className="truncate">{children}</span>
      )}
    </>
  )

  if (href) {
    return (
      <a
        href={href}
        className={clsx(baseClasses, activeClasses, className)}
        onClick={onClick}
        title={collapsed ? String(children) : undefined}
      >
        {content}
      </a>
    )
  }

  return (
    <button
      className={clsx(baseClasses, activeClasses, 'w-full text-left', className)}
      onClick={onClick}
      title={collapsed ? String(children) : undefined}
    >
      {content}
    </button>
  )
}