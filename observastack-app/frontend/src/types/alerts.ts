/**
 * Alert-specific type definitions for the frontend
 */

// Alert Models
export interface Alert {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  title: string
  description: string
  source: 'prometheus' | 'loki' | 'tempo' | 'opensearch' | 'external'
  timestamp: string
  status: 'active' | 'acknowledged' | 'resolved' | 'silenced'
  assignee?: string
  tenantId: string
  labels: Record<string, string>
  annotations: Record<string, string>
  fingerprint: string
  generatorUrl?: string
  silenceId?: string
  startsAt: string
  endsAt?: string
  updatedAt: string
}

export interface AlertGroup {
  id: string
  alerts: Alert[]
  commonLabels: Record<string, string>
  groupKey: string
  status: 'active' | 'acknowledged' | 'resolved'
  createdAt: string
  updatedAt: string
}

export interface AlertQuery {
  status?: string[]
  severity?: string[]
  source?: string[]
  assignee?: string
  fromTime?: string
  toTime?: string
  limit?: number
  offset?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface AlertsResponse {
  success: boolean
  message: string
  alerts: Alert[]
  total: number
  groups?: AlertGroup[]
}

export interface AlertActionRequest {
  alertIds: string[]
  action: 'acknowledge' | 'resolve' | 'assign' | 'silence'
  assignee?: string
  comment?: string
  silenceDuration?: string
}

export interface AlertActionResponse {
  success: boolean
  message: string
  affectedAlerts: number
  failedAlerts: string[]
}

export interface AlertStatistics {
  total: number
  byStatus: Record<string, number>
  bySeverity: Record<string, number>
  bySource: Record<string, number>
  resolutionTimeAvg?: number
  mttr?: number
}

export interface Silence {
  id: string
  matchers: Array<{
    name: string
    value: string
    isRegex: string
  }>
  startsAt: string
  endsAt: string
  createdBy: string
  comment: string
  status: 'active' | 'pending' | 'expired'
  createdAt: string
  updatedAt: string
}

export interface SilenceRequest {
  matchers: Array<{
    name: string
    value: string
    isRegex: string
  }>
  startsAt: string
  endsAt: string
  createdBy: string
  comment: string
}

export interface AlertNotificationChannel {
  id: string
  name: string
  type: 'email' | 'slack' | 'webhook' | 'pagerduty' | 'teams'
  config: Record<string, any>
  enabled: boolean
  tenantId: string
  createdAt: string
  updatedAt: string
}

export interface AlertNotificationRule {
  id: string
  name: string
  conditions: Record<string, any>
  channels: string[]
  enabled: boolean
  tenantId: string
  createdAt: string
  updatedAt: string
}

// UI-specific types
export interface AlertFilters {
  status: string[]
  severity: string[]
  source: string[]
  assignee: string
  timeRange: {
    from: string
    to: string
  }
  searchText: string
}

export interface AlertSortConfig {
  field: 'timestamp' | 'severity' | 'title' | 'status'
  direction: 'asc' | 'desc'
}

export interface AlertListViewConfig {
  filters: AlertFilters
  sort: AlertSortConfig
  pagination: {
    page: number
    pageSize: number
  }
  groupBy?: 'none' | 'severity' | 'source' | 'status'
}

export interface AlertDetailViewProps {
  alert: Alert
  onClose: () => void
  onAction: (action: AlertActionRequest) => Promise<void>
}

export interface AlertActionModalProps {
  alerts: Alert[]
  action: 'acknowledge' | 'resolve' | 'assign' | 'silence'
  isOpen: boolean
  onClose: () => void
  onConfirm: (request: AlertActionRequest) => Promise<void>
}

// Severity and status mappings for UI
export const SEVERITY_COLORS = {
  critical: 'error',
  high: 'warning', 
  medium: 'warning',
  low: 'info',
  info: 'default'
} as const

export const STATUS_COLORS = {
  active: 'error',
  acknowledged: 'warning',
  resolved: 'success',
  silenced: 'default'
} as const

export const SEVERITY_ICONS = {
  critical: '🔴',
  high: '🟠', 
  medium: '🟡',
  low: '🔵',
  info: '⚪'
} as const

export const STATUS_ICONS = {
  active: '🚨',
  acknowledged: '👀',
  resolved: '✅',
  silenced: '🔇'
} as const