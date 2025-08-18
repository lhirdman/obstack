import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AlertList } from './AlertList'
import { Alert } from '../../types/alerts'

describe('AlertList', () => {
  const mockOnAlertClick = vi.fn()
  const mockOnAcknowledge = vi.fn()
  const mockOnResolve = vi.fn()
  const mockOnLoadMore = vi.fn()

  const mockAlerts: Alert[] = [
    {
      id: 'alert-1',
      title: 'High CPU Usage',
      description: 'CPU usage is above 90%',
      severity: 'critical',
      status: 'active',
      source: 'prometheus',
      timestamp: '2025-08-16T07:30:00Z',
      labels: { service: 'api-server' },
      tenantId: 'tenant-1'
    },
    {
      id: 'alert-2',
      title: 'Memory Usage Warning',
      description: 'Memory usage is above 80%',
      severity: 'high',
      status: 'acknowledged',
      source: 'prometheus',
      timestamp: '2025-08-16T07:25:00Z',
      labels: { service: 'database' },
      tenantId: 'tenant-1',
      assignee: 'john.doe'
    },
    {
      id: 'alert-3',
      title: 'Disk Space Low',
      description: 'Disk space is below 10%',
      severity: 'medium',
      status: 'resolved',
      source: 'prometheus',
      timestamp: '2025-08-16T07:20:00Z',
      labels: { service: 'storage' },
      tenantId: 'tenant-1'
    }
  ]

  beforeEach(() => {
    mockOnAlertClick.mockClear()
    mockOnAcknowledge.mockClear()
    mockOnResolve.mockClear()
    mockOnLoadMore.mockClear()
  })

  it('renders list of alerts', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    expect(screen.getByText('Memory Usage Warning')).toBeInTheDocument()
    expect(screen.getByText('Disk Space Low')).toBeInTheDocument()
  })

  it('shows loading skeleton when loading', () => {
    render(
      <AlertList
        alerts={[]}
        loading={true}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    // Should show skeleton loading cards
    const skeletonElements = screen.getAllByRole('generic')
    expect(skeletonElements.length).toBeGreaterThan(0)
  })

  it('shows empty state when no alerts', () => {
    render(
      <AlertList
        alerts={[]}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('No alerts found')).toBeInTheDocument()
    expect(screen.getByText('All systems are running smoothly.')).toBeInTheDocument()
  })

  it('groups alerts by status when groupBy is status', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        groupBy="status"
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Active (1)')).toBeInTheDocument()
    expect(screen.getByText('Acknowledged (1)')).toBeInTheDocument()
    expect(screen.getByText('Resolved (1)')).toBeInTheDocument()
  })

  it('groups alerts by severity when groupBy is severity', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        groupBy="severity"
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Critical (1)')).toBeInTheDocument()
    expect(screen.getByText('High (1)')).toBeInTheDocument()
    expect(screen.getByText('Medium (1)')).toBeInTheDocument()
  })

  it('sorts alerts by timestamp in descending order by default', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const alertTitles = screen.getAllByRole('heading', { level: 3 })
    expect(alertTitles[0]).toHaveTextContent('High CPU Usage') // Most recent
    expect(alertTitles[1]).toHaveTextContent('Memory Usage Warning')
    expect(alertTitles[2]).toHaveTextContent('Disk Space Low') // Oldest
  })

  it('sorts alerts by severity when sortBy is severity', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        sortBy="severity"
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const alertTitles = screen.getAllByRole('heading', { level: 3 })
    expect(alertTitles[0]).toHaveTextContent('High CPU Usage') // Critical first
    expect(alertTitles[1]).toHaveTextContent('Memory Usage Warning') // High second
    expect(alertTitles[2]).toHaveTextContent('Disk Space Low') // Medium last
  })

  it('shows load more button when hasMore is true', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        hasMore={true}
        onLoadMore={mockOnLoadMore}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Load more alerts')).toBeInTheDocument()
  })

  it('calls onLoadMore when load more button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <AlertList
        alerts={mockAlerts}
        hasMore={true}
        onLoadMore={mockOnLoadMore}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const loadMoreButton = screen.getByText('Load more alerts')
    await user.click(loadMoreButton)

    expect(mockOnLoadMore).toHaveBeenCalledTimes(1)
  })

  it('shows loading state on load more button when loadingMore is true', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        hasMore={true}
        loadingMore={true}
        onLoadMore={mockOnLoadMore}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const loadMoreButton = screen.getByText('Loading more...')
    expect(loadMoreButton).toBeDisabled()
  })

  it('passes through alert actions to AlertCard components', async () => {
    const user = userEvent.setup()
    render(
      <AlertList
        alerts={[mockAlerts[0]]} // Only active alert
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const acknowledgeButton = screen.getByText('Acknowledge')
    await user.click(acknowledgeButton)

    expect(mockOnAcknowledge).toHaveBeenCalledWith('alert-1')
  })

  it('shows compact view when compact prop is true', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        compact={true}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    // Check that alerts are rendered in compact mode
    const alertCards = screen.getAllByRole('article')
    alertCards.forEach(card => {
      expect(card).toHaveClass('p-3') // Compact padding
    })
  })

  it('filters alerts by status when showResolved is false', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        showResolved={false}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    expect(screen.getByText('Memory Usage Warning')).toBeInTheDocument()
    expect(screen.queryByText('Disk Space Low')).not.toBeInTheDocument()
  })

  it('shows alert count in header', () => {
    render(
      <AlertList
        alerts={mockAlerts}
        showHeader={true}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Alerts (3)')).toBeInTheDocument()
  })

  it('handles empty alert list gracefully', () => {
    render(
      <AlertList
        alerts={[]}
        onAlertClick={mockOnAlertClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('No alerts found')).toBeInTheDocument()
  })
})