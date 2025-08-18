import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Alerts } from '../../views/Alerts'
import { AuthProvider } from '../../auth/AuthContext'
import { ToastProvider } from '../../components/ui/Toast'
import { Alert } from '../../types/alerts'

// Mock API client
const mockApiClient = {
  getAlerts: vi.fn(),
  acknowledgeAlert: vi.fn(),
  resolveAlert: vi.fn(),
  assignAlert: vi.fn(),
  getAlertDetail: vi.fn()
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
    roles: ['operator']
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

describe('Alert Management Workflow Integration', () => {
  const mockAlerts: Alert[] = [
    {
      id: 'alert-1',
      title: 'High CPU Usage',
      description: 'CPU usage is above 90% for the last 5 minutes',
      severity: 'critical',
      status: 'active',
      source: 'prometheus',
      timestamp: '2025-08-16T07:30:00Z',
      labels: {
        service: 'api-server',
        instance: 'api-01'
      },
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
      labels: {
        service: 'database',
        instance: 'db-01'
      },
      tenantId: 'tenant-1',
      assignee: 'john.doe'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock responses
    mockApiClient.getAlerts.mockResolvedValue({
      alerts: mockAlerts,
      total: 2,
      hasMore: false
    })

    mockApiClient.acknowledgeAlert.mockResolvedValue({ success: true })
    mockApiClient.resolveAlert.mockResolvedValue({ success: true })
    mockApiClient.assignAlert.mockResolvedValue({ success: true })
  })

  it('completes alert acknowledgment workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User acknowledges an alert
    const acknowledgeButton = screen.getByText('Acknowledge')
    await user.click(acknowledgeButton)

    // 3. Verify API call was made
    await waitFor(() => {
      expect(mockApiClient.acknowledgeAlert).toHaveBeenCalledWith('alert-1')
    })

    // 4. Verify success toast is shown
    await waitFor(() => {
      expect(screen.getByText('Alert acknowledged successfully')).toBeInTheDocument()
    })

    // 5. Verify alert list is refreshed
    expect(mockApiClient.getAlerts).toHaveBeenCalledTimes(2) // Initial load + refresh
  })

  it('completes alert resolution workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User resolves an alert
    const resolveButton = screen.getByText('Resolve')
    await user.click(resolveButton)

    // 3. Verify confirmation dialog appears
    expect(screen.getByText('Resolve Alert')).toBeInTheDocument()
    expect(screen.getByText('Are you sure you want to resolve this alert?')).toBeInTheDocument()

    // 4. User confirms resolution
    const confirmButton = screen.getByText('Confirm')
    await user.click(confirmButton)

    // 5. Verify API call was made
    await waitFor(() => {
      expect(mockApiClient.resolveAlert).toHaveBeenCalledWith('alert-1')
    })

    // 6. Verify success feedback
    await waitFor(() => {
      expect(screen.getByText('Alert resolved successfully')).toBeInTheDocument()
    })
  })

  it('handles alert filtering workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User opens filters
    const filtersButton = screen.getByText('Filters')
    await user.click(filtersButton)

    // 3. User selects severity filter
    const severityFilter = screen.getByLabelText('Severity')
    await user.selectOptions(severityFilter, 'critical')

    // 4. User applies filters
    const applyButton = screen.getByText('Apply Filters')
    await user.click(applyButton)

    // 5. Verify filtered API call
    await waitFor(() => {
      expect(mockApiClient.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          filters: {
            severity: 'critical'
          }
        })
      )
    })
  })

  it('handles alert sorting workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User changes sort order
    const sortSelect = screen.getByLabelText('Sort by')
    await user.selectOptions(sortSelect, 'severity')

    // 3. Verify sorted API call
    await waitFor(() => {
      expect(mockApiClient.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          sortBy: 'severity',
          sortOrder: 'desc'
        })
      )
    })
  })

  it('handles alert detail view workflow', async () => {
    const user = userEvent.setup()
    
    // Mock alert detail response
    mockApiClient.getAlertDetail.mockResolvedValue({
      ...mockAlerts[0],
      history: [
        {
          timestamp: '2025-08-16T07:30:00Z',
          action: 'created',
          user: 'system'
        }
      ],
      relatedAlerts: []
    })
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User clicks on alert to view details
    const alertCard = screen.getByText('High CPU Usage')
    await user.click(alertCard)

    // 3. Verify detail API call
    await waitFor(() => {
      expect(mockApiClient.getAlertDetail).toHaveBeenCalledWith('alert-1')
    })

    // 4. Verify detail view is shown
    await waitFor(() => {
      expect(screen.getByText('Alert Details')).toBeInTheDocument()
      expect(screen.getByText('History')).toBeInTheDocument()
    })
  })

  it('handles bulk alert operations workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User selects multiple alerts
    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[0]) // Select first alert
    await user.click(checkboxes[1]) // Select second alert

    // 3. Verify bulk actions appear
    expect(screen.getByText('2 selected')).toBeInTheDocument()
    expect(screen.getByText('Acknowledge Selected')).toBeInTheDocument()
    expect(screen.getByText('Resolve Selected')).toBeInTheDocument()

    // 4. User performs bulk acknowledge
    const bulkAcknowledgeButton = screen.getByText('Acknowledge Selected')
    await user.click(bulkAcknowledgeButton)

    // 5. Verify bulk API calls
    await waitFor(() => {
      expect(mockApiClient.acknowledgeAlert).toHaveBeenCalledWith('alert-1')
      expect(mockApiClient.acknowledgeAlert).toHaveBeenCalledWith('alert-2')
    })
  })

  it('handles alert assignment workflow', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User opens assignment dialog
    const assignButton = screen.getByLabelText('Assign alert')
    await user.click(assignButton)

    // 3. Verify assignment dialog appears
    expect(screen.getByText('Assign Alert')).toBeInTheDocument()

    // 4. User selects assignee
    const assigneeSelect = screen.getByLabelText('Assign to')
    await user.selectOptions(assigneeSelect, 'jane.doe')

    // 5. User confirms assignment
    const confirmAssignButton = screen.getByText('Assign')
    await user.click(confirmAssignButton)

    // 6. Verify assignment API call
    await waitFor(() => {
      expect(mockApiClient.assignAlert).toHaveBeenCalledWith('alert-1', 'jane.doe')
    })
  })

  it('handles alert error states gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock API error
    mockApiClient.acknowledgeAlert.mockRejectedValue(new Error('Network error'))
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. User tries to acknowledge alert
    const acknowledgeButton = screen.getByText('Acknowledge')
    await user.click(acknowledgeButton)

    // 3. Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText('Failed to acknowledge alert')).toBeInTheDocument()
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })

    // 4. User can retry
    const retryButton = screen.getByText('Retry')
    await user.click(retryButton)

    // 5. Verify retry attempt
    await waitFor(() => {
      expect(mockApiClient.acknowledgeAlert).toHaveBeenCalledTimes(2)
    })
  })

  it('handles real-time alert updates', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for initial alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. Simulate new alert arriving via WebSocket
    const newAlert: Alert = {
      id: 'alert-3',
      title: 'Disk Space Critical',
      description: 'Disk space is below 5%',
      severity: 'critical',
      status: 'active',
      source: 'prometheus',
      timestamp: '2025-08-16T07:35:00Z',
      labels: { service: 'storage' },
      tenantId: 'tenant-1'
    }

    // Mock updated alerts response
    mockApiClient.getAlerts.mockResolvedValue({
      alerts: [...mockAlerts, newAlert],
      total: 3,
      hasMore: false
    })

    // 3. Trigger refresh (simulating WebSocket update)
    const refreshButton = screen.getByLabelText('Refresh alerts')
    await user.click(refreshButton)

    // 4. Verify new alert appears
    await waitFor(() => {
      expect(screen.getByText('Disk Space Critical')).toBeInTheDocument()
    })
  })

  it('handles alert pagination workflow', async () => {
    const user = userEvent.setup()
    
    // Mock paginated response
    mockApiClient.getAlerts.mockResolvedValue({
      alerts: mockAlerts,
      total: 50,
      hasMore: true
    })
    
    render(
      <TestWrapper>
        <Alerts />
      </TestWrapper>
    )

    // 1. Wait for alerts to load
    await waitFor(() => {
      expect(screen.getByText('High CPU Usage')).toBeInTheDocument()
    })

    // 2. Verify pagination controls
    expect(screen.getByText('Load more alerts')).toBeInTheDocument()
    expect(screen.getByText('Showing 2 of 50 alerts')).toBeInTheDocument()

    // 3. User loads more alerts
    const loadMoreButton = screen.getByText('Load more alerts')
    await user.click(loadMoreButton)

    // 4. Verify paginated API call
    await waitFor(() => {
      expect(mockApiClient.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          offset: 2,
          limit: 20
        })
      )
    })
  })
})