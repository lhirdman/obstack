/**
 * Custom hook for admin and tenant management operations
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  Tenant, 
  TenantCreate, 
  TenantUpdate, 
  TenantList, 
  TenantStats, 
  TenantHealthCheck,
  TenantFilters,
  SystemUser,
  SystemSettings,
  AuditLogList,
  AuditLogFilters
} from '../types/admin';
import adminService from '../services/admin-service';

interface UseTenantsState {
  tenants: Tenant[];
  total: number;
  loading: boolean;
  error: string | null;
}

interface UseTenantState {
  tenant: Tenant | null;
  stats: TenantStats | null;
  health: TenantHealthCheck | null;
  loading: boolean;
  error: string | null;
}

interface UseUsersState {
  users: SystemUser[];
  total: number;
  loading: boolean;
  error: string | null;
}

interface UseSystemState {
  settings: SystemSettings | null;
  health: Record<string, any> | null;
  metrics: Record<string, any> | null;
  loading: boolean;
  error: string | null;
}

export function useTenants(filters: TenantFilters = {}) {
  const [state, setState] = useState<UseTenantsState>({
    tenants: [],
    total: 0,
    loading: false,
    error: null,
  });

  const loadTenants = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await adminService.getTenants(filters);
      setState({
        tenants: result.tenants,
        total: result.total,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load tenants',
      }));
    }
  }, [filters]);

  const createTenant = useCallback(async (tenantData: TenantCreate): Promise<Tenant> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const newTenant = await adminService.createTenant(tenantData);
      setState(prev => ({
        ...prev,
        tenants: [newTenant, ...prev.tenants],
        total: prev.total + 1,
        loading: false,
      }));
      return newTenant;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to create tenant',
      }));
      throw error;
    }
  }, []);

  const updateTenant = useCallback(async (tenantId: string, updateData: TenantUpdate): Promise<Tenant> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const updatedTenant = await adminService.updateTenant(tenantId, updateData);
      setState(prev => ({
        ...prev,
        tenants: prev.tenants.map(t => t.id === tenantId ? updatedTenant : t),
        loading: false,
      }));
      return updatedTenant;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to update tenant',
      }));
      throw error;
    }
  }, []);

  const deleteTenant = useCallback(async (tenantId: string): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      await adminService.deleteTenant(tenantId);
      setState(prev => ({
        ...prev,
        tenants: prev.tenants.filter(t => t.id !== tenantId),
        total: prev.total - 1,
        loading: false,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to delete tenant',
      }));
      throw error;
    }
  }, []);

  useEffect(() => {
    loadTenants();
  }, [loadTenants]);

  return {
    ...state,
    loadTenants,
    createTenant,
    updateTenant,
    deleteTenant,
  };
}

export function useTenant(tenantId: string | null) {
  const [state, setState] = useState<UseTenantState>({
    tenant: null,
    stats: null,
    health: null,
    loading: false,
    error: null,
  });

  const loadTenant = useCallback(async () => {
    if (!tenantId) return;
    
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const [tenant, stats, health] = await Promise.all([
        adminService.getTenant(tenantId),
        adminService.getTenantStats(tenantId),
        adminService.getTenantHealth(tenantId),
      ]);
      
      setState({
        tenant,
        stats,
        health,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load tenant details',
      }));
    }
  }, [tenantId]);

  useEffect(() => {
    loadTenant();
  }, [loadTenant]);

  return {
    ...state,
    loadTenant,
  };
}

export function useUsers(filters: any = {}) {
  const [state, setState] = useState<UseUsersState>({
    users: [],
    total: 0,
    loading: false,
    error: null,
  });

  const loadUsers = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await adminService.getUsers(filters);
      setState({
        users: result.users,
        total: result.total,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load users',
      }));
    }
  }, [filters]);

  const manageUser = useCallback(async (userId: string, action: any): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      await adminService.manageUser(userId, action);
      await loadUsers(); // Reload users after action
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to manage user',
      }));
      throw error;
    }
  }, [loadUsers]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  return {
    ...state,
    loadUsers,
    manageUser,
  };
}

export function useSystemSettings() {
  const [state, setState] = useState<UseSystemState>({
    settings: null,
    health: null,
    metrics: null,
    loading: false,
    error: null,
  });

  const loadSystemData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const [settings, health, metrics] = await Promise.all([
        adminService.getSystemSettings(),
        adminService.getSystemHealth(),
        adminService.getSystemMetrics(),
      ]);
      
      setState({
        settings,
        health,
        metrics,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load system data',
      }));
    }
  }, []);

  const updateSettings = useCallback(async (newSettings: Partial<SystemSettings>): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const updatedSettings = await adminService.updateSystemSettings(newSettings);
      setState(prev => ({
        ...prev,
        settings: updatedSettings,
        loading: false,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to update settings',
      }));
      throw error;
    }
  }, []);

  useEffect(() => {
    loadSystemData();
  }, [loadSystemData]);

  return {
    ...state,
    loadSystemData,
    updateSettings,
  };
}

export function useAuditLogs(filters: AuditLogFilters = {}) {
  const [logs, setLogs] = useState<AuditLogList>({
    logs: [],
    total: 0,
    page: 1,
    page_size: 50,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await adminService.getAuditLogs(filters);
      setLogs(result);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  return {
    logs,
    loading,
    error,
    loadLogs,
  };
}