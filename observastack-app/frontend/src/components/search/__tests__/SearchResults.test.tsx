import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchResults } from '../SearchResults'
import { SearchResult, SearchItem, LogItem } from '../../../types'

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn(() => 'Aug 16, 07:30:00.000'),
  parseISO: vi.fn((str) => new Date(str))
}))

describe('SearchResults', () => {
  const mockOnResultClick = vi.fn()
  const mockOnCorrelationClick = vi.fn()

  const mockLogItem: SearchItem = {
    id: 'log-1',
    timestamp: '2025-08-16T07:30:00Z',
    source: 'logs',
    service: 'api-server',
    correlationId: 'trace-123',
    content: {
      message: 'Authentication failed for user',
      level: 'error',
      labels: {
        user_id: 'user-456'
      },
      fields: {}
    } as LogItem
  }

  const mockResults: SearchResult = {
    items: [mockLogItem],
    stats: {
      matched: 1,
      scanned: 100,
      latencyMs: 45,
      sources: {
        logs: 1
      }
    },
    facets: []
  }

  beforeEach(() => {
    mockOnResultClick.mockClear()
    mockOnCorrelationClick.mockClear()
  })

  it('renders search results with statistics', () => {
    render(
      <SearchResults
        results={mockResults}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    expect(screen.getByText('1 results')).toBeInTheDocument()
    expect(screen.getByText('45ms')).toBeInTheDocument()
    expect(screen.getByText('logs: 1')).toBeInTheDocument()
  })

  it('renders log item correctly', () => {
    render(
      <SearchResults
        results={mockResults}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    expect(screen.getByText('logs')).toBeInTheDocument()
    expect(screen.getByText('api-server')).toBeInTheDocument()
    expect(screen.getByText('Authentication failed for user')).toBeInTheDocument()
    expect(screen.getByText('ERROR')).toBeInTheDocument()
    expect(screen.getByText('Correlated')).toBeInTheDocument()
  })

  it('shows loading skeleton when loading', () => {
    render(
      <SearchResults
        results={{ items: [], stats: { matched: 0, scanned: 0, latencyMs: 0, sources: {} }, facets: [] }}
        loading={true}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    // Check for loading skeleton elements
    const skeletonElements = screen.getAllByRole('generic')
    expect(skeletonElements.length).toBeGreaterThan(0)
  })

  it('shows empty state when no results', () => {
    render(
      <SearchResults
        results={{ items: [], stats: { matched: 0, scanned: 100, latencyMs: 25, sources: {} }, facets: [] }}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    expect(screen.getByText('No results found')).toBeInTheDocument()
    expect(screen.getByText('Try adjusting your search terms or filters to find what you\'re looking for.')).toBeInTheDocument()
  })

  it('calls onResultClick when result is clicked', async () => {
    const user = userEvent.setup()
    render(
      <SearchResults
        results={mockResults}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    const resultCard = screen.getByText('Authentication failed for user').closest('div')
    if (resultCard) {
      await user.click(resultCard)
      expect(mockOnResultClick).toHaveBeenCalledWith(mockLogItem)
    }
  })

  it('calls onCorrelationClick when correlation link is clicked', async () => {
    const user = userEvent.setup()
    render(
      <SearchResults
        results={mockResults}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    const correlationLink = screen.getByText('Correlated')
    await user.click(correlationLink)
    
    expect(mockOnCorrelationClick).toHaveBeenCalledWith('trace-123')
  })

  it('shows load more button when nextToken is present', () => {
    const resultsWithNextToken = {
      ...mockResults,
      nextToken: 'next-page-token'
    }
    
    render(
      <SearchResults
        results={resultsWithNextToken}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    expect(screen.getByText('Load more results')).toBeInTheDocument()
  })

  it('formats large numbers in statistics', () => {
    const largeResults: SearchResult = {
      items: [],
      stats: {
        matched: 1500,
        scanned: 1500000,
        latencyMs: 1200,
        sources: {
          logs: 1500
        }
      },
      facets: []
    }
    
    render(
      <SearchResults
        results={largeResults}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    expect(screen.getByText('1.5K results')).toBeInTheDocument()
    expect(screen.getByText('from 1.5M scanned')).toBeInTheDocument()
    expect(screen.getByText('1.20s')).toBeInTheDocument()
  })

  it('handles missing correlation ID gracefully', () => {
    const { correlationId, ...itemWithoutCorrelation } = mockLogItem
    
    const resultsWithoutCorrelation: SearchResult = {
      ...mockResults,
      items: [itemWithoutCorrelation as SearchItem]
    }
    
    render(
      <SearchResults
        results={resultsWithoutCorrelation}
        onResultClick={mockOnResultClick}
        onCorrelationClick={mockOnCorrelationClick}
      />
    )
    
    expect(screen.queryByText('Correlated')).not.toBeInTheDocument()
  })
})