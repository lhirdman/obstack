/**
 * React hook for Grafana dashboard management
 */

import { useState, useEffect, useCallback } from 'react';
import { GrafanaService, DashboardInfo, EmbedConfig, GrafanaHealth } from '../services/grafana-service';

const grafanaService = new GrafanaService();

export interface UseGrafanaState {
  dashboards: DashboardInfo[];
  costDashboards: DashboardInfo[];
  observabilityDashboards: DashboardInfo[];
  embedConfig: EmbedConfig | null;
  health: GrafanaHealth | null;
  loading: boolean;
  error: string | null;
}

export interface UseGrafanaActions {
  loadDashboards: () => Promise<void>;
  loadCostDashboards: () => Promise<void>;
  loadObservabilityDashboards: () => Promise<void>;
  loadEmbedConfig: () => Promise<void>;
  checkHealth: () => Promise<void>;
  generateDashboardUrl: (dashboardUid: string, options?: any) => Promise<string>;
  createSnapshot: (dashboardUid: string, expires?: number) => Promise<any>;
  searchDashboards: (query?: string, tags?: string[]) => Promise<DashboardInfo[]>;
  refresh: () => Promise<void>;
}

export function useGrafana(): UseGrafanaState & UseGrafanaActions {
  const [state, setState] = useState<UseGrafanaState>({
    dashboards: [],
    costDashboards: [],
    observabilityDashboards: [],
    embedConfig: null,
    health: null,
    loading: false,
    error: null
  });

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, loading: false }));
  }, []);

  const loadDashboards = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await grafanaService.getDashboards();
      
      setState(prev => ({
        ...prev,
        dashboards: response.dashboards,
        loading: false
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboards');
    }
  }, [setLoading, setError]);

  const loadCostDashboards = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const costDashboards = await grafanaService.getCostDashboards();
      
      setState(prev => ({
        ...prev,
        costDashboards,
        loading: false
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cost dashboards');
    }
  }, [setLoading, setError]);

  const loadObservabilityDashboards = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const observabilityDashboards = await grafanaService.getObservabilityDashboards();
      
      setState(prev => ({
        ...prev,
        observabilityDashboards,
        loading: false
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load observability dashboards');
    }
  }, [setLoading, setError]);

  const loadEmbedConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const embedConfig = await grafanaService.getEmbedConfig();
      
      setState(prev => ({
        ...prev,
        embedConfig,
        loading: false
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load embed config');
    }
  }, [setLoading, setError]);

  const checkHealth = useCallback(async () => {
    try {
      const health = await grafanaService.checkHealth();
      
      setState(prev => ({
        ...prev,
        health
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check Grafana health');
    }
  }, [setError]);

  const generateDashboardUrl = useCallback(async (
    dashboardUid: string,
    options?: any
  ): Promise<string> => {
    try {
      const response = await grafanaService.generateDashboardUrl({
        dashboard_uid: dashboardUid,
        ...options
      });
      return response.embed_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate dashboard URL');
      throw err;
    }
  }, [setError]);

  const createSnapshot = useCallback(async (
    dashboardUid: string,
    expires: number = 3600
  ): Promise<any> => {
    try {
      return await grafanaService.createSnapshot(dashboardUid, expires);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create snapshot');
      throw err;
    }
  }, [setError]);

  const searchDashboards = useCallback(async (
    query?: string,
    tags?: string[]
  ): Promise<DashboardInfo[]> => {
    try {
      return await grafanaService.searchDashboards(query, tags);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search dashboards');
      throw err;
    }
  }, [setError]);

  const refresh = useCallback(async () => {
    await Promise.all([
      loadDashboards(),
      loadCostDashboards(),
      loadObservabilityDashboards(),
      loadEmbedConfig(),
      checkHealth()
    ]);
  }, [loadDashboards, loadCostDashboards, loadObservabilityDashboards, loadEmbedConfig, checkHealth]);

  // Load initial data
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    ...state,
    loadDashboards,
    loadCostDashboards,
    loadObservabilityDashboards,
    loadEmbedConfig,
    checkHealth,
    generateDashboardUrl,
    createSnapshot,
    searchDashboards,
    refresh
  };
}

export interface UseDashboardEmbedOptions {
  dashboardUid: string;
  panelId?: number;
  theme?: 'light' | 'dark';
  timeFrom?: string;
  timeTo?: string;
  variables?: Record<string, string>;
  refresh?: string;
  autoRefresh?: boolean;
}

export interface UseDashboardEmbedState {
  embedUrl: string | null;
  loading: boolean;
  error: string | null;
}

export function useDashboardEmbed(options: UseDashboardEmbedOptions): UseDashboardEmbedState {
  const [state, setState] = useState<UseDashboardEmbedState>({
    embedUrl: null,
    loading: false,
    error: null
  });

  const generateEmbedUrl = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const response = await grafanaService.generateDashboardUrl({
        dashboard_uid: options.dashboardUid,
        panel_id: options.panelId,
        theme: options.theme,
        time_from: options.timeFrom,
        time_to: options.timeTo,
        variables: options.variables,
        refresh: options.refresh
      });
      
      setState({
        embedUrl: response.embed_url,
        loading: false,
        error: null
      });
    } catch (err) {
      setState({
        embedUrl: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to generate embed URL'
      });
    }
  }, [options]);

  useEffect(() => {
    if (options.dashboardUid) {
      generateEmbedUrl();
    }
  }, [generateEmbedUrl, options.dashboardUid]);

  // Auto-refresh if enabled
  useEffect(() => {
    if (options.autoRefresh && options.refresh) {
      const refreshMs = parseRefreshInterval(options.refresh);
      if (refreshMs > 0) {
        const interval = setInterval(generateEmbedUrl, refreshMs);
        return () => clearInterval(interval);
      }
    }
  }, [options.autoRefresh, options.refresh, generateEmbedUrl]);

  return state;
}

/**
 * Parse Grafana refresh interval to milliseconds
 */
function parseRefreshInterval(refresh: string): number {
  const match = refresh.match(/^(\d+)([smh])$/);
  if (!match) return 0;
  
  const value = parseInt(match[1]);
  const unit = match[2];
  
  switch (unit) {
    case 's': return value * 1000;
    case 'm': return value * 60 * 1000;
    case 'h': return value * 60 * 60 * 1000;
    default: return 0;
  }
}