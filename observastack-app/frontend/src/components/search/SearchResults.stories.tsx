import type { Meta, StoryObj } from '@storybook/react'
import { SearchResults } from './SearchResults'
import { SearchResult, SearchItem, LogItem, MetricItem, TraceItem } from '../../types'

const meta: Meta<typeof SearchResults> = {
  title: 'Search/SearchResults',
  component: SearchResults,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Display search results with source identification, cross-signal navigation, and result statistics.'
      }
    }
  },
  argTypes: {
    onResultClick: { action: 'result-click' },
    onCorrelationClick: { action: 'correlation-click' },
    loading: { control: 'boolean' }
  }
}

export default meta
type Story = StoryObj<typeof SearchResults>

// Mock data
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
      user_id: 'user-456',
      endpoint: '/api/login'
    },
    fields: {
      ip_address: '192.168.1.100',
      user_agent: 'Mozilla/5.0'
    }
  } as LogItem
}

const mockMetricItem: SearchItem = {
  id: 'metric-1',
  timestamp: '2025-08-16T07:30:00Z',
  source: 'metrics',
  service: 'api-server',
  content: {
    name: 'http_requests_total',
    value: 1250,
    unit: 'requests',
    type: 'counter',
    labels: {
      method: 'POST',
      status: '200',
      endpoint: '/api/users'
    }
  } as MetricItem
}

const mockTraceItem: SearchItem = {
  id: 'trace-1',
  timestamp: '2025-08-16T07:30:00Z',
  source: 'traces',
  service: 'api-server',
  correlationId: 'trace-123',
  content: {
    traceId: 'trace-123',
    spanId: 'span-456',
    operationName: 'POST /api/login',
    duration: 150000,
    status: 'error',
    tags: {
      'http.method': 'POST',
      'http.status_code': '401',
      'error': 'true'
    }
  } as TraceItem
}

const mockResults: SearchResult = {
  items: [mockLogItem, mockMetricItem, mockTraceItem],
  stats: {
    matched: 3,
    scanned: 1000,
    latencyMs: 45,
    sources: {
      logs: 1,
      metrics: 1,
      traces: 1
    }
  },
  facets: [
    {
      field: 'service',
      values: [
        { value: 'api-server', count: 2 },
        { value: 'auth-service', count: 1 }
      ]
    }
  ]
}

export const Default: Story = {
  args: {
    results: mockResults,
    loading: false
  }
}

export const Loading: Story = {
  args: {
    results: { items: [], stats: { matched: 0, scanned: 0, latencyMs: 0, sources: {} }, facets: [] },
    loading: true
  }
}

export const Empty: Story = {
  args: {
    results: { items: [], stats: { matched: 0, scanned: 1000, latencyMs: 25, sources: {} }, facets: [] },
    loading: false
  }
}

export const LogsOnly: Story = {
  args: {
    results: {
      items: [mockLogItem],
      stats: {
        matched: 1,
        scanned: 500,
        latencyMs: 30,
        sources: { logs: 1 }
      },
      facets: []
    },
    loading: false
  }
}

export const LargeResultSet: Story = {
  args: {
    results: {
      items: Array.from({ length: 10 }, (_, i) => ({
        ...mockLogItem,
        id: `log-${i}`,
        content: {
          ...mockLogItem.content,
          message: `Log message ${i + 1}: ${(mockLogItem.content as LogItem).message}`
        }
      })),
      stats: {
        matched: 10,
        scanned: 5000,
        latencyMs: 120,
        sources: { logs: 10 }
      },
      facets: [],
      nextToken: 'next-page-token'
    },
    loading: false
  }
}