"""Insights and analytics Pydantic models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .common import BaseResponse, SeverityLevel, TrendDirection

class InsightCategory(str, Enum):
    """Insight category enumeration."""
    COST = "cost"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    SECURITY = "security"
    CAPACITY = "capacity"

class RecommendationType(str, Enum):
    """Recommendation type enumeration."""
    RIGHTSIZING = "rightsizing"
    SCHEDULING = "scheduling"
    STORAGE = "storage"
    NETWORKING = "networking"
    SCALING = "scaling"
    OPTIMIZATION = "optimization"

class ImpactLevel(str, Enum):
    """Impact level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EffortLevel(str, Enum):
    """Effort level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TimePeriod(str, Enum):
    """Time period enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class InsightMetric(BaseModel):
    """Insight metric model."""
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(default="")
    trend: TrendDirection
    recommendation: Optional[str] = Field(None, max_length=500)
    severity: SeverityLevel
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Recommendation(BaseModel):
    """Recommendation model."""
    id: str
    type: RecommendationType
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    impact: ImpactLevel
    effort: EffortLevel
    estimated_savings: float = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    expires_at: Optional[datetime] = None

class CostInsight(BaseModel):
    """Cost insight model."""
    category: str = Field(min_length=1)
    current_cost: float = Field(ge=0)
    projected_cost: float = Field(ge=0)
    savings_opportunity: float = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    period: TimePeriod
    recommendations: List[Recommendation] = Field(default_factory=list)
    timestamp: datetime
    confidence_score: float = Field(ge=0, le=1)
    data_sources: List[str] = Field(default_factory=list)

class ResourceUtilization(BaseModel):
    """Resource utilization model."""
    resource: str = Field(min_length=1)
    current: float = Field(ge=0)
    capacity: float = Field(ge=0)
    utilization: float = Field(ge=0, le=100, description="Utilization percentage")
    trend: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    threshold_breaches: int = Field(ge=0)
    last_updated: datetime

class PerformanceInsight(BaseModel):
    """Performance insight model."""
    service: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    current_value: float
    baseline_value: float
    deviation_percentage: float
    severity: SeverityLevel
    trend: TrendDirection
    recommendations: List[Recommendation] = Field(default_factory=list)
    affected_endpoints: List[str] = Field(default_factory=list)
    timestamp: datetime

class CapacityForecast(BaseModel):
    """Capacity forecast model."""
    resource: str = Field(min_length=1)
    current_usage: float = Field(ge=0)
    projected_usage: float = Field(ge=0)
    capacity_limit: float = Field(ge=0)
    forecast_period: TimePeriod
    confidence_interval: Dict[str, float] = Field(default_factory=dict)
    breach_probability: float = Field(ge=0, le=1)
    recommended_actions: List[Recommendation] = Field(default_factory=list)
    model_accuracy: float = Field(ge=0, le=1)
    created_at: datetime

class AnomalyDetection(BaseModel):
    """Anomaly detection model."""
    id: str
    service: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    anomaly_score: float = Field(ge=0, le=1)
    severity: SeverityLevel
    description: str = Field(max_length=1000)
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    root_cause: Optional[str] = Field(None, max_length=500)
    related_alerts: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InsightsDashboardRequest(BaseModel):
    """Insights dashboard request model."""
    categories: Optional[List[InsightCategory]] = None
    time_range: Optional[Dict[str, str]] = None
    services: Optional[List[str]] = None
    severity_filter: Optional[List[SeverityLevel]] = None
    include_recommendations: bool = True

class InsightsDashboardResponse(BaseResponse):
    """Insights dashboard response model."""
    cost_insights: List[CostInsight] = Field(default_factory=list)
    performance_insights: List[PerformanceInsight] = Field(default_factory=list)
    capacity_forecasts: List[CapacityForecast] = Field(default_factory=list)
    anomalies: List[AnomalyDetection] = Field(default_factory=list)
    resource_utilization: List[ResourceUtilization] = Field(default_factory=list)
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class CostOptimizationRequest(BaseModel):
    """Cost optimization request model."""
    services: Optional[List[str]] = None
    time_range: Dict[str, str]
    optimization_goals: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)

class CostOptimizationResponse(BaseResponse):
    """Cost optimization response model."""
    current_cost: float
    optimized_cost: float
    potential_savings: float
    savings_percentage: float
    recommendations: List[Recommendation]
    implementation_plan: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)

class TrendAnalysisRequest(BaseModel):
    """Trend analysis request model."""
    metrics: List[str] = Field(min_length=1)
    time_range: Dict[str, str]
    services: Optional[List[str]] = None
    aggregation: str = Field(default="avg", pattern="^(avg|sum|min|max|count)$")
    granularity: str = Field(default="1h", pattern="^[0-9]+[smhd]$")

class TrendAnalysisResponse(BaseResponse):
    """Trend analysis response model."""
    trends: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    correlations: Dict[str, float] = Field(default_factory=dict)
    forecasts: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)

class BenchmarkingRequest(BaseModel):
    """Benchmarking request model."""
    service: str = Field(min_length=1)
    metrics: List[str] = Field(min_length=1)
    time_range: Dict[str, str]
    comparison_type: str = Field(pattern="^(historical|peer|industry)$")

class BenchmarkingResponse(BaseResponse):
    """Benchmarking response model."""
    service: str
    benchmarks: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    performance_score: float = Field(ge=0, le=100)
    recommendations: List[Recommendation] = Field(default_factory=list)
    comparison_data: Dict[str, Any] = Field(default_factory=dict)