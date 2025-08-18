/**
 * Custom hook for cost monitoring and OpenCost integration
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { costService } from '../services/cost-service';
import type {
  CostQueryRequest,
  CostQueryResponse,
  KubernetesCost,
  CostAlert,
  CostTrend,
  CostOptimization,
  OpenCostMetrics,
  CostDashboardFilters
} from '../types/costs';

interface CostState {
  costs: KubernetesCost[];
  metrics: OpenCostMetrics | null;
  trends: CostTrend[];
  alerts: CostAlert[];
  optimizations: CostOptimization[];
  totalCost: number;
  loading: boolean;
  error: string | null;
}

interface UseCostsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
  enableStreaming?: boolean;
}

export function useCosts(
  filters: CostDashboardFilters,
  options: UseCostsOptions = {}
) {
  const {
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
    enableStreaming = false
  } = options;

  const [state, setState] = useState<CostState>({
    costs: [],
    metrics: null,
    trends: [],
    alerts: [],
    optimizations: [],
    totalCost: 0,
    loading: false,
    error: null
  });

  const streamRef = useRef<EventSource | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load cost data
  const loadCostData = useCallback(async () => {
    if (!filters.cluster) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const request: CostQueryRequest = {
        cluster: filters.cluster,
        namespace: filters.namespace,
        workload: filters.workload,
        startTime: filters.timeRange.from,
        endTime: filters.timeRange.to,
        aggregation: '1h',
        includeRecommendations: true
      };

      const [costResponse, trendsData, alertsData] = await Promise.all([
        costService.queryCosts(request),
        costService.getCostTrends(
          filters.cluster,
          filters.namespace,
          filters.workload,
          7
        ),
        costService.getCostAlerts(
          filters.cluster,
          filters.namespace,
          undefined,
          true
        )
      ]);

      // Get cluster metrics if no specific namespace/workload filter
      let metricsData: OpenCostMetrics | null = null;
      if (!filters.namespace && !filters.workload) {
        metricsData = await costService.getClusterMetrics(
          filters.cluster,
          filters.timeRange.from,
          filters.timeRange.to
        );
      }

      setState(prev => ({
        ...prev,
        costs: costResponse.costs,
        metrics: metricsData,
        trends: trendsData,
        alerts: alertsData,
        optimizations: costResponse.recommendations,
        totalCost: costResponse.totalCost,
        loading: false
      }));

    } catch (error) {
      console.error('Failed to load cost data:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load cost data'
      }));
    }
  }, [filters]);

  // Start streaming cost allocation data
  const startStreaming = useCallback(() => {
    if (!filters.cluster || !enableStreaming) return;

    // Close existing stream
    if (streamRef.current) {
      streamRef.current.close();
    }

    streamRef.current = costService.streamCostAllocation(
      filters.cluster,
      filters.timeRange.from,
      filters.timeRange.to,
      (data) => {
        if (data.type === 'allocation') {
          setState(prev => ({
            ...prev,
            metrics: prev.metrics ? {
              ...prev.metrics,
              totalCost: data.total_cost,
              costByNamespace: data.namespaces,
              costByWorkload: data.workloads,
              overallEfficiency: data.efficiency,
              lastUpdated: data.timestamp
            } : null
          }));
        }
      },
      (error) => {
        console.error('Cost streaming error:', error);
        setState(prev => ({
          ...prev,
          error: 'Real-time cost streaming failed'
        }));
      }
    );
  }, [filters, enableStreaming]);

  // Stop streaming
  const stopStreaming = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.close();
      streamRef.current = null;
    }
  }, []);

  // Refresh data
  const refresh = useCallback(() => {
    loadCostData();
  }, [loadCostData]);

  // Create cost alert
  const createAlert = useCallback(async (
    type: string,
    threshold: number,
    namespace: string,
    workload?: string
  ) => {
    if (!filters.cluster) return;

    try {
      const response = await costService.createCostAlert({
        type: type as any,
        threshold,
        namespace,
        workload,
        cluster: filters.cluster
      });

      if (response.success) {
        // Refresh alerts
        const alertsData = await costService.getCostAlerts(
          filters.cluster,
          filters.namespace,
          undefined,
          true
        );
        setState(prev => ({ ...prev, alerts: alertsData }));
      }

      return response;
    } catch (error) {
      console.error('Failed to create cost alert:', error);
      throw error;
    }
  }, [filters.cluster, filters.namespace]);

  // Resolve cost alert
  const resolveAlert = useCallback(async (alertId: string) => {
    try {
      await costService.resolveCostAlert(alertId);
      
      // Refresh alerts
      if (filters.cluster) {
        const alertsData = await costService.getCostAlerts(
          filters.cluster,
          filters.namespace,
          undefined,
          true
        );
        setState(prev => ({ ...prev, alerts: alertsData }));
      }
    } catch (error) {
      console.error('Failed to resolve cost alert:', error);
      throw error;
    }
  }, [filters.cluster, filters.namespace]);

  // Generate optimization analysis
  const analyzeOptimizations = useCallback(async () => {
    if (!filters.cluster) return;

    try {
      const response = await costService.analyzeCostOptimization({
        cluster: filters.cluster,
        namespace: filters.namespace,
        workload: filters.workload,
        timeRangeDays: 7,
        minSavingsThreshold: 5.0
      });

      setState(prev => ({
        ...prev,
        optimizations: response.optimizations
      }));

      return response;
    } catch (error) {
      console.error('Failed to analyze cost optimizations:', error);
      throw error;
    }
  }, [filters]);

  // Effect to load initial data
  useEffect(() => {
    loadCostData();
  }, [loadCostData]);

  // Effect to handle auto-refresh
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        loadCostData();
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, loadCostData]);

  // Effect to handle streaming
  useEffect(() => {
    if (enableStreaming) {
      startStreaming();
    } else {
      stopStreaming();
    }

    return () => {
      stopStreaming();
    };
  }, [enableStreaming, startStreaming, stopStreaming]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming();
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [stopStreaming]);

  return {
    ...state,
    refresh,
    createAlert,
    resolveAlert,
    analyzeOptimizations,
    startStreaming,
    stopStreaming
  };
}

// Hook for cost optimization analysis
export function useCostOptimization(
  cluster?: string,
  namespace?: string,
  workload?: string
) {
  const [optimizations, setOptimizations] = useState<CostOptimization[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async () => {
    if (!cluster) return;

    setLoading(true);
    setError(null);

    try {
      const response = await costService.analyzeCostOptimization({
        cluster,
        namespace,
        workload,
        timeRangeDays: 7,
        minSavingsThreshold: 1.0
      });

      setOptimizations(response.optimizations);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      setError(errorMessage);
      console.error('Cost optimization analysis failed:', err);
    } finally {
      setLoading(false);
    }
  }, [cluster, namespace, workload]);

  useEffect(() => {
    analyze();
  }, [analyze]);

  return {
    optimizations,
    loading,
    error,
    analyze
  };
}

// Hook for cost alerts management
export function useCostAlerts(cluster?: string, namespace?: string) {
  const [alerts, setAlerts] = useState<CostAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    if (!cluster) return;

    setLoading(true);
    setError(null);

    try {
      const alertsData = await costService.getCostAlerts(
        cluster,
        namespace,
        undefined,
        true
      );
      setAlerts(alertsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load alerts';
      setError(errorMessage);
      console.error('Failed to load cost alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [cluster, namespace]);

  const resolveAlert = useCallback(async (alertId: string) => {
    try {
      await costService.resolveCostAlert(alertId);
      await loadAlerts(); // Refresh alerts
    } catch (err) {
      console.error('Failed to resolve alert:', err);
      throw err;
    }
  }, [loadAlerts]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  return {
    alerts,
    loading,
    error,
    refresh: loadAlerts,
    resolveAlert
  };
}