import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ResponsiveLayout, TouchFriendlyButton, TouchFriendlyCard } from './ResponsiveLayout'

// Mock window.innerWidth
const mockInnerWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
}

describe('ResponsiveLayout', () => {
  beforeEach(() => {
    // Reset to desktop size
    mockInnerWidth(1024)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders desktop layout correctly', () => {
    render(
      <ResponsiveLayout
        sidebar={<div data-testid="sidebar">Sidebar</div>}
      >
        <div data-testid="main-content">Main Content</div>
      </ResponsiveLayout>
    )

    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('main-content')).toBeInTheDocument()
  })

  it('shows mobile header on mobile screens', () => {
    mockInnerWidth(600)
    
    render(
      <ResponsiveLayout
        sidebar={<div data-testid="sidebar">Sidebar</div>}
      >
        <div data-testid="main-content">Main Content</div>
      </ResponsiveLayout>
    )

    // Trigger resize event
    fireEvent(window, new Event('resize'))

    expect(screen.getByText('ObservaStack')).toBeInTheDocument()
    expect(screen.getByText('Open sidebar')).toBeInTheDocument()
  })

  it('opens mobile sidebar when button is clicked', () => {
    mockInnerWidth(600)
    
    render(
      <ResponsiveLayout
        sidebar={<div data-testid="sidebar">Sidebar</div>}
      >
        <div data-testid="main-content">Main Content</div>
      </ResponsiveLayout>
    )

    // Trigger resize event to activate mobile mode
    fireEvent(window, new Event('resize'))

    const openButton = screen.getByText('Open sidebar')
    fireEvent.click(openButton)

    // Sidebar should be visible
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
  })
})

describe('TouchFriendlyButton', () => {
  it('renders with default props', () => {
    render(
      <TouchFriendlyButton data-testid="button">
        Click me
      </TouchFriendlyButton>
    )

    const button = screen.getByTestId('button')
    expect(button).toHaveClass('min-h-[44px]', 'px-4', 'py-2', 'text-base')
    expect(button).toHaveClass('bg-blue-600', 'text-white')
  })

  it('applies size classes correctly', () => {
    render(
      <TouchFriendlyButton size="lg" data-testid="button">
        Large Button
      </TouchFriendlyButton>
    )

    const button = screen.getByTestId('button')
    expect(button).toHaveClass('min-h-[48px]', 'px-6', 'py-3', 'text-lg')
  })

  it('applies variant classes correctly', () => {
    render(
      <TouchFriendlyButton variant="secondary" data-testid="button">
        Secondary Button
      </TouchFriendlyButton>
    )

    const button = screen.getByTestId('button')
    expect(button).toHaveClass('bg-gray-200', 'text-gray-900')
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    render(
      <TouchFriendlyButton onClick={handleClick} data-testid="button">
        Click me
      </TouchFriendlyButton>
    )

    const button = screen.getByTestId('button')
    fireEvent.click(button)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(
      <TouchFriendlyButton disabled data-testid="button">
        Disabled Button
      </TouchFriendlyButton>
    )

    const button = screen.getByTestId('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed')
  })
})

describe('TouchFriendlyCard', () => {
  it('renders with default props', () => {
    render(
      <TouchFriendlyCard data-testid="card">
        Card content
      </TouchFriendlyCard>
    )

    const card = screen.getByTestId('card')
    expect(card).toHaveClass('bg-white', 'rounded-lg', 'border', 'p-4', 'sm:p-6')
  })

  it('applies interactive styles when interactive is true', () => {
    render(
      <TouchFriendlyCard interactive data-testid="card">
        Interactive card
      </TouchFriendlyCard>
    )

    const card = screen.getByTestId('card')
    expect(card).toHaveClass('cursor-pointer', 'hover:shadow-md', 'touch-manipulation')
  })

  it('applies padding classes correctly', () => {
    render(
      <TouchFriendlyCard padding="lg" data-testid="card">
        Large padding card
      </TouchFriendlyCard>
    )

    const card = screen.getByTestId('card')
    expect(card).toHaveClass('p-6', 'sm:p-8')
  })

  it('handles click events when interactive', () => {
    const handleClick = vi.fn()
    render(
      <TouchFriendlyCard interactive onClick={handleClick} data-testid="card">
        Clickable card
      </TouchFriendlyCard>
    )

    const card = screen.getByTestId('card')
    fireEvent.click(card)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})