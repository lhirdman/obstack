import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AlertCard } from './AlertCard'
import { Alert } from '../../types/alerts'

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn(() => 'Aug 16, 07:30'),
  formatDistanceToNow: vi.fn(() => '2 hours ago'),
  parseISO: vi.fn((str) => new Date(str))
}))

describe('AlertCard', () => {
  const mockOnClick = vi.fn()
  const mockOnAcknowledge = vi.fn()
  const mockOnResolve = vi.fn()

  const mockAlert: Alert = {
    id: 'alert-1',
    title: 'High CPU Usage',
    description: 'CPU usage is above 90% for the last 5 minutes',
    severity: 'high',
    status: 'active',
    source: 'prometheus',
    timestamp: '2025-08-16T07:30:00Z',
    labels: {
      service: 'api-server',
      instance: 'api-01'
    },
    tenantId: 'tenant-1'
  }

  beforeEach(() => {
    mockOnClick.mockClear()
    mockOnAcknowledge.mockClear()
    mockOnResolve.mockClear()
  })

  it('renders alert information correctly', () => {
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    expect(screen.getByText('CPU usage is above 90% for the last 5 minutes')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
    expect(screen.getByText('prometheus')).toBeInTheDocument()
    expect(screen.getByText('2 hours ago')).toBeInTheDocument()
  })

  it('displays alert labels', () => {
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('service: api-server')).toBeInTheDocument()
    expect(screen.getByText('instance: api-01')).toBeInTheDocument()
  })

  it('applies correct severity styling', () => {
    const { rerender } = render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const severityBadge = screen.getByText('HIGH')
    expect(severityBadge).toHaveClass('bg-orange-100', 'text-orange-800')

    // Test critical severity
    rerender(
      <AlertCard
        alert={{ ...mockAlert, severity: 'critical' }}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const criticalBadge = screen.getByText('CRITICAL')
    expect(criticalBadge).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('shows acknowledge button for active alerts', () => {
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Acknowledge')).toBeInTheDocument()
    expect(screen.getByText('Resolve')).toBeInTheDocument()
  })

  it('shows different actions for acknowledged alerts', () => {
    render(
      <AlertCard
        alert={{ ...mockAlert, status: 'acknowledged', assignee: 'john.doe' }}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Assigned to john.doe')).toBeInTheDocument()
    expect(screen.getByText('Resolve')).toBeInTheDocument()
    expect(screen.queryByText('Acknowledge')).not.toBeInTheDocument()
  })

  it('shows resolved status for resolved alerts', () => {
    render(
      <AlertCard
        alert={{ ...mockAlert, status: 'resolved' }}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('RESOLVED')).toBeInTheDocument()
    expect(screen.queryByText('Acknowledge')).not.toBeInTheDocument()
    expect(screen.queryByText('Resolve')).not.toBeInTheDocument()
  })

  it('calls onClick when card is clicked', async () => {
    const user = userEvent.setup()
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const card = screen.getByText('High CPU Usage').closest('div')
    if (card) {
      await user.click(card)
      expect(mockOnClick).toHaveBeenCalledWith(mockAlert)
    }
  })

  it('calls onAcknowledge when acknowledge button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const acknowledgeButton = screen.getByText('Acknowledge')
    await user.click(acknowledgeButton)

    expect(mockOnAcknowledge).toHaveBeenCalledWith(mockAlert.id)
  })

  it('calls onResolve when resolve button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const resolveButton = screen.getByText('Resolve')
    await user.click(resolveButton)

    expect(mockOnResolve).toHaveBeenCalledWith(mockAlert.id)
  })

  it('prevents event bubbling when action buttons are clicked', async () => {
    const user = userEvent.setup()
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    const acknowledgeButton = screen.getByText('Acknowledge')
    await user.click(acknowledgeButton)

    // onClick should not be called when action button is clicked
    expect(mockOnClick).not.toHaveBeenCalled()
    expect(mockOnAcknowledge).toHaveBeenCalledWith(mockAlert.id)
  })

  it('shows compact view when compact prop is true', () => {
    render(
      <AlertCard
        alert={mockAlert}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
        compact={true}
      />
    )

    // In compact mode, description should be truncated or hidden
    const card = screen.getByText('High CPU Usage').closest('div')
    expect(card).toHaveClass('p-3') // Smaller padding in compact mode
  })

  it('handles missing assignee gracefully', () => {
    render(
      <AlertCard
        alert={{ ...mockAlert, status: 'acknowledged' }}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('Acknowledged')).toBeInTheDocument()
    expect(screen.queryByText('Assigned to')).not.toBeInTheDocument()
  })

  it('handles alerts without labels', () => {
    render(
      <AlertCard
        alert={{ ...mockAlert, labels: {} }}
        onClick={mockOnClick}
        onAcknowledge={mockOnAcknowledge}
        onResolve={mockOnResolve}
      />
    )

    expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    // Should not crash when no labels are present
  })
})