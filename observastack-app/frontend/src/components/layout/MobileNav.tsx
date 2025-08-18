import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'

export interface MobileNavProps {
  children: React.ReactNode
  className?: string
}

export function MobileNav({ children, className }: MobileNavProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      {/* Mobile menu button */}
      <div className="md:hidden">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
          aria-expanded="false"
        >
          <span className="sr-only">Open main menu</span>
          {isOpen ? (
            <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
          ) : (
            <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
          )}
        </button>
      </div>

      {/* Mobile menu overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-black bg-opacity-25"
            onClick={() => setIsOpen(false)}
          />
          <div className="relative flex flex-col w-full max-w-xs bg-white shadow-xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Menu</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 -mr-2 text-gray-400 hover:text-gray-500"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className={clsx('flex-1 px-4 py-6 overflow-y-auto', className)}>
              {children}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export interface MobileNavItemProps {
  href?: string
  icon?: React.ReactNode
  children: React.ReactNode
  active?: boolean
  onClick?: () => void
  className?: string
}

export function MobileNavItem({
  href,
  icon,
  children,
  active = false,
  onClick,
  className
}: MobileNavItemProps) {
  const baseClasses = 'flex items-center px-3 py-2 text-base font-medium rounded-md transition-colors duration-150 ease-in-out'
  const activeClasses = active
    ? 'bg-blue-100 text-blue-900'
    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'

  const content = (
    <>
      {icon && (
        <div className={clsx(
          'flex-shrink-0 mr-3',
          active ? 'text-blue-500' : 'text-gray-400'
        )}>
          {icon}
        </div>
      )}
      <span>{children}</span>
    </>
  )

  if (href) {
    return (
      <a
        href={href}
        className={clsx(baseClasses, activeClasses, className)}
        onClick={onClick}
      >
        {content}
      </a>
    )
  }

  return (
    <button
      className={clsx(baseClasses, activeClasses, 'w-full text-left', className)}
      onClick={onClick}
    >
      {content}
    </button>
  )
}