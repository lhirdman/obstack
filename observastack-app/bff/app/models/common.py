"""Common Pydantic models and base classes."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )

class ApiResponse(BaseResponse, Generic[T]):
    """Generic API response wrapper."""
    data: T
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ApiError(BaseResponse):
    """API error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str

class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model."""
    items: List[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=1000)
    has_next: bool
    has_previous: bool

class TimeRange(BaseModel):
    """Time range model for queries."""
    from_time: str = Field(alias="from", description="Start time (ISO 8601 or relative)")
    to_time: str = Field(alias="to", description="End time (ISO 8601 or relative)")

class SeverityLevel(str, Enum):
    """Severity levels for alerts and insights."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class StatusEnum(str, Enum):
    """Generic status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

class TrendDirection(str, Enum):
    """Trend direction enumeration."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UP = "up"
    DOWN = "down"

class Permission(BaseModel):
    """Permission model."""
    resource: str
    actions: List[str]

class Role(BaseModel):
    """Role model."""
    id: str
    name: str
    permissions: List[Permission]

class UserPreferences(BaseModel):
    """User preferences model."""
    theme: str = Field(default="system", pattern="^(light|dark|system)$")
    timezone: str = Field(default="UTC")
    default_time_range: TimeRange
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict)

class BrandingSettings(BaseModel):
    """Branding settings for tenants."""
    logo: Optional[str] = None
    primary_color: str = Field(pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(pattern="^#[0-9A-Fa-f]{6}$")
    custom_css: Optional[str] = None

class FeatureFlags(BaseModel):
    """Feature flags model."""
    sso: bool = False
    opensearch: bool = False
    cost_insights: bool = False
    alerting: bool = True
    custom_dashboards: bool = False

class GrafanaIntegration(BaseModel):
    """Grafana integration settings."""
    url: str = Field(pattern="^https?://")
    enabled: bool = True
    embed_auth: bool = True

class KeycloakIntegration(BaseModel):
    """Keycloak integration settings."""
    realm: str
    client_id: str
    enabled: bool = True

class AlertmanagerIntegration(BaseModel):
    """Alertmanager integration settings."""
    url: str = Field(pattern="^https?://")
    enabled: bool = True
    webhook_secret: Optional[str] = None

class IntegrationSettings(BaseModel):
    """Integration settings model."""
    grafana: GrafanaIntegration
    keycloak: KeycloakIntegration
    alertmanager: AlertmanagerIntegration

class RetentionPolicy(BaseModel):
    """Data retention policy model."""
    logs: int = Field(ge=1, le=3650, description="Log retention in days")
    metrics: int = Field(ge=1, le=3650, description="Metrics retention in days")
    traces: int = Field(ge=1, le=365, description="Traces retention in days")
    alerts: int = Field(ge=1, le=365, description="Alerts retention in days")

class TenantSettings(BaseModel):
    """Tenant settings model."""
    branding: BrandingSettings
    features: FeatureFlags
    integrations: IntegrationSettings

class Tenant(BaseModel):
    """Tenant model."""
    id: str
    name: str = Field(min_length=1, max_length=100)
    domain: str = Field(pattern="^[a-zA-Z0-9.-]+$")
    settings: TenantSettings
    data_retention: RetentionPolicy

class User(BaseModel):
    """User model."""
    id: str
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(pattern="^[^@]+@[^@]+\.[^@]+$")
    tenant_id: str
    roles: List[Role]
    preferences: UserPreferences