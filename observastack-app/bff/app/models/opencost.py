"""OpenCost integration Pydantic models for Kubernetes cost monitoring."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .common import BaseResponse, SeverityLevel

class ResourceType(str, Enum):
    """Kubernetes resource type enumeration."""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"

class CostAlertType(str, Enum):
    """Cost alert type enumeration."""
    BUDGET_EXCEEDED = "budget_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    EFFICIENCY_LOW = "efficiency_low"
    WASTE_DETECTED = "waste_detected"
    THRESHOLD_BREACH = "threshold_breach"

class OptimizationType(str, Enum):
    """Cost optimization type enumeration."""
    RIGHTSIZING = "rightsizing"
    SCHEDULING = "scheduling"
    STORAGE = "storage"
    NETWORKING = "networking"
    WORKLOAD_OPTIMIZATION = "workload_optimization"

class ImplementationEffort(str, Enum):
    """Implementation effort level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CostAllocation(BaseModel):
    """Cost allocation model for Kubernetes resources."""
    resource_type: ResourceType
    allocated_cost: float = Field(ge=0, description="Cost allocated to this resource")
    actual_usage: float = Field(ge=0, description="Actual resource usage")
    efficiency: float = Field(ge=0, le=100, description="Resource efficiency percentage")
    wasted_cost: float = Field(ge=0, description="Cost of unused resources")
    optimization_potential: float = Field(ge=0, description="Potential cost savings")
    currency: str = Field(default="USD", max_length=3)
    period_start: datetime
    period_end: datetime
    tenant_id: str = Field(min_length=1, description="Tenant identifier for isolation")

class KubernetesCost(BaseModel):
    """Kubernetes cost model for workloads and services."""
    namespace: str = Field(min_length=1, description="Kubernetes namespace")
    workload: str = Field(min_length=1, description="Workload name (deployment, statefulset, etc.)")
    service: Optional[str] = Field(None, description="Service name if applicable")
    cluster: str = Field(min_length=1, description="Kubernetes cluster name")
    
    # Cost breakdown by resource type
    cpu_cost: float = Field(ge=0, description="CPU cost for the period")
    memory_cost: float = Field(ge=0, description="Memory cost for the period")
    storage_cost: float = Field(ge=0, description="Storage cost for the period")
    network_cost: float = Field(ge=0, description="Network cost for the period")
    gpu_cost: float = Field(ge=0, default=0, description="GPU cost for the period")
    total_cost: float = Field(ge=0, description="Total cost for all resources")
    
    # Efficiency and optimization metrics
    efficiency: float = Field(ge=0, le=100, description="Overall resource efficiency percentage")
    recommendations: List["CostOptimization"] = Field(default_factory=list)
    
    # Metadata and context
    currency: str = Field(default="USD", max_length=3)
    period_start: datetime
    period_end: datetime
    tenant_id: str = Field(min_length=1, description="Tenant identifier for isolation")
    labels: Dict[str, str] = Field(default_factory=dict, description="Kubernetes labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Kubernetes annotations")
    
    # Resource requests and limits
    cpu_request: Optional[float] = Field(None, ge=0, description="CPU request in cores")
    memory_request: Optional[float] = Field(None, ge=0, description="Memory request in bytes")
    cpu_limit: Optional[float] = Field(None, ge=0, description="CPU limit in cores")
    memory_limit: Optional[float] = Field(None, ge=0, description="Memory limit in bytes")

class CostOptimization(BaseModel):
    """Cost optimization recommendation model."""
    type: OptimizationType
    title: str = Field(min_length=1, max_length=200, description="Optimization title")
    description: str = Field(max_length=2000, description="Detailed description")
    potential_savings: float = Field(ge=0, description="Estimated cost savings")
    implementation_effort: ImplementationEffort
    risk_level: RiskLevel
    steps: List[str] = Field(min_length=1, description="Implementation steps")
    
    # Resource-specific recommendations
    current_resources: Dict[str, float] = Field(default_factory=dict)
    recommended_resources: Dict[str, float] = Field(default_factory=dict)
    
    # Metadata
    confidence_score: float = Field(ge=0, le=1, description="Confidence in recommendation")
    impact_analysis: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CostAlert(BaseModel):
    """Cost alert model for threshold breaches and anomalies."""
    id: str = Field(min_length=1, description="Unique alert identifier")
    type: CostAlertType
    severity: SeverityLevel
    
    # Alert details
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=1000)
    threshold: float = Field(ge=0, description="Alert threshold value")
    current_value: float = Field(ge=0, description="Current metric value")
    
    # Kubernetes context
    namespace: str = Field(min_length=1)
    workload: Optional[str] = Field(None)
    cluster: str = Field(min_length=1)
    
    # Recommendations and actions
    recommendations: List[str] = Field(default_factory=list)
    action_url: Optional[str] = Field(None, description="URL for remediation actions")
    
    # Metadata
    tenant_id: str = Field(min_length=1, description="Tenant identifier for isolation")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CostTrend(BaseModel):
    """Cost trend analysis model."""
    resource_type: ResourceType
    namespace: str = Field(min_length=1)
    workload: Optional[str] = None
    
    # Trend data points
    data_points: List[Dict[str, Any]] = Field(min_length=1, description="Time series data points")
    trend_direction: str = Field(pattern="^(increasing|decreasing|stable)$")
    trend_percentage: float = Field(description="Percentage change over period")
    
    # Forecasting
    forecast_points: List[Dict[str, Any]] = Field(default_factory=list)
    forecast_confidence: float = Field(ge=0, le=1, default=0.0)
    
    # Analysis period
    period_start: datetime
    period_end: datetime
    tenant_id: str = Field(min_length=1)

class OpenCostMetrics(BaseModel):
    """OpenCost metrics aggregation model."""
    cluster: str = Field(min_length=1)
    total_cost: float = Field(ge=0)
    cost_by_namespace: Dict[str, float] = Field(default_factory=dict)
    cost_by_workload: Dict[str, float] = Field(default_factory=dict)
    cost_by_service: Dict[str, float] = Field(default_factory=dict)
    
    # Resource breakdown
    cpu_cost_total: float = Field(ge=0)
    memory_cost_total: float = Field(ge=0)
    storage_cost_total: float = Field(ge=0)
    network_cost_total: float = Field(ge=0)
    
    # Efficiency metrics
    overall_efficiency: float = Field(ge=0, le=100)
    wasted_cost: float = Field(ge=0)
    optimization_potential: float = Field(ge=0)
    
    # Time period
    period_start: datetime
    period_end: datetime
    tenant_id: str = Field(min_length=1)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Request/Response models for API endpoints

class CostQueryRequest(BaseModel):
    """Request model for querying cost data."""
    cluster: Optional[str] = None
    namespace: Optional[str] = None
    workload: Optional[str] = None
    service: Optional[str] = None
    start_time: datetime
    end_time: datetime
    aggregation: str = Field(default="1h", pattern="^[0-9]+[smhd]$")
    include_recommendations: bool = Field(default=True)

class CostQueryResponse(BaseResponse):
    """Response model for cost data queries."""
    costs: List[KubernetesCost] = Field(default_factory=list)
    total_cost: float = Field(ge=0)
    cost_breakdown: Dict[str, float] = Field(default_factory=dict)
    trends: List[CostTrend] = Field(default_factory=list)
    recommendations: List[CostOptimization] = Field(default_factory=list)
    query_metadata: Dict[str, Any] = Field(default_factory=dict)

class CostAlertRequest(BaseModel):
    """Request model for creating cost alerts."""
    type: CostAlertType
    threshold: float = Field(gt=0)
    namespace: str = Field(min_length=1)
    workload: Optional[str] = None
    cluster: str = Field(min_length=1)
    notification_channels: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CostAlertResponse(BaseResponse):
    """Response model for cost alert operations."""
    alert: CostAlert
    created: bool = Field(default=True)

class CostOptimizationRequest(BaseModel):
    """Request model for cost optimization analysis."""
    cluster: Optional[str] = None
    namespace: Optional[str] = None
    workload: Optional[str] = None
    optimization_types: List[OptimizationType] = Field(default_factory=list)
    time_range_days: int = Field(default=7, ge=1, le=90)
    min_savings_threshold: float = Field(default=0.0, ge=0)

class CostOptimizationResponse(BaseResponse):
    """Response model for cost optimization analysis."""
    optimizations: List[CostOptimization] = Field(default_factory=list)
    total_potential_savings: float = Field(ge=0)
    implementation_priority: List[str] = Field(default_factory=list)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)

class CostReportRequest(BaseModel):
    """Request model for cost reporting."""
    report_type: str = Field(pattern="^(chargeback|showback|allocation|trend)$")
    cluster: Optional[str] = None
    namespaces: Optional[List[str]] = None
    start_time: datetime
    end_time: datetime
    group_by: List[str] = Field(default_factory=list)
    include_forecasts: bool = Field(default=False)

class CostReportResponse(BaseResponse):
    """Response model for cost reports."""
    report_data: Dict[str, Any] = Field(default_factory=dict)
    summary: Dict[str, float] = Field(default_factory=dict)
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    export_urls: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Update forward references
KubernetesCost.model_rebuild()
CostOptimization.model_rebuild()