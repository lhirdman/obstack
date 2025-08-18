import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Sidebar, SidebarHeader, SidebarNav, SidebarNavItem } from './Sidebar'

// Mock window.innerWidth
const mockInnerWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
}

describe('Sidebar', () => {
  beforeEach(() => {
    mockInnerWidth(1024) // Desktop size
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders with default props', () => {
    render(
      <Sidebar>
        <div data-testid="sidebar-content">Sidebar Content</div>
      </Sidebar>
    )

    expect(screen.getByTestId('sidebar-content')).toBeInTheDocument()
  })

  it('shows toggle button when collapsible', () => {
    render(
      <Sidebar collapsible>
        <div>Content</div>
      </Sidebar>
    )

    expect(screen.getByLabelText('Collapse sidebar')).toBeInTheDocument()
  })

  it('toggles collapsed state when button is clicked', () => {
    render(
      <Sidebar collapsible>
        <div>Content</div>
      </Sidebar>
    )

    const toggleButton = screen.getByLabelText('Collapse sidebar')
    fireEvent.click(toggleButton)

    expect(screen.getByLabelText('Expand sidebar')).toBeInTheDocument()
  })

  it('auto-collapses on mobile', () => {
    mockInnerWidth(600) // Mobile size
    
    render(
      <Sidebar>
        <div>Content</div>
      </Sidebar>
    )

    // Trigger resize event
    fireEvent(window, new Event('resize'))

    // Should be collapsed on mobile
    const sidebar = screen.getByRole('complementary')
    expect(sidebar).toHaveClass('-translate-x-full')
  })
})

describe('SidebarHeader', () => {
  it('renders title when not collapsed', () => {
    render(<SidebarHeader title="Test Title" />)
    
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('renders initial when collapsed', () => {
    render(<SidebarHeader title="Test Title" collapsed />)
    
    expect(screen.getByText('T')).toBeInTheDocument()
    expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
  })
})

describe('SidebarNav', () => {
  it('renders navigation items', () => {
    render(
      <SidebarNav>
        <div data-testid="nav-item-1">Item 1</div>
        <div data-testid="nav-item-2">Item 2</div>
      </SidebarNav>
    )

    expect(screen.getByTestId('nav-item-1')).toBeInTheDocument()
    expect(screen.getByTestId('nav-item-2')).toBeInTheDocument()
  })
})

describe('SidebarNavItem', () => {
  it('renders as link when href is provided', () => {
    render(
      <SidebarNavItem href="/test">
        Test Link
      </SidebarNavItem>
    )

    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/test')
    expect(link).toHaveTextContent('Test Link')
  })

  it('renders as button when no href is provided', () => {
    render(
      <SidebarNavItem>
        Test Button
      </SidebarNavItem>
    )

    const button = screen.getByRole('button')
    expect(button).toHaveTextContent('Test Button')
  })

  it('applies active styles when active', () => {
    render(
      <SidebarNavItem active>
        Active Item
      </SidebarNavItem>
    )

    const button = screen.getByRole('button')
    expect(button).toHaveClass('bg-blue-100', 'text-blue-900')
  })

  it('renders icon when provided', () => {
    const TestIcon = () => <span data-testid="test-icon">🏠</span>
    
    render(
      <SidebarNavItem icon={<TestIcon />}>
        Home
      </SidebarNavItem>
    )

    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })

  it('hides text when collapsed', () => {
    render(
      <SidebarNavItem collapsed>
        Hidden Text
      </SidebarNavItem>
    )

    expect(screen.queryByText('Hidden Text')).not.toBeInTheDocument()
  })

  it('shows tooltip title when collapsed', () => {
    render(
      <SidebarNavItem collapsed>
        Tooltip Text
      </SidebarNavItem>
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('title', 'Tooltip Text')
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    
    render(
      <SidebarNavItem onClick={handleClick}>
        Clickable Item
      </SidebarNavItem>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})