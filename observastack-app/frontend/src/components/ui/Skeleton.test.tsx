import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton, SkeletonText, SkeletonCard, SkeletonTable, SkeletonList } from './Skeleton'

describe('Skeleton', () => {
  it('renders with default props', () => {
    render(<Skeleton data-testid="skeleton" />)
    
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('bg-gray-200', 'rounded-md', 'animate-pulse')
  })

  it('applies variant classes correctly', () => {
    render(<Skeleton variant="circular" data-testid="skeleton" />)
    
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('rounded-full')
  })

  it('applies custom width and height', () => {
    render(<Skeleton width={100} height={50} data-testid="skeleton" />)
    
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveStyle({ width: '100px', height: '50px' })
  })

  it('applies animation classes', () => {
    render(<Skeleton animation="none" data-testid="skeleton" />)
    
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).not.toHaveClass('animate-pulse')
  })
})

describe('SkeletonText', () => {
  it('renders default number of lines', () => {
    render(<SkeletonText data-testid="skeleton-text" />)
    
    const container = screen.getByTestId('skeleton-text')
    const lines = container.querySelectorAll('div')
    expect(lines).toHaveLength(3)
  })

  it('renders custom number of lines', () => {
    render(<SkeletonText lines={5} data-testid="skeleton-text" />)
    
    const container = screen.getByTestId('skeleton-text')
    const lines = container.querySelectorAll('div')
    expect(lines).toHaveLength(5)
  })
})

describe('SkeletonCard', () => {
  it('renders with all elements by default', () => {
    render(<SkeletonCard data-testid="skeleton-card" />)
    
    const card = screen.getByTestId('skeleton-card')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('p-4', 'border', 'rounded-lg', 'bg-white')
  })

  it('hides avatar when showAvatar is false', () => {
    const { container } = render(<SkeletonCard showAvatar={false} />)
    
    // Check that there's no circular skeleton (avatar)
    const circularSkeletons = container.querySelectorAll('.rounded-full')
    expect(circularSkeletons).toHaveLength(0)
  })
})

describe('SkeletonTable', () => {
  it('renders with default rows and columns', () => {
    const { container } = render(<SkeletonTable />)
    
    // Should have header + 5 rows = 6 total rows
    const rows = container.querySelectorAll('.grid')
    expect(rows).toHaveLength(6) // 1 header + 5 data rows
  })

  it('renders custom rows and columns', () => {
    const { container } = render(<SkeletonTable rows={3} columns={2} />)
    
    // Should have header + 3 rows = 4 total rows
    const rows = container.querySelectorAll('.grid')
    expect(rows).toHaveLength(4) // 1 header + 3 data rows
  })
})

describe('SkeletonList', () => {
  it('renders default number of items', () => {
    const { container } = render(<SkeletonList />)
    
    const items = container.querySelectorAll('.flex.items-center')
    expect(items).toHaveLength(5)
  })

  it('renders custom number of items', () => {
    const { container } = render(<SkeletonList items={3} />)
    
    const items = container.querySelectorAll('.flex.items-center')
    expect(items).toHaveLength(3)
  })

  it('hides avatars when showAvatar is false', () => {
    const { container } = render(<SkeletonList showAvatar={false} />)
    
    const circularSkeletons = container.querySelectorAll('.rounded-full')
    expect(circularSkeletons).toHaveLength(0)
  })
})