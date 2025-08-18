/**
 * Admin service for tenant and system management operations
 */

import { 
  Tenant, 
  TenantCreate, 
  TenantUpdate, 
  TenantList, 
  TenantStats, 
  TenantHealthCheck,
  TenantFilters,
  UserFilters,
  AuditLogFilters,
  AuditLogList,
  SystemUser,
  SystemSettings,
  UserManagement,
  RoleManagement
} from '../types/admin';

const API_BASE = '/api/v1';

class AdminService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Tenant Management
  async createTenant(tenantData: TenantCreate): Promise<Tenant> {
    return this.request<Tenant>('/tenants', {
      method: 'POST',
      body: JSON.stringify(tenantData),
    });
  }

  async getTenants(filters: TenantFilters = {}): Promise<TenantList> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);

    const queryString = params.toString();
    const endpoint = queryString ? `/tenants?${queryString}` : '/tenants';
    
    return this.request<TenantList>(endpoint);
  }

  async getTenant(tenantId: string): Promise<Tenant> {
    return this.request<Tenant>(`/tenants/${tenantId}`);
  }

  async updateTenant(tenantId: string, updateData: TenantUpdate): Promise<Tenant> {
    return this.request<Tenant>(`/tenants/${tenantId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async deleteTenant(tenantId: string): Promise<void> {
    await this.request<void>(`/tenants/${tenantId}`, {
      method: 'DELETE',
    });
  }

  async getTenantStats(tenantId: string): Promise<TenantStats> {
    return this.request<TenantStats>(`/tenants/${tenantId}/stats`);
  }

  async getTenantHealth(tenantId: string): Promise<TenantHealthCheck> {
    return this.request<TenantHealthCheck>(`/tenants/${tenantId}/health`);
  }

  async getTenantByDomain(domain: string): Promise<Tenant> {
    return this.request<Tenant>(`/tenants/domain/${domain}`);
  }

  // User Management (placeholder - would need actual user management endpoints)
  async getUsers(filters: UserFilters = {}): Promise<{ users: SystemUser[]; total: number }> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.tenant_id) params.append('tenant_id', filters.tenant_id);
    if (filters.role) params.append('role', filters.role);
    if (filters.status) params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);

    const queryString = params.toString();
    const endpoint = queryString ? `/admin/users?${queryString}` : '/admin/users';
    
    return this.request<{ users: SystemUser[]; total: number }>(endpoint);
  }

  async getUser(userId: string): Promise<SystemUser> {
    return this.request<SystemUser>(`/admin/users/${userId}`);
  }

  async manageUser(userId: string, action: UserManagement): Promise<void> {
    await this.request<void>(`/admin/users/${userId}/manage`, {
      method: 'POST',
      body: JSON.stringify(action),
    });
  }

  async assignRoles(userId: string, roleData: RoleManagement): Promise<void> {
    await this.request<void>(`/admin/users/${userId}/roles`, {
      method: 'PUT',
      body: JSON.stringify(roleData),
    });
  }

  // System Settings (placeholder)
  async getSystemSettings(): Promise<SystemSettings> {
    return this.request<SystemSettings>('/admin/settings');
  }

  async updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    return this.request<SystemSettings>('/admin/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Audit Logs (placeholder)
  async getAuditLogs(filters: AuditLogFilters = {}): Promise<AuditLogList> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.tenant_id) params.append('tenant_id', filters.tenant_id);
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.action) params.append('action', filters.action);
    if (filters.resource_type) params.append('resource_type', filters.resource_type);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);

    const queryString = params.toString();
    const endpoint = queryString ? `/admin/audit-logs?${queryString}` : '/admin/audit-logs';
    
    return this.request<AuditLogList>(endpoint);
  }

  // System Health
  async getSystemHealth(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('/admin/health');
  }

  async getSystemMetrics(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('/admin/metrics');
  }
}

export const adminService = new AdminService();
export default adminService;