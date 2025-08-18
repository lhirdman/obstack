import React from 'react'
import { clsx } from 'clsx'

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: 1 | 2 | 3 | 4 | 6 | 12
  gap?: 'sm' | 'md' | 'lg' | 'xl'
  responsive?: {
    sm?: 1 | 2 | 3 | 4 | 6 | 12
    md?: 1 | 2 | 3 | 4 | 6 | 12
    lg?: 1 | 2 | 3 | 4 | 6 | 12
    xl?: 1 | 2 | 3 | 4 | 6 | 12
  }
  children: React.ReactNode
}

export function Grid({
  cols = 1,
  gap = 'md',
  responsive,
  className,
  children,
  ...props
}: GridProps) {
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8'
  }

  const colClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    6: 'grid-cols-6',
    12: 'grid-cols-12'
  }

  const responsiveClasses = responsive ? [
    responsive.sm && `sm:grid-cols-${responsive.sm}`,
    responsive.md && `md:grid-cols-${responsive.md}`,
    responsive.lg && `lg:grid-cols-${responsive.lg}`,
    responsive.xl && `xl:grid-cols-${responsive.xl}`
  ].filter(Boolean).join(' ') : ''

  return (
    <div
      className={clsx(
        'grid',
        colClasses[cols],
        gapClasses[gap],
        responsiveClasses,
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export interface GridItemProps extends React.HTMLAttributes<HTMLDivElement> {
  span?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
  responsive?: {
    sm?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
    md?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
    lg?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
    xl?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
  }
  children: React.ReactNode
}

export function GridItem({
  span = 1,
  responsive,
  className,
  children,
  ...props
}: GridItemProps) {
  const spanClasses = {
    1: 'col-span-1',
    2: 'col-span-2',
    3: 'col-span-3',
    4: 'col-span-4',
    5: 'col-span-5',
    6: 'col-span-6',
    7: 'col-span-7',
    8: 'col-span-8',
    9: 'col-span-9',
    10: 'col-span-10',
    11: 'col-span-11',
    12: 'col-span-12'
  }

  const responsiveClasses = responsive ? [
    responsive.sm && `sm:col-span-${responsive.sm}`,
    responsive.md && `md:col-span-${responsive.md}`,
    responsive.lg && `lg:col-span-${responsive.lg}`,
    responsive.xl && `xl:col-span-${responsive.xl}`
  ].filter(Boolean).join(' ') : ''

  return (
    <div
      className={clsx(
        spanClasses[span],
        responsiveClasses,
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}