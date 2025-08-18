/**
 * Cost monitoring and OpenCost integration type definitions
 */

// Enums
export type ResourceType = 'cpu' | 'memory' | 'storage' | 'network' | 'gpu';

export type CostAlertType = 
  | 'budget_exceeded' 
  | 'anomaly_detected' 
  | 'efficiency_low' 
  | 'waste_detected' 
  | 'threshold_breach';

export type OptimizationType = 
  | 'rightsizing' 
  | 'scheduling' 
  | 'storage' 
  | 'networking' 
  | 'workload_optimization';

export type ImplementationEffort = 'low' | 'medium' | 'high';
export type RiskLevel = 'low' | 'medium' | 'high';
export type TrendDirection = 'increasing' | 'decreasing' | 'stable';

// Core cost models
export interface CostAllocation {
  resourceType: ResourceType;
  allocatedCost: number;
  actualUsage: number;
  efficiency: number;
  wastedCost: number;
  optimizationPotential: number;
  currency: string;
  periodStart: string;
  periodEnd: string;
  tenantId: string;
}

export interface KubernetesCost {
  namespace: string;
  workload: string;
  service?: string;
  cluster: string;
  
  // Cost breakdown
  cpuCost: number;
  memoryCost: number;
  storageCost: number;
  networkCost: number;
  gpuCost: number;
  totalCost: number;
  
  // Efficiency metrics
  efficiency: number;
  recommendations: CostOptimization[];
  
  // Metadata
  currency: string;
  periodStart: string;
  periodEnd: string;
  tenantId: string;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  
  // Resource requests/limits
  cpuRequest?: number;
  memoryRequest?: number;
  cpuLimit?: number;
  memoryLimit?: number;
}

export interface CostOptimization {
  type: OptimizationType;
  title: string;
  description: string;
  potentialSavings: number;
  implementationEffort: ImplementationEffort;
  riskLevel: RiskLevel;
  steps: string[];
  
  // Resource recommendations
  currentResources: Record<string, number>;
  recommendedResources: Record<string, number>;
  
  // Metadata
  confidenceScore: number;
  impactAnalysis: Record<string, unknown>;
  createdAt: string;
}

export interface CostAlert {
  id: string;
  type: CostAlertType;
  severity: 'low' | 'medium' | 'high' | 'critical';
  
  // Alert details
  title: string;
  description: string;
  threshold: number;
  currentValue: number;
  
  // Kubernetes context
  namespace: string;
  workload?: string;
  cluster: string;
  
  // Actions
  recommendations: string[];
  actionUrl?: string;
  
  // Metadata
  tenantId: string;
  createdAt: string;
  resolvedAt?: string;
  metadata: Record<string, unknown>;
}

export interface CostTrend {
  resourceType: ResourceType;
  namespace: string;
  workload?: string;
  
  // Trend data
  dataPoints: Array<{
    timestamp: string;
    value: number;
    [key: string]: unknown;
  }>;
  trendDirection: TrendDirection;
  trendPercentage: number;
  
  // Forecasting
  forecastPoints: Array<{
    timestamp: string;
    value: number;
    confidence?: number;
  }>;
  forecastConfidence: number;
  
  // Period
  periodStart: string;
  periodEnd: string;
  tenantId: string;
}

export interface OpenCostMetrics {
  cluster: string;
  totalCost: number;
  costByNamespace: Record<string, number>;
  costByWorkload: Record<string, number>;
  costByService: Record<string, number>;
  
  // Resource breakdown
  cpuCostTotal: number;
  memoryCostTotal: number;
  storageCostTotal: number;
  networkCostTotal: number;
  
  // Efficiency
  overallEfficiency: number;
  wastedCost: number;
  optimizationPotential: number;
  
  // Time period
  periodStart: string;
  periodEnd: string;
  tenantId: string;
  lastUpdated: string;
}

// API Request/Response models
export interface CostQueryRequest {
  cluster?: string;
  namespace?: string;
  workload?: string;
  service?: string;
  startTime: string;
  endTime: string;
  aggregation?: string;
  includeRecommendations?: boolean;
}

export interface CostQueryResponse {
  success: boolean;
  costs: KubernetesCost[];
  totalCost: number;
  costBreakdown: Record<string, number>;
  trends: CostTrend[];
  recommendations: CostOptimization[];
  queryMetadata: Record<string, unknown>;
}

export interface CostAlertRequest {
  type: CostAlertType;
  threshold: number;
  namespace: string;
  workload?: string;
  cluster: string;
  notificationChannels?: string[];
  metadata?: Record<string, unknown>;
}

export interface CostAlertResponse {
  success: boolean;
  alert: CostAlert;
  created: boolean;
}

export interface CostOptimizationRequest {
  cluster?: string;
  namespace?: string;
  workload?: string;
  optimizationTypes?: OptimizationType[];
  timeRangeDays?: number;
  minSavingsThreshold?: number;
}

export interface CostOptimizationResponse {
  success: boolean;
  optimizations: CostOptimization[];
  totalPotentialSavings: number;
  implementationPriority: string[];
  analysisMetadata: Record<string, unknown>;
}

export interface CostReportRequest {
  reportType: 'chargeback' | 'showback' | 'allocation' | 'trend';
  cluster?: string;
  namespaces?: string[];
  startTime: string;
  endTime: string;
  groupBy?: string[];
  includeForecasts?: boolean;
}

export interface CostReportResponse {
  success: boolean;
  reportData: Record<string, unknown>;
  summary: Record<string, number>;
  charts: Array<{
    type: string;
    title: string;
    data: Record<string, unknown>;
  }>;
  exportUrls: Record<string, string>;
  generatedAt: string;
}

// UI-specific types
export interface CostDashboardFilters {
  cluster?: string;
  namespace?: string;
  workload?: string;
  timeRange: {
    from: string;
    to: string;
  };
  groupBy: 'namespace' | 'workload' | 'service';
}

export interface CostChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string[];
    borderColor?: string;
    borderWidth?: number;
  }>;
}

export interface CostSummaryCard {
  title: string;
  value: number;
  unit: string;
  trend?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  };
  color?: 'primary' | 'success' | 'warning' | 'danger';
}