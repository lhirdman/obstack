// Core data model interfaces for ObservaStack frontend

// Re-export error types
export * from './errors'

// Re-export alert types
export * from './alerts'

// Re-export cost types
export * from './costs'

// User and Authentication Models
export interface User {
  id: string
  username: string
  email: string
  tenantId: string
  roles: Role[]
  preferences: UserPreferences
}

export interface Role {
  id: string
  name: string
  permissions: Permission[]
}

export interface Permission {
  resource: string
  actions: string[]
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  timezone: string
  defaultTimeRange: TimeRange
  dashboardLayout: Record<string, unknown>
}

// Tenant Models
export interface Tenant {
  id: string
  name: string
  domain: string
  settings: TenantSettings
  dataRetention: RetentionPolicy
}

export interface TenantSettings {
  branding: BrandingSettings
  features: FeatureFlags
  integrations: IntegrationSettings
}

export interface BrandingSettings {
  logo?: string
  primaryColor: string
  secondaryColor: string
  customCss?: string
}

export interface FeatureFlags {
  sso: boolean
  opensearch: boolean
  costInsights: boolean
  alerting: boolean
  customDashboards: boolean
}

export interface IntegrationSettings {
  grafana: GrafanaIntegration
  keycloak: KeycloakIntegration
  alertmanager: AlertmanagerIntegration
}

export interface GrafanaIntegration {
  url: string
  enabled: boolean
  embedAuth: boolean
}

export interface KeycloakIntegration {
  realm: string
  clientId: string
  enabled: boolean
}

export interface AlertmanagerIntegration {
  url: string
  enabled: boolean
  webhookSecret?: string
}

export interface RetentionPolicy {
  logs: number // days
  metrics: number // days
  traces: number // days
  alerts: number // days
}

// Time and Range Models
export interface TimeRange {
  from: string // ISO 8601 timestamp or relative time (e.g., "now-1h")
  to: string // ISO 8601 timestamp or relative time (e.g., "now")
}

// Search Models
export interface SearchQuery {
  freeText: string
  type: 'logs' | 'metrics' | 'traces' | 'all'
  timeRange: TimeRange
  filters: SearchFilter[]
  tenantId: string
  limit?: number
  offset?: number
}

export interface SearchFilter {
  field: string
  operator: 'equals' | 'contains' | 'regex' | 'range' | 'exists'
  value: string | number | boolean | [number, number]
}

export interface SearchResult {
  items: SearchItem[]
  stats: SearchStats
  facets: SearchFacet[]
  nextToken?: string
}

export interface SearchItem {
  id: string
  timestamp: string
  source: 'logs' | 'metrics' | 'traces'
  service: string
  content: LogItem | MetricItem | TraceItem
  correlationId?: string
}

export interface LogItem {
  message: string
  level: 'debug' | 'info' | 'warn' | 'error' | 'fatal'
  labels: Record<string, string>
  fields: Record<string, unknown>
}

export interface MetricItem {
  name: string
  value: number
  unit: string
  labels: Record<string, string>
  type: 'counter' | 'gauge' | 'histogram' | 'summary'
}

export interface TraceItem {
  traceId: string
  spanId: string
  operationName: string
  duration: number
  status: 'ok' | 'error' | 'timeout'
  tags: Record<string, string>
}

export interface SearchStats {
  matched: number
  scanned: number
  latencyMs: number
  sources: Record<string, number>
}

export interface SearchFacet {
  field: string
  values: Array<{
    value: string
    count: number
  }>
}

// Alert Models
export interface Alert {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  source: string
  timestamp: string
  status: 'active' | 'acknowledged' | 'resolved'
  assignee?: string
  tenantId: string
  labels: Record<string, string>
  annotations: Record<string, string>
  fingerprint: string
  generatorUrl?: string
  silenceId?: string
}

export interface AlertGroup {
  id: string
  alerts: Alert[]
  commonLabels: Record<string, string>
  groupKey: string
  status: 'active' | 'acknowledged' | 'resolved'
}

export interface AlertRule {
  id: string
  name: string
  query: string
  condition: string
  threshold: number
  duration: string
  severity: Alert['severity']
  enabled: boolean
  tenantId: string
}

// Insights Models
export interface InsightMetric {
  name: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  recommendation?: string
  severity: 'info' | 'warning' | 'critical'
  timestamp: string
}

export interface CostInsight {
  category: string
  currentCost: number
  projectedCost: number
  savingsOpportunity: number
  currency: string
  period: 'daily' | 'weekly' | 'monthly'
  recommendations: Recommendation[]
  timestamp: string
}

export interface Recommendation {
  id: string
  type: 'rightsizing' | 'scheduling' | 'storage' | 'networking'
  title: string
  description: string
  impact: 'high' | 'medium' | 'low'
  effort: 'high' | 'medium' | 'low'
  estimatedSavings: number
  actionUrl?: string
}

export interface ResourceUtilization {
  resource: string
  current: number
  capacity: number
  utilization: number // percentage
  trend: Array<{
    timestamp: string
    value: number
  }>
  recommendations: string[]
}

// API Response Models
export interface ApiResponse<T = unknown> {
  data: T
  success: boolean
  message?: string
  timestamp: string
}

export interface ApiError {
  error: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
  requestId: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasNext: boolean
  hasPrevious: boolean
}

// Authentication Models
export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number
  tokenType: 'Bearer'
}

export interface LoginRequest {
  username: string
  password: string
  tenantId?: string
}

export interface RefreshTokenRequest {
  refreshToken: string
}

// System Models
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  services: ServiceHealth[]
  timestamp: string
}

export interface ServiceHealth {
  name: string
  status: 'up' | 'down' | 'degraded'
  latency?: number
  errorRate?: number
  lastCheck: string
}

export interface FeatureFlag {
  name: string
  enabled: boolean
  description: string
  rolloutPercentage?: number
}

// Dashboard Models
export interface Dashboard {
  id: string
  title: string
  description?: string
  panels: DashboardPanel[]
  timeRange: TimeRange
  refresh: string
  tenantId: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface DashboardPanel {
  id: string
  title: string
  type: 'graph' | 'table' | 'stat' | 'logs' | 'traces'
  query: string
  position: {
    x: number
    y: number
    width: number
    height: number
  }
  options: Record<string, unknown>
}