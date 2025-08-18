import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EmbeddedDashboard } from './EmbeddedDashboard'

// Mock the authentication context
const mockAuthContext = {
  user: {
    id: 'user-1',
    username: 'testuser',
    email: 'test@example.com',
    tenantId: 'tenant-1',
    roles: ['viewer']
  },
  token: 'mock-jwt-token',
  isAuthenticated: true
}

vi.mock('../../auth/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

describe('EmbeddedDashboard', () => {
  const mockOnNavigate = vi.fn()
  const mockOnError = vi.fn()

  beforeEach(() => {
    mockOnNavigate.mockClear()
    mockOnError.mockClear()
    
    // Mock iframe load event
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
      writable: true,
      value: {
        postMessage: vi.fn()
      }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders iframe with correct src URL', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    expect(iframe).toBeInTheDocument()
    expect(iframe).toHaveAttribute('src', expect.stringContaining('/grafana/d/dashboard-1'))
  })

  it('includes authentication token in URL parameters', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    expect(iframe).toHaveAttribute('src', expect.stringContaining('auth_token=mock-jwt-token'))
  })

  it('includes tenant context in URL parameters', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    expect(iframe).toHaveAttribute('src', expect.stringContaining('tenant_id=tenant-1'))
  })

  it('applies custom time range when provided', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        timeRange={{ from: 'now-1h', to: 'now' }}
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    expect(iframe).toHaveAttribute('src', expect.stringContaining('from=now-1h'))
    expect(iframe).toHaveAttribute('src', expect.stringContaining('to=now'))
  })

  it('applies custom variables when provided', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        variables={{ service: 'api-server', environment: 'production' }}
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    expect(iframe).toHaveAttribute('src', expect.stringContaining('var-service=api-server'))
    expect(iframe).toHaveAttribute('src', expect.stringContaining('var-environment=production'))
  })

  it('shows loading state initially', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument()
  })

  it('hides loading state when iframe loads', async () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    
    // Simulate iframe load event
    fireEvent.load(iframe)

    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).not.toBeInTheDocument()
    })
  })

  it('shows error state when iframe fails to load', async () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    
    // Simulate iframe error event
    fireEvent.error(iframe)

    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard')).toBeInTheDocument()
    })

    expect(mockOnError).toHaveBeenCalledWith(expect.any(Error))
  })

  it('shows retry button on error', async () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    fireEvent.error(iframe)

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })
  })

  it('reloads iframe when retry button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    fireEvent.error(iframe)

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })

    const retryButton = screen.getByText('Retry')
    await user.click(retryButton)

    // Should show loading state again
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument()
  })

  it('applies fullscreen mode when enabled', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        fullscreen={true}
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const container = screen.getByTitle('System Metrics dashboard').parentElement
    expect(container).toHaveClass('fixed', 'inset-0', 'z-50')
  })

  it('shows navigation overlay when showNavigation is true', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        showNavigation={true}
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    expect(screen.getByText('System Metrics')).toBeInTheDocument()
    expect(screen.getByLabelText('Go back')).toBeInTheDocument()
    expect(screen.getByLabelText('Open in new tab')).toBeInTheDocument()
  })

  it('calls onNavigate when back button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        showNavigation={true}
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const backButton = screen.getByLabelText('Go back')
    await user.click(backButton)

    expect(mockOnNavigate).toHaveBeenCalledWith('back')
  })

  it('opens dashboard in new tab when external link is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock window.open
    const mockOpen = vi.fn()
    Object.defineProperty(window, 'open', {
      writable: true,
      value: mockOpen
    })

    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        showNavigation={true}
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const externalButton = screen.getByLabelText('Open in new tab')
    await user.click(externalButton)

    expect(mockOpen).toHaveBeenCalledWith(
      expect.stringContaining('/grafana/d/dashboard-1'),
      '_blank'
    )
  })

  it('handles iframe communication messages', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    // Simulate message from iframe
    const messageEvent = new MessageEvent('message', {
      data: {
        type: 'grafana-navigation',
        payload: { dashboard: 'new-dashboard-id' }
      },
      origin: window.location.origin
    })

    fireEvent(window, messageEvent)

    expect(mockOnNavigate).toHaveBeenCalledWith('dashboard', { dashboard: 'new-dashboard-id' })
  })

  it('ignores messages from untrusted origins', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    // Simulate message from untrusted origin
    const messageEvent = new MessageEvent('message', {
      data: {
        type: 'grafana-navigation',
        payload: { dashboard: 'malicious-dashboard' }
      },
      origin: 'https://malicious-site.com'
    })

    fireEvent(window, messageEvent)

    expect(mockOnNavigate).not.toHaveBeenCalled()
  })

  it('applies custom height when provided', () => {
    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        height="600px"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    const iframe = screen.getByTitle('System Metrics dashboard')
    expect(iframe).toHaveStyle({ height: '600px' })
  })

  it('handles missing authentication gracefully', () => {
    // Mock unauthenticated state
    vi.mocked(mockAuthContext).isAuthenticated = false
    vi.mocked(mockAuthContext).token = null

    render(
      <EmbeddedDashboard
        dashboardId="dashboard-1"
        title="System Metrics"
        onNavigate={mockOnNavigate}
        onError={mockOnError}
      />
    )

    expect(screen.getByText('Authentication required')).toBeInTheDocument()
    expect(screen.queryByTitle('System Metrics dashboard')).not.toBeInTheDocument()
  })
})