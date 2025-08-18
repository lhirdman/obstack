import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CostSummaryCards } from './CostSummaryCards'
import { CostSummary } from '../../types/costs'

// Mock chart library
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
}))

describe('CostSummaryCards', () => {
  const mockCostSummary: CostSummary = {
    totalCost: 1250.75,
    previousPeriodCost: 1100.50,
    trend: 'up',
    trendPercentage: 13.6,
    breakdown: {
      compute: 750.25,
      storage: 300.50,
      network: 150.00,
      other: 50.00
    },
    topNamespaces: [
      { name: 'production', cost: 800.25, percentage: 64.0 },
      { name: 'staging', cost: 250.50, percentage: 20.0 },
      { name: 'development', cost: 200.00, percentage: 16.0 }
    ],
    alerts: {
      budgetExceeded: 2,
      anomaliesDetected: 1,
      optimizationOpportunities: 5
    },
    efficiency: {
      cpuUtilization: 65.5,
      memoryUtilization: 78.2,
      storageUtilization: 82.1,
      overallScore: 75.3
    }
  }

  it('renders total cost correctly', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    expect(screen.getByText('$1,250.75')).toBeInTheDocument()
    expect(screen.getByText('Total Cost')).toBeInTheDocument()
  })

  it('shows cost trend with percentage', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    expect(screen.getByText('↗ 13.6%')).toBeInTheDocument()
    expect(screen.getByText('vs previous period')).toBeInTheDocument()
  })

  it('displays cost breakdown by category', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    expect(screen.getByText('Compute')).toBeInTheDocument()
    expect(screen.getByText('$750.25')).toBeInTheDocument()
    expect(screen.getByText('Storage')).toBeInTheDocument()
    expect(screen.getByText('$300.50')).toBeInTheDocument()
    expect(screen.getByText('Network')).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
  })

  it('shows top namespaces with costs and percentages', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    expect(screen.getByText('production')).toBeInTheDocument()
    expect(screen.getByText('$800.25')).toBeInTheDocument()
    expect(screen.getByText('64.0%')).toBeInTheDocument()
    
    expect(screen.getByText('staging')).toBeInTheDocument()
    expect(screen.getByText('$250.50')).toBeInTheDocument()
    expect(screen.getByText('20.0%')).toBeInTheDocument()
  })

  it('displays alert counts', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    expect(screen.getByText('2')).toBeInTheDocument() // Budget exceeded
    expect(screen.getByText('Budget Alerts')).toBeInTheDocument()
    
    expect(screen.getByText('1')).toBeInTheDocument() // Anomalies
    expect(screen.getByText('Anomalies')).toBeInTheDocument()
    
    expect(screen.getByText('5')).toBeInTheDocument() // Optimization opportunities
    expect(screen.getByText('Optimization Opportunities')).toBeInTheDocument()
  })

  it('shows efficiency metrics', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    expect(screen.getByText('75.3%')).toBeInTheDocument()
    expect(screen.getByText('Overall Efficiency')).toBeInTheDocument()
    
    expect(screen.getByText('65.5%')).toBeInTheDocument() // CPU
    expect(screen.getByText('78.2%')).toBeInTheDocument() // Memory
    expect(screen.getByText('82.1%')).toBeInTheDocument() // Storage
  })

  it('applies correct trend styling for upward trend', () => {
    render(<CostSummaryCards costSummary={mockCostSummary} />)

    const trendElement = screen.getByText('↗ 13.6%')
    expect(trendElement).toHaveClass('text-red-600') // Upward trend is bad for costs
  })

  it('applies correct trend styling for downward trend', () => {
    const downwardTrendSummary = {
      ...mockCostSummary,
      trend: 'down' as const,
      trendPercentage: -8.5
    }

    render(<CostSummaryCards costSummary={downwardTrendSummary} />)

    const trendElement = screen.getByText('↘ 8.5%')
    expect(trendElement).toHaveClass('text-green-600') // Downward trend is good for costs
  })

  it('shows stable trend correctly', () => {
    const stableTrendSummary = {
      ...mockCostSummary,
      trend: 'stable' as const,
      trendPercentage: 0.2
    }

    render(<CostSummaryCards costSummary={stableTrendSummary} />)

    const trendElement = screen.getByText('→ 0.2%')
    expect(trendElement).toHaveClass('text-gray-600')
  })

  it('handles loading state', () => {
    render(<CostSummaryCards costSummary={null} loading={true} />)

    // Should show skeleton loading cards
    const skeletonElements = screen.getAllByRole('generic')
    expect(skeletonElements.length).toBeGreaterThan(0)
  })

  it('handles error state', () => {
    render(<CostSummaryCards costSummary={null} error="Failed to load cost data" />)

    expect(screen.getByText('Error loading cost data')).toBeInTheDocument()
    expect(screen.getByText('Failed to load cost data')).toBeInTheDocument()
  })

  it('formats large numbers correctly', () => {
    const largeCostSummary = {
      ...mockCostSummary,
      totalCost: 1500000.75,
      breakdown: {
        compute: 1200000.25,
        storage: 200000.50,
        network: 80000.00,
        other: 20000.00
      }
    }

    render(<CostSummaryCards costSummary={largeCostSummary} />)

    expect(screen.getByText('$1.50M')).toBeInTheDocument()
    expect(screen.getByText('$1.20M')).toBeInTheDocument()
    expect(screen.getByText('$200.00K')).toBeInTheDocument()
  })

  it('shows efficiency score with appropriate color coding', () => {
    const { rerender } = render(<CostSummaryCards costSummary={mockCostSummary} />)

    // Good efficiency (75.3%)
    let efficiencyElement = screen.getByText('75.3%')
    expect(efficiencyElement).toHaveClass('text-green-600')

    // Poor efficiency
    const poorEfficiencySummary = {
      ...mockCostSummary,
      efficiency: {
        ...mockCostSummary.efficiency,
        overallScore: 45.2
      }
    }

    rerender(<CostSummaryCards costSummary={poorEfficiencySummary} />)

    efficiencyElement = screen.getByText('45.2%')
    expect(efficiencyElement).toHaveClass('text-red-600')
  })

  it('handles missing optional data gracefully', () => {
    const minimalSummary: CostSummary = {
      totalCost: 1000.00,
      previousPeriodCost: 950.00,
      trend: 'up',
      trendPercentage: 5.3,
      breakdown: {
        compute: 600.00,
        storage: 300.00,
        network: 100.00,
        other: 0
      },
      topNamespaces: [],
      alerts: {
        budgetExceeded: 0,
        anomaliesDetected: 0,
        optimizationOpportunities: 0
      },
      efficiency: {
        cpuUtilization: 0,
        memoryUtilization: 0,
        storageUtilization: 0,
        overallScore: 0
      }
    }

    render(<CostSummaryCards costSummary={minimalSummary} />)

    expect(screen.getByText('$1,000.00')).toBeInTheDocument()
    expect(screen.getByText('No namespaces found')).toBeInTheDocument()
  })
})