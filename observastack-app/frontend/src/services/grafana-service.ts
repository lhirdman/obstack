/**
 * Grafana service for dashboard management and embedding
 */

import { apiClient } from '../lib/api-client';

export interface DashboardInfo {
  uid: string;
  title: string;
  tags: string[];
  url: string;
  folder_title?: string;
}

export interface DashboardListResponse {
  dashboards: DashboardInfo[];
  total: number;
}

export interface DashboardUrlRequest {
  dashboard_uid: string;
  panel_id?: number;
  time_from?: string;
  time_to?: string;
  refresh?: string;
  variables?: Record<string, string>;
  theme?: 'light' | 'dark';
}

export interface DashboardUrlResponse {
  url: string;
  embed_url: string;
}

export interface EmbedConfig {
  grafana_url: string;
  theme: string;
  tenant_id: string;
  auth_token: string;
}

export interface GrafanaHealth {
  status: 'healthy' | 'unhealthy';
  service: string;
  timestamp: string;
}

export class GrafanaService {
  private baseUrl = '/api/v1/grafana';

  /**
   * Check Grafana health status
   */
  async checkHealth(): Promise<GrafanaHealth> {
    const response = await apiClient.get(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * Get list of dashboards accessible to current tenant
   */
  async getDashboards(): Promise<DashboardListResponse> {
    const response = await apiClient.get(`${this.baseUrl}/dashboards`);
    return response.data;
  }

  /**
   * Get specific dashboard by UID
   */
  async getDashboard(dashboardUid: string): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/dashboards/${dashboardUid}`);
    return response.data;
  }

  /**
   * Generate dashboard URL with authentication and parameters
   */
  async generateDashboardUrl(request: DashboardUrlRequest): Promise<DashboardUrlResponse> {
    const response = await apiClient.post(`${this.baseUrl}/dashboards/url`, request);
    return response.data;
  }

  /**
   * Get embed configuration for iframe integration
   */
  async getEmbedConfig(): Promise<EmbedConfig> {
    const response = await apiClient.get(`${this.baseUrl}/embed/config`);
    return response.data;
  }

  /**
   * Create dashboard snapshot for sharing
   */
  async createSnapshot(dashboardUid: string, expires: number = 3600): Promise<any> {
    const response = await apiClient.post(
      `${this.baseUrl}/dashboards/${dashboardUid}/snapshot`,
      {},
      { params: { expires } }
    );
    return response.data;
  }

  /**
   * Proxy request to Grafana API
   */
  async proxyRequest(
    path: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    data?: any,
    params?: Record<string, any>
  ): Promise<any> {
    const config: any = {
      method,
      url: `${this.baseUrl}/proxy/${path}`,
      params
    };

    if (data && ['POST', 'PUT'].includes(method)) {
      config.data = data;
    }

    const response = await apiClient.request(config);
    return response.data;
  }

  /**
   * Search dashboards with filters
   */
  async searchDashboards(query?: string, tags?: string[]): Promise<DashboardInfo[]> {
    const params: Record<string, any> = { type: 'dash-db' };
    
    if (query) {
      params.query = query;
    }
    
    if (tags && tags.length > 0) {
      params.tag = tags;
    }

    const response = await this.proxyRequest('api/search', 'GET', undefined, params);
    return response;
  }

  /**
   * Get dashboard folders
   */
  async getFolders(): Promise<any[]> {
    const response = await this.proxyRequest('api/folders');
    return response;
  }

  /**
   * Get dashboard annotations
   */
  async getAnnotations(
    dashboardUid: string,
    from?: string,
    to?: string
  ): Promise<any[]> {
    const params: Record<string, any> = {
      dashboardUID: dashboardUid
    };

    if (from) params.from = from;
    if (to) params.to = to;

    const response = await this.proxyRequest('api/annotations', 'GET', undefined, params);
    return response;
  }

  /**
   * Get dashboard variables
   */
  async getDashboardVariables(dashboardUid: string): Promise<any[]> {
    const dashboard = await this.getDashboard(dashboardUid);
    return dashboard.dashboard?.templating?.list || [];
  }

  /**
   * Build embed URL with parameters
   */
  buildEmbedUrl(
    dashboardUid: string,
    options: {
      panelId?: number;
      theme?: 'light' | 'dark';
      timeFrom?: string;
      timeTo?: string;
      variables?: Record<string, string>;
      kiosk?: boolean;
      refresh?: string;
    } = {}
  ): string {
    const {
      panelId,
      theme = 'light',
      timeFrom,
      timeTo,
      variables = {},
      kiosk = true,
      refresh
    } = options;

    // Build base path
    const basePath = panelId 
      ? `/d-solo/${dashboardUid}` 
      : `/d/${dashboardUid}`;

    // Build query parameters
    const params = new URLSearchParams();
    
    params.set('orgId', '1');
    params.set('theme', theme);
    
    if (kiosk) {
      params.set('kiosk', 'true');
    }
    
    if (panelId) {
      params.set('panelId', panelId.toString());
    }
    
    if (timeFrom) {
      params.set('from', timeFrom);
    }
    
    if (timeTo) {
      params.set('to', timeTo);
    }
    
    if (refresh) {
      params.set('refresh', refresh);
    }

    // Add dashboard variables
    Object.entries(variables).forEach(([key, value]) => {
      params.set(`var-${key}`, value);
    });

    return `${basePath}?${params.toString()}`;
  }

  /**
   * Get cost monitoring dashboards
   */
  async getCostDashboards(): Promise<DashboardInfo[]> {
    const dashboards = await this.searchDashboards(undefined, ['cost', 'opencost', 'kubernetes-cost']);
    return dashboards.filter(d => 
      d.title.toLowerCase().includes('cost') ||
      d.tags.some(tag => ['cost', 'opencost', 'kubernetes-cost'].includes(tag.toLowerCase()))
    );
  }

  /**
   * Get observability dashboards (logs, metrics, traces)
   */
  async getObservabilityDashboards(): Promise<DashboardInfo[]> {
    const dashboards = await this.searchDashboards(undefined, [
      'observability', 'monitoring', 'logs', 'metrics', 'traces', 'prometheus', 'loki', 'tempo'
    ]);
    return dashboards.filter(d => 
      !d.title.toLowerCase().includes('cost') &&
      !d.tags.some(tag => ['cost', 'opencost'].includes(tag.toLowerCase()))
    );
  }
}