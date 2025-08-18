import React from 'react'
import { clsx } from 'clsx'

export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  children: React.ReactNode
}

export function Container({
  size = 'xl',
  padding = 'md',
  className,
  children,
  ...props
}: ContainerProps) {
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-4xl',
    xl: 'max-w-7xl',
    full: 'max-w-full'
  }

  const paddingClasses = {
    none: '',
    sm: 'px-2 sm:px-4',
    md: 'px-4 sm:px-6 lg:px-8',
    lg: 'px-6 sm:px-8 lg:px-12',
    xl: 'px-8 sm:px-12 lg:px-16'
  }

  return (
    <div
      className={clsx(
        'mx-auto w-full',
        sizeClasses[size],
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}