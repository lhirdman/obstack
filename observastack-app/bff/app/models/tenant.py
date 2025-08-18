"""Tenant management Pydantic models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from .common import BaseResponse


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class DataRetentionPolicy(BaseModel):
    """Data retention policy configuration."""
    logs_retention_days: int = Field(default=30, ge=1, le=3650, description="Log retention in days")
    metrics_retention_days: int = Field(default=90, ge=1, le=3650, description="Metrics retention in days")
    traces_retention_days: int = Field(default=14, ge=1, le=365, description="Traces retention in days")
    alerts_retention_days: int = Field(default=365, ge=1, le=3650, description="Alerts retention in days")
    cost_data_retention_days: int = Field(default=730, ge=1, le=3650, description="Cost data retention in days")


class TenantSettings(BaseModel):
    """Tenant-specific settings and configuration."""
    max_users: int = Field(default=10, ge=1, le=1000, description="Maximum number of users")
    max_dashboards: int = Field(default=50, ge=1, le=500, description="Maximum number of dashboards")
    max_alerts: int = Field(default=100, ge=1, le=1000, description="Maximum number of alerts")
    features_enabled: List[str] = Field(default_factory=list, description="Enabled feature flags")
    custom_branding: Dict[str, Any] = Field(default_factory=dict, description="Custom branding configuration")
    notification_settings: Dict[str, Any] = Field(default_factory=dict, description="Notification preferences")
    cost_budget_monthly: Optional[float] = Field(None, ge=0, description="Monthly cost budget in USD")
    cost_alert_threshold: float = Field(default=0.8, ge=0.1, le=1.0, description="Cost alert threshold (0.1-1.0)")


class TenantCreate(BaseModel):
    """Tenant creation request model."""
    name: str = Field(min_length=1, max_length=100, description="Tenant display name")
    domain: str = Field(min_length=1, max_length=100, description="Tenant domain identifier")
    description: Optional[str] = Field(None, max_length=500, description="Tenant description")
    admin_email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Admin user email")
    admin_username: str = Field(min_length=1, max_length=50, description="Admin username")
    settings: Optional[TenantSettings] = Field(default_factory=TenantSettings, description="Tenant settings")
    retention_policy: Optional[DataRetentionPolicy] = Field(default_factory=DataRetentionPolicy, description="Data retention policy")

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        """Validate domain format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Domain must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()


class TenantUpdate(BaseModel):
    """Tenant update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tenant display name")
    description: Optional[str] = Field(None, max_length=500, description="Tenant description")
    status: Optional[TenantStatus] = Field(None, description="Tenant status")
    settings: Optional[TenantSettings] = Field(None, description="Tenant settings")
    retention_policy: Optional[DataRetentionPolicy] = Field(None, description="Data retention policy")


class Tenant(BaseResponse):
    """Tenant response model."""
    id: str = Field(description="Unique tenant identifier")
    name: str = Field(description="Tenant display name")
    domain: str = Field(description="Tenant domain identifier")
    description: Optional[str] = Field(None, description="Tenant description")
    status: TenantStatus = Field(description="Current tenant status")
    settings: TenantSettings = Field(description="Tenant settings")
    retention_policy: DataRetentionPolicy = Field(description="Data retention policy")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    user_count: int = Field(default=0, description="Number of users in tenant")
    storage_usage_mb: float = Field(default=0.0, description="Storage usage in MB")
    monthly_cost: Optional[float] = Field(None, description="Current monthly cost in USD")


class TenantList(BaseResponse):
    """Tenant list response model."""
    tenants: List[Tenant] = Field(description="List of tenants")
    total: int = Field(description="Total number of tenants")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Number of items per page")


class TenantStats(BaseResponse):
    """Tenant statistics response model."""
    tenant_id: str = Field(description="Tenant identifier")
    user_count: int = Field(description="Number of users")
    dashboard_count: int = Field(description="Number of dashboards")
    alert_count: int = Field(description="Number of active alerts")
    storage_usage_mb: float = Field(description="Storage usage in MB")
    monthly_cost: Optional[float] = Field(None, description="Current monthly cost")
    cost_trend: Optional[str] = Field(None, description="Cost trend (up/down/stable)")
    last_activity: Optional[datetime] = Field(None, description="Last user activity")


class TenantUsageMetrics(BaseResponse):
    """Tenant usage metrics response model."""
    tenant_id: str = Field(description="Tenant identifier")
    period_start: datetime = Field(description="Metrics period start")
    period_end: datetime = Field(description="Metrics period end")
    log_volume_mb: float = Field(description="Log volume in MB")
    metric_points: int = Field(description="Number of metric data points")
    trace_spans: int = Field(description="Number of trace spans")
    api_requests: int = Field(description="Number of API requests")
    active_users: int = Field(description="Number of active users in period")
    cost_breakdown: Dict[str, float] = Field(default_factory=dict, description="Cost breakdown by service")


class TenantAuditLog(BaseResponse):
    """Tenant audit log entry model."""
    id: str = Field(description="Audit log entry ID")
    tenant_id: str = Field(description="Tenant identifier")
    user_id: str = Field(description="User who performed the action")
    action: str = Field(description="Action performed")
    resource_type: str = Field(description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of affected resource")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional action details")
    timestamp: datetime = Field(description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class TenantAuditLogList(BaseResponse):
    """Tenant audit log list response model."""
    logs: List[TenantAuditLog] = Field(description="List of audit log entries")
    total: int = Field(description="Total number of log entries")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of items per page")


class UserManagement(BaseModel):
    """User management request model."""
    user_id: str = Field(description="User identifier")
    action: str = Field(description="Action to perform (activate, deactivate, delete)")
    reason: Optional[str] = Field(None, description="Reason for the action")


class RoleManagement(BaseModel):
    """Role management request model."""
    user_id: str = Field(description="User identifier")
    roles: List[str] = Field(description="List of role names to assign")
    replace: bool = Field(default=False, description="Replace existing roles or add to them")


class TenantHealthCheck(BaseResponse):
    """Tenant health check response model."""
    tenant_id: str = Field(description="Tenant identifier")
    status: str = Field(description="Overall health status")
    services: Dict[str, str] = Field(description="Individual service health status")
    storage_health: Dict[str, Any] = Field(description="Storage system health")
    cost_health: Dict[str, Any] = Field(description="Cost monitoring health")
    last_check: datetime = Field(description="Last health check timestamp")
    issues: List[str] = Field(default_factory=list, description="List of identified issues")