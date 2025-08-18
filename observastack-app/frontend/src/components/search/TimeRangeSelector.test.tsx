import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TimeRangeSelector } from './TimeRangeSelector'
import { TimeRange } from '../../types'

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn((date, formatStr) => {
    if (formatStr === 'yyyy-MM-dd\'T\'HH:mm') {
      return '2025-08-16T07:30'
    }
    return '2025-08-16T07:30:00Z'
  }),
  parseISO: vi.fn((str) => new Date(str)),
  isValid: vi.fn(() => true),
  subHours: vi.fn((date, hours) => new Date(Date.now() - hours * 60 * 60 * 1000)),
  subDays: vi.fn((date, days) => new Date(Date.now() - days * 24 * 60 * 60 * 1000)),
  subWeeks: vi.fn((date, weeks) => new Date(Date.now() - weeks * 7 * 24 * 60 * 60 * 1000))
}))

describe('TimeRangeSelector', () => {
  const mockOnTimeRangeChange = vi.fn()

  const defaultTimeRange: TimeRange = {
    from: 'now-1h',
    to: 'now'
  }

  beforeEach(() => {
    mockOnTimeRangeChange.mockClear()
  })

  it('renders with default time range', () => {
    render(
      <TimeRangeSelector
        timeRange={defaultTimeRange}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    expect(screen.getByDisplayValue('Last 1 hour')).toBeInTheDocument()
  })

  it('shows quick time range options', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={defaultTimeRange}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const select = screen.getByDisplayValue('Last 1 hour')
    await user.click(select)

    expect(screen.getByText('Last 15 minutes')).toBeInTheDocument()
    expect(screen.getByText('Last 1 hour')).toBeInTheDocument()
    expect(screen.getByText('Last 24 hours')).toBeInTheDocument()
    expect(screen.getByText('Last 7 days')).toBeInTheDocument()
    expect(screen.getByText('Custom range')).toBeInTheDocument()
  })

  it('changes time range when quick option is selected', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={defaultTimeRange}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const select = screen.getByDisplayValue('Last 1 hour')
    await user.selectOptions(select, 'now-24h')

    expect(mockOnTimeRangeChange).toHaveBeenCalledWith({
      from: 'now-24h',
      to: 'now'
    })
  })

  it('shows custom date inputs when custom range is selected', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={{ from: '2025-08-15T00:00:00Z', to: '2025-08-16T00:00:00Z' }}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const select = screen.getByDisplayValue('Custom range')
    expect(select).toBeInTheDocument()

    // Should show date/time inputs
    expect(screen.getByLabelText('From')).toBeInTheDocument()
    expect(screen.getByLabelText('To')).toBeInTheDocument()
  })

  it('updates custom from date when changed', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={{ from: '2025-08-15T00:00:00Z', to: '2025-08-16T00:00:00Z' }}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const fromInput = screen.getByLabelText('From')
    await user.clear(fromInput)
    await user.type(fromInput, '2025-08-14T12:00')

    expect(mockOnTimeRangeChange).toHaveBeenCalledWith({
      from: '2025-08-14T12:00:00Z',
      to: '2025-08-16T00:00:00Z'
    })
  })

  it('updates custom to date when changed', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={{ from: '2025-08-15T00:00:00Z', to: '2025-08-16T00:00:00Z' }}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const toInput = screen.getByLabelText('To')
    await user.clear(toInput)
    await user.type(toInput, '2025-08-16T18:00')

    expect(mockOnTimeRangeChange).toHaveBeenCalledWith({
      from: '2025-08-15T00:00:00Z',
      to: '2025-08-16T18:00:00Z'
    })
  })

  it('validates that from date is before to date', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={{ from: '2025-08-15T00:00:00Z', to: '2025-08-16T00:00:00Z' }}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const fromInput = screen.getByLabelText('From')
    await user.clear(fromInput)
    await user.type(fromInput, '2025-08-17T12:00')

    // Should show validation error
    expect(screen.getByText('From date must be before to date')).toBeInTheDocument()
  })

  it('shows relative time description for quick ranges', () => {
    render(
      <TimeRangeSelector
        timeRange={defaultTimeRange}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    expect(screen.getByText(/Showing data from/)).toBeInTheDocument()
  })

  it('applies quick range when Apply button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={defaultTimeRange}
        onTimeRangeChange={mockOnTimeRangeChange}
        showApplyButton={true}
      />
    )

    const select = screen.getByDisplayValue('Last 1 hour')
    await user.selectOptions(select, 'now-15m')

    const applyButton = screen.getByText('Apply')
    await user.click(applyButton)

    expect(mockOnTimeRangeChange).toHaveBeenCalledWith({
      from: 'now-15m',
      to: 'now'
    })
  })

  it('resets to original range when Cancel is clicked', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={defaultTimeRange}
        onTimeRangeChange={mockOnTimeRangeChange}
        showApplyButton={true}
      />
    )

    const select = screen.getByDisplayValue('Last 1 hour')
    await user.selectOptions(select, 'now-24h')

    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)

    // Should reset to original range
    expect(screen.getByDisplayValue('Last 1 hour')).toBeInTheDocument()
  })

  it('handles invalid date input gracefully', async () => {
    const user = userEvent.setup()
    render(
      <TimeRangeSelector
        timeRange={{ from: '2025-08-15T00:00:00Z', to: '2025-08-16T00:00:00Z' }}
        onTimeRangeChange={mockOnTimeRangeChange}
      />
    )

    const fromInput = screen.getByLabelText('From')
    await user.clear(fromInput)
    await user.type(fromInput, 'invalid-date')

    // Should show validation error
    expect(screen.getByText('Invalid date format')).toBeInTheDocument()
  })
})