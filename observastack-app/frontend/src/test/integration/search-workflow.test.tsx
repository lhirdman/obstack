import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Search } from '../../views/Search'
import { AuthProvider } from '../../auth/AuthContext'
import { ToastProvider } from '../../components/ui/Toast'

// Mock API client
const mockApiClient = {
  search: vi.fn(),
  getSearchHistory: vi.fn(),
  saveSearch: vi.fn()
}

vi.mock('../../lib/api-client', () => ({
  apiClient: mockApiClient
}))

// Mock authentication
const mockAuth = {
  user: {
    id: 'user-1',
    username: 'testuser',
    email: 'test@example.com',
    tenantId: 'tenant-1',
    roles: ['viewer']
  },
  token: 'mock-jwt-token',
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn()
}

vi.mock('../../auth/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => mockAuth
}))

// Test wrapper component
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  )
}

describe('Search Workflow Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock responses
    mockApiClient.search.mockResolvedValue({
      items: [
        {
          id: 'log-1',
          timestamp: '2025-08-16T07:30:00Z',
          source: 'logs',
          service: 'api-server',
          correlationId: 'trace-123',
          content: {
            message: 'Authentication failed for user john.doe',
            level: 'error',
            labels: { user_id: 'user-456' },
            fields: {}
          }
        }
      ],
      stats: {
        matched: 1,
        scanned: 100,
        latencyMs: 45,
        sources: { logs: 1 }
      },
      facets: []
    })

    mockApiClient.getSearchHistory.mockResolvedValue([])
  })

  it('completes full search workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User enters search query
    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'authentication failed')

    // 2. User submits search
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 3. Verify API call was made
    await waitFor(() => {
      expect(mockApiClient.search).toHaveBeenCalledWith(
        expect.objectContaining({
          freeText: 'authentication failed',
          type: 'all',
          tenantId: 'tenant-1'
        })
      )
    })

    // 4. Verify results are displayed
    await waitFor(() => {
      expect(screen.getByText('Authentication failed for user john.doe')).toBeInTheDocument()
      expect(screen.getByText('1 results')).toBeInTheDocument()
      expect(screen.getByText('45ms')).toBeInTheDocument()
    })

    // 5. User clicks on correlation link
    const correlationLink = screen.getByText('Correlated')
    await user.click(correlationLink)

    // 6. Verify correlation search is triggered
    await waitFor(() => {
      expect(mockApiClient.search).toHaveBeenCalledWith(
        expect.objectContaining({
          correlationId: 'trace-123'
        })
      )
    })
  })

  it('handles search with filters workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User opens filters
    const filtersButton = screen.getByRole('button', { name: /filters/i })
    await user.click(filtersButton)

    // 2. User adds a filter
    const addFilterButton = screen.getByText('Add Filter')
    await user.click(addFilterButton)

    // 3. User configures filter
    const fieldSelect = screen.getByDisplayValue('')
    await user.selectOptions(fieldSelect, 'level')

    const valueInput = screen.getByDisplayValue('')
    await user.type(valueInput, 'error')

    // 4. User applies filters and searches
    const applyButton = screen.getByText('Apply')
    await user.click(applyButton)

    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'failed')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 5. Verify search includes filters
    await waitFor(() => {
      expect(mockApiClient.search).toHaveBeenCalledWith(
        expect.objectContaining({
          freeText: 'failed',
          filters: [
            { field: 'level', operator: 'equals', value: 'error' }
          ]
        })
      )
    })
  })

  it('handles time range selection workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User changes time range
    const timeRangeSelect = screen.getByDisplayValue('Last 1 hour')
    await user.selectOptions(timeRangeSelect, 'now-24h')

    // 2. User performs search
    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'error')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 3. Verify search includes time range
    await waitFor(() => {
      expect(mockApiClient.search).toHaveBeenCalledWith(
        expect.objectContaining({
          timeRange: {
            from: 'now-24h',
            to: 'now'
          }
        })
      )
    })
  })

  it('handles search error gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock API error
    mockApiClient.search.mockRejectedValue(new Error('Search service unavailable'))
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User performs search
    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'test query')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 2. Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText('Search failed')).toBeInTheDocument()
      expect(screen.getByText('Search service unavailable')).toBeInTheDocument()
    })

    // 3. User can retry
    const retryButton = screen.getByText('Try Again')
    await user.click(retryButton)

    // 4. Verify retry attempt
    await waitFor(() => {
      expect(mockApiClient.search).toHaveBeenCalledTimes(2)
    })
  })

  it('handles empty search results', async () => {
    const user = userEvent.setup()
    
    // Mock empty results
    mockApiClient.search.mockResolvedValue({
      items: [],
      stats: { matched: 0, scanned: 1000, latencyMs: 25, sources: {} },
      facets: []
    })
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User performs search
    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'nonexistent query')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 2. Verify empty state is shown
    await waitFor(() => {
      expect(screen.getByText('No results found')).toBeInTheDocument()
      expect(screen.getByText('Try adjusting your search terms or filters')).toBeInTheDocument()
    })
  })

  it('handles search type switching', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User changes search type to logs only
    const typeSelect = screen.getByDisplayValue('All Sources')
    await user.selectOptions(typeSelect, 'logs')

    // 2. User performs search
    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'error message')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 3. Verify search type is included
    await waitFor(() => {
      expect(mockApiClient.search).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'logs'
        })
      )
    })
  })

  it('handles search history and saved searches', async () => {
    const user = userEvent.setup()
    
    // Mock search history
    mockApiClient.getSearchHistory.mockResolvedValue([
      {
        id: 'history-1',
        query: 'authentication failed',
        timestamp: '2025-08-16T07:00:00Z',
        type: 'logs'
      }
    ])
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User opens search history
    const historyButton = screen.getByLabelText('Search history')
    await user.click(historyButton)

    // 2. Verify history is displayed
    await waitFor(() => {
      expect(screen.getByText('authentication failed')).toBeInTheDocument()
    })

    // 3. User clicks on history item
    const historyItem = screen.getByText('authentication failed')
    await user.click(historyItem)

    // 4. Verify search form is populated
    expect(screen.getByDisplayValue('authentication failed')).toBeInTheDocument()
  })

  it('handles real-time search updates', async () => {
    const user = userEvent.setup()
    
    // Mock streaming search results
    let searchResolver: (value: any) => void
    mockApiClient.search.mockImplementation(() => {
      return new Promise(resolve => {
        searchResolver = resolve
      })
    })
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    )

    // 1. User starts search
    const searchInput = screen.getByPlaceholderText('Search logs, metrics, and traces...')
    await user.type(searchInput, 'streaming search')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // 2. Verify loading state
    expect(screen.getByText('Searching...')).toBeInTheDocument()

    // 3. Simulate streaming results
    searchResolver!({
      items: [
        {
          id: 'stream-1',
          timestamp: '2025-08-16T07:30:00Z',
          source: 'logs',
          service: 'stream-service',
          content: {
            message: 'Streaming result 1',
            level: 'info',
            labels: {},
            fields: {}
          }
        }
      ],
      stats: { matched: 1, scanned: 50, latencyMs: 100, sources: { logs: 1 } },
      facets: []
    })

    // 4. Verify results are displayed
    await waitFor(() => {
      expect(screen.getByText('Streaming result 1')).toBeInTheDocument()
    })
  })
})