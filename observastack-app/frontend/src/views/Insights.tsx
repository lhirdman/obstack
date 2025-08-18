import React, { useState, useEffect } from 'react';
import {
  CostSummaryCards,
  CostBreakdownChart,
  CostTrendChart,
  CostOptimizationPanel,
  CostAlertPanel,
  CostDashboardFilters
} from '../components/costs';
import { useCosts, useCostOptimization, useCostAlerts } from '../hooks/useCosts';
import type { CostDashboardFilters as FilterType, CostSummaryCard, CostChartData } from '../types/costs';

export default function Insights() {
  // Initialize filters with default values
  const [filters, setFilters] = useState<FilterType>(() => {
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    return {
      cluster: 'default', // Default cluster - in real app, this would come from user context
      timeRange: {
        from: oneDayAgo.toISOString(),
        to: now.toISOString()
      },
      groupBy: 'namespace'
    };
  });

  // Cost data hooks
  const {
    costs,
    metrics,
    trends,
    totalCost,
    loading: costsLoading,
    error: costsError,
    refresh: refreshCosts,
    createAlert,
    resolveAlert
  } = useCosts(filters, {
    autoRefresh: true,
    refreshInterval: 30000, // 30 seconds
    enableStreaming: false // Disable streaming for now
  });

  const {
    optimizations,
    loading: optimizationsLoading,
    analyze: analyzeOptimizations
  } = useCostOptimization(filters.cluster, filters.namespace, filters.workload);

  const {
    alerts,
    loading: alertsLoading,
    resolveAlert: resolveAlertHook
  } = useCostAlerts(filters.cluster, filters.namespace);

  // Mock data for clusters, namespaces, workloads (in real app, these would come from API)
  const clusters = ['default', 'production', 'staging'];
  const namespaces = ['kube-system', 'default', 'monitoring', 'ingress-nginx'];
  const workloads = ['nginx-deployment', 'api-server', 'database', 'redis'];

  // Generate summary cards from cost data
  const generateSummaryCards = (): CostSummaryCard[] => {
    const cards: CostSummaryCard[] = [
      {
        title: 'Total Cost',
        value: totalCost,
        unit: 'USD',
        color: 'primary',
        trend: {
          direction: 'up',
          percentage: 5.2
        }
      }
    ];

    if (metrics) {
      cards.push(
        {
          title: 'CPU Cost',
          value: metrics.cpuCostTotal,
          unit: 'USD',
          color: 'primary',
          trend: {
            direction: 'down',
            percentage: 2.1
          }
        },
        {
          title: 'Memory Cost',
          value: metrics.memoryCostTotal,
          unit: 'USD',
          color: 'primary',
          trend: {
            direction: 'up',
            percentage: 8.3
          }
        },
        {
          title: 'Efficiency',
          value: metrics.overallEfficiency,
          unit: '%',
          color: metrics.overallEfficiency > 70 ? 'success' : metrics.overallEfficiency > 50 ? 'warning' : 'danger',
          trend: {
            direction: 'stable',
            percentage: 0.5
          }
        }
      );
    }

    return cards;
  };

  // Generate chart data for cost breakdown
  const generateBreakdownChartData = (): CostChartData => {
    if (!metrics) {
      return {
        labels: [],
        datasets: [{ label: 'Cost', data: [] }]
      };
    }

    if (filters.groupBy === 'namespace') {
      return {
        labels: Object.keys(metrics.costByNamespace),
        datasets: [{
          label: 'Cost by Namespace',
          data: Object.values(metrics.costByNamespace),
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
        }]
      };
    } else if (filters.groupBy === 'workload') {
      return {
        labels: Object.keys(metrics.costByWorkload),
        datasets: [{
          label: 'Cost by Workload',
          data: Object.values(metrics.costByWorkload),
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
        }]
      };
    } else {
      // Resource breakdown
      return {
        labels: ['CPU', 'Memory', 'Storage', 'Network'],
        datasets: [{
          label: 'Cost by Resource',
          data: [
            metrics.cpuCostTotal,
            metrics.memoryCostTotal,
            metrics.storageCostTotal,
            metrics.networkCostTotal
          ],
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
        }]
      };
    }
  };

  // Handle alert creation
  const handleCreateAlert = async (alertData: any) => {
    try {
      await createAlert(
        alertData.type,
        alertData.threshold,
        alertData.namespace,
        alertData.workload
      );
    } catch (error) {
      console.error('Failed to create alert:', error);
      throw error;
    }
  };

  // Handle alert resolution
  const handleResolveAlert = async (alertId: string) => {
    try {
      await resolveAlertHook(alertId);
    } catch (error) {
      console.error('Failed to resolve alert:', error);
      throw error;
    }
  };

  const summaryCards = generateSummaryCards();
  const breakdownChartData = generateBreakdownChartData();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cost Insights</h1>
          <p className="text-gray-600">
            Monitor Kubernetes costs, optimize resource usage, and manage cost alerts
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={refreshCosts}
            disabled={costsLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {costsLoading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={analyzeOptimizations}
            disabled={optimizationsLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {optimizationsLoading ? 'Analyzing...' : 'Analyze Costs'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {costsError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading cost data</h3>
              <p className="mt-1 text-sm text-red-700">{costsError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <CostDashboardFilters
        filters={filters}
        onFiltersChange={setFilters}
        clusters={clusters}
        namespaces={namespaces}
        workloads={workloads}
        loading={costsLoading}
      />

      {/* Summary Cards */}
      <CostSummaryCards
        cards={summaryCards}
        loading={costsLoading}
      />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CostBreakdownChart
          data={breakdownChartData}
          title={`Cost Breakdown by ${filters.groupBy}`}
          type="pie"
          loading={costsLoading}
        />
        
        <CostTrendChart
          trends={trends}
          title="Cost Trends"
          loading={costsLoading}
          showForecast={true}
        />
      </div>

      {/* Optimization and Alerts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <CostOptimizationPanel
          optimizations={optimizations}
          loading={optimizationsLoading}
          onRefresh={analyzeOptimizations}
        />
        
        <CostAlertPanel
          alerts={alerts}
          loading={alertsLoading}
          onResolveAlert={handleResolveAlert}
          onCreateAlert={handleCreateAlert}
        />
      </div>

      {/* Additional Insights */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {optimizations.length}
            </div>
            <div className="text-sm text-gray-600">Optimization Opportunities</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              ${optimizations.reduce((sum, opt) => sum + opt.potentialSavings, 0).toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">Potential Monthly Savings</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {alerts.filter(alert => !alert.resolvedAt).length}
            </div>
            <div className="text-sm text-gray-600">Active Cost Alerts</div>
          </div>
        </div>
      </div>
    </div>
  );
}
