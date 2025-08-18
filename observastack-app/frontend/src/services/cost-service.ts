/**
 * Cost monitoring service for OpenCost integration
 */

import { apiClient } from '../lib/api-client';
import type {
  CostQueryRequest,
  CostQueryResponse,
  CostAlertRequest,
  CostAlertResponse,
  CostOptimizationRequest,
  CostOptimizationResponse,
  CostReportRequest,
  CostReportResponse,
  KubernetesCost,
  CostAlert,
  CostTrend,
  OpenCostMetrics
} from '../types/costs';

export class CostService {
  private readonly baseUrl = '/api/v1/costs';

  /**
   * Query cost data with filtering and aggregation
   */
  async queryCosts(request: CostQueryRequest): Promise<CostQueryResponse> {
    const response = await apiClient.post<CostQueryResponse>(
      `${this.baseUrl}/query`,
      request
    );
    return response.data;
  }

  /**
   * Get cost data for all workloads in a namespace
   */
  async getNamespaceCosts(
    cluster: string,
    namespace: string,
    startTime: string,
    endTime: string,
    aggregation = '1h'
  ): Promise<KubernetesCost[]> {
    const response = await apiClient.get<KubernetesCost[]>(
      `${this.baseUrl}/clusters/${cluster}/namespaces/${namespace}/costs`,
      {
        params: {
          start_time: startTime,
          end_time: endTime,
          aggregation
        }
      }
    );
    return response.data;
  }

  /**
   * Get comprehensive cluster metrics
   */
  async getClusterMetrics(
    cluster: string,
    startTime: string,
    endTime: string,
    aggregation = '1h'
  ): Promise<OpenCostMetrics> {
    const response = await apiClient.get<OpenCostMetrics>(
      `${this.baseUrl}/clusters/${cluster}/metrics`,
      {
        params: {
          start_time: startTime,
          end_time: endTime,
          aggregation
        }
      }
    );
    return response.data;
  }

  /**
   * Get cost trend analysis
   */
  async getCostTrends(
    cluster: string,
    namespace?: string,
    workload?: string,
    days = 7
  ): Promise<CostTrend[]> {
    const response = await apiClient.get<CostTrend[]>(
      `${this.baseUrl}/trends`,
      {
        params: {
          cluster,
          namespace,
          workload,
          days
        }
      }
    );
    return response.data;
  }

  /**
   * Analyze cost optimization opportunities
   */
  async analyzeCostOptimization(
    request: CostOptimizationRequest
  ): Promise<CostOptimizationResponse> {
    const response = await apiClient.post<CostOptimizationResponse>(
      `${this.baseUrl}/optimization`,
      request
    );
    return response.data;
  }

  /**
   * Create a cost alert
   */
  async createCostAlert(request: CostAlertRequest): Promise<CostAlertResponse> {
    const response = await apiClient.post<CostAlertResponse>(
      `${this.baseUrl}/alerts`,
      request
    );
    return response.data;
  }

  /**
   * Get cost alerts with filtering
   */
  async getCostAlerts(
    cluster?: string,
    namespace?: string,
    alertType?: string,
    activeOnly = true
  ): Promise<CostAlert[]> {
    const response = await apiClient.get<CostAlert[]>(
      `${this.baseUrl}/alerts`,
      {
        params: {
          cluster,
          namespace,
          alert_type: alertType,
          active_only: activeOnly
        }
      }
    );
    return response.data;
  }

  /**
   * Resolve a cost alert
   */
  async resolveCostAlert(alertId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.put<{ success: boolean; message: string }>(
      `${this.baseUrl}/alerts/${alertId}/resolve`
    );
    return response.data;
  }

  /**
   * Generate cost reports for chargeback/showback
   */
  async generateCostReport(request: CostReportRequest): Promise<CostReportResponse> {
    const response = await apiClient.post<CostReportResponse>(
      `${this.baseUrl}/reports`,
      request
    );
    return response.data;
  }

  /**
   * Stream real-time cost allocation data
   */
  streamCostAllocation(
    cluster: string,
    startTime: string,
    endTime: string,
    onData: (data: any) => void,
    onError?: (error: Error) => void
  ): EventSource {
    const params = new URLSearchParams({
      cluster,
      start_time: startTime,
      end_time: endTime
    });

    const eventSource = new EventSource(
      `${this.baseUrl}/allocation/stream?${params.toString()}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onData(data);
      } catch (error) {
        console.error('Failed to parse cost allocation data:', error);
        onError?.(error as Error);
      }
    };

    eventSource.onerror = (event) => {
      console.error('Cost allocation stream error:', event);
      onError?.(new Error('Cost allocation stream failed'));
    };

    return eventSource;
  }

  /**
   * Check OpenCost service health
   */
  async checkHealth(): Promise<{
    status: string;
    error?: string;
    timestamp: string;
  }> {
    const response = await apiClient.get<{
      status: string;
      error?: string;
      timestamp: string;
    }>(`${this.baseUrl}/health`);
    return response.data;
  }
}

// Export singleton instance
export const costService = new CostService();