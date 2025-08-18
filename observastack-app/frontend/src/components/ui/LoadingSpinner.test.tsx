import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LoadingSpinner, LoadingOverlay, LoadingState } from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner data-testid="spinner" />)
    
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('animate-spin', 'w-6', 'h-6', 'text-blue-600')
  })

  it('applies size classes correctly', () => {
    render(<LoadingSpinner size="lg" data-testid="spinner" />)
    
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('w-8', 'h-8')
  })

  it('applies color classes correctly', () => {
    render(<LoadingSpinner color="white" data-testid="spinner" />)
    
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('text-white')
  })

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-class" data-testid="spinner" />)
    
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('custom-class')
  })
})

describe('LoadingOverlay', () => {
  it('renders children when not loading', () => {
    render(
      <LoadingOverlay loading={false}>
        <div data-testid="content">Content</div>
      </LoadingOverlay>
    )

    expect(screen.getByTestId('content')).toBeInTheDocument()
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })

  it('shows overlay when loading', () => {
    render(
      <LoadingOverlay loading={true}>
        <div data-testid="content">Content</div>
      </LoadingOverlay>
    )

    expect(screen.getByTestId('content')).toBeInTheDocument()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows custom loading message', () => {
    render(
      <LoadingOverlay loading={true} message="Please wait...">
        <div>Content</div>
      </LoadingOverlay>
    )

    expect(screen.getByText('Please wait...')).toBeInTheDocument()
  })

  it('applies overlay styles when loading', () => {
    const { container } = render(
      <LoadingOverlay loading={true}>
        <div>Content</div>
      </LoadingOverlay>
    )

    const overlay = container.querySelector('.absolute.inset-0')
    expect(overlay).toHaveClass('bg-white', 'bg-opacity-75', 'flex', 'items-center', 'justify-center')
  })
})

describe('LoadingState', () => {
  it('renders children when not loading and no error', () => {
    render(
      <LoadingState loading={false} error={null}>
        <div data-testid="content">Content</div>
      </LoadingState>
    )

    expect(screen.getByTestId('content')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <LoadingState loading={true} error={null}>
        <div>Content</div>
      </LoadingState>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Content')).not.toBeInTheDocument()
  })

  it('shows custom loading component', () => {
    render(
      <LoadingState 
        loading={true} 
        error={null}
        loadingComponent={<div data-testid="custom-loading">Custom Loading</div>}
      >
        <div>Content</div>
      </LoadingState>
    )

    expect(screen.getByTestId('custom-loading')).toBeInTheDocument()
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })

  it('shows error state with string error', () => {
    render(
      <LoadingState loading={false} error="Custom error message">
        <div>Content</div>
      </LoadingState>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Custom error message')).toBeInTheDocument()
    expect(screen.queryByText('Content')).not.toBeInTheDocument()
  })

  it('shows error state with Error object', () => {
    const error = new Error('Network error')
    render(
      <LoadingState loading={false} error={error}>
        <div>Content</div>
      </LoadingState>
    )

    expect(screen.getByText('Network error')).toBeInTheDocument()
    expect(screen.queryByText('Content')).not.toBeInTheDocument()
  })

  it('shows custom error component', () => {
    render(
      <LoadingState 
        loading={false} 
        error="Error occurred"
        errorComponent={<div data-testid="custom-error">Custom Error</div>}
      >
        <div>Content</div>
      </LoadingState>
    )

    expect(screen.getByTestId('custom-error')).toBeInTheDocument()
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn()
    
    render(
      <LoadingState loading={false} error="Error occurred" onRetry={onRetry}>
        <div>Content</div>
      </LoadingState>
    )

    const retryButton = screen.getByText('Try Again')
    fireEvent.click(retryButton)

    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('does not show retry button when onRetry is not provided', () => {
    render(
      <LoadingState loading={false} error="Error occurred">
        <div>Content</div>
      </LoadingState>
    )

    expect(screen.queryByText('Try Again')).not.toBeInTheDocument()
  })
})