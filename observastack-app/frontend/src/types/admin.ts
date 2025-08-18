/**
 * Admin and tenant management type definitions
 */

export interface TenantSettings {
  max_users: number;
  max_dashboards: number;
  max_alerts: number;
  features_enabled: string[];
  custom_branding: Record<string, any>;
  notification_settings: Record<string, any>;
  cost_budget_monthly?: number;
  cost_alert_threshold: number;
}

export interface DataRetentionPolicy {
  logs_retention_days: number;
  metrics_retention_days: number;
  traces_retention_days: number;
  alerts_retention_days: number;
  cost_data_retention_days: number;
}

export enum TenantStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
  ARCHIVED = 'archived'
}

export interface Tenant {
  id: string;
  name: string;
  domain: string;
  description?: string;
  status: TenantStatus;
  settings: TenantSettings;
  retention_policy: DataRetentionPolicy;
  created_at: string;
  updated_at: string;
  user_count: number;
  storage_usage_mb: number;
  monthly_cost?: number;
}

export interface TenantCreate {
  name: string;
  domain: string;
  description?: string;
  admin_email: string;
  admin_username: string;
  settings?: TenantSettings;
  retention_policy?: DataRetentionPolicy;
}

export interface TenantUpdate {
  name?: string;
  description?: string;
  status?: TenantStatus;
  settings?: TenantSettings;
  retention_policy?: DataRetentionPolicy;
}

export interface TenantList {
  tenants: Tenant[];
  total: number;
  page: number;
  page_size: number;
}

export interface TenantStats {
  tenant_id: string;
  user_count: number;
  dashboard_count: number;
  alert_count: number;
  storage_usage_mb: number;
  monthly_cost?: number;
  cost_trend?: string;
  last_activity?: string;
}

export interface TenantHealthCheck {
  tenant_id: string;
  status: string;
  services: Record<string, string>;
  storage_health: Record<string, any>;
  cost_health: Record<string, any>;
  last_check: string;
  issues: string[];
}

export interface UserManagement {
  user_id: string;
  action: string;
  reason?: string;
}

export interface RoleManagement {
  user_id: string;
  roles: string[];
  replace: boolean;
}

export interface SystemUser {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  tenant_id: string;
  roles: string[];
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

export interface SystemSettings {
  feature_flags: Record<string, boolean>;
  global_settings: Record<string, any>;
  maintenance_mode: boolean;
  system_notifications: string[];
}

export interface AuditLogEntry {
  id: string;
  tenant_id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
}

export interface AuditLogList {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

// Filter and pagination interfaces
export interface TenantFilters {
  status?: TenantStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface UserFilters {
  tenant_id?: string;
  role?: string;
  status?: 'active' | 'inactive';
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AuditLogFilters {
  tenant_id?: string;
  user_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}