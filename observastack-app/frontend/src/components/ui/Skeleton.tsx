import React from 'react'
import { clsx } from 'clsx'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number
  height?: string | number
  variant?: 'text' | 'rectangular' | 'circular'
  animation?: 'pulse' | 'wave' | 'none'
}

export function Skeleton({
  width,
  height,
  variant = 'rectangular',
  animation = 'pulse',
  className,
  ...props
}: SkeletonProps) {
  const baseClasses = 'bg-gray-200'
  
  const variantClasses = {
    text: 'rounded',
    rectangular: 'rounded-md',
    circular: 'rounded-full'
  }
  
  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-pulse', // Could implement wave animation with CSS
    none: ''
  }

  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }

  return (
    <div
      className={clsx(
        baseClasses,
        variantClasses[variant],
        animationClasses[animation],
        className
      )}
      style={style}
      {...props}
    />
  )
}

export interface SkeletonTextProps extends React.HTMLAttributes<HTMLDivElement> {
  lines?: number
  className?: string
}

export function SkeletonText({ lines = 3, className, ...props }: SkeletonTextProps) {
  return (
    <div className={clsx('space-y-2', className)} {...props}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          variant="text"
          height={16}
          width={i === lines - 1 ? '75%' : '100%'}
        />
      ))}
    </div>
  )
}

export interface SkeletonCardProps extends React.HTMLAttributes<HTMLDivElement> {
  showAvatar?: boolean
  showTitle?: boolean
  showDescription?: boolean
  className?: string
}

export function SkeletonCard({
  showAvatar = true,
  showTitle = true,
  showDescription = true,
  className,
  ...props
}: SkeletonCardProps) {
  return (
    <div className={clsx('p-4 border border-gray-200 rounded-lg bg-white', className)} {...props}>
      <div className="flex items-start space-x-3">
        {showAvatar && (
          <Skeleton variant="circular" width={40} height={40} />
        )}
        <div className="flex-1 space-y-2">
          {showTitle && (
            <Skeleton variant="text" height={20} width="60%" />
          )}
          {showDescription && (
            <SkeletonText lines={2} />
          )}
        </div>
      </div>
    </div>
  )
}

export interface SkeletonTableProps {
  rows?: number
  columns?: number
  className?: string
}

export function SkeletonTable({ rows = 5, columns = 4, className }: SkeletonTableProps) {
  return (
    <div className={clsx('space-y-3', className)}>
      {/* Header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }, (_, i) => (
          <Skeleton key={`header-${i}`} variant="text" height={20} />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }, (_, rowIndex) => (
        <div key={`row-${rowIndex}`} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }, (_, colIndex) => (
            <Skeleton key={`cell-${rowIndex}-${colIndex}`} variant="text" height={16} />
          ))}
        </div>
      ))}
    </div>
  )
}

export interface SkeletonListProps {
  items?: number
  showAvatar?: boolean
  className?: string
}

export function SkeletonList({ items = 5, showAvatar = true, className }: SkeletonListProps) {
  return (
    <div className={clsx('space-y-3', className)}>
      {Array.from({ length: items }, (_, i) => (
        <div key={i} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
          {showAvatar && (
            <Skeleton variant="circular" width={32} height={32} />
          )}
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" height={16} width="40%" />
            <Skeleton variant="text" height={14} width="80%" />
          </div>
        </div>
      ))}
    </div>
  )
}