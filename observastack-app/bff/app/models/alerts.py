"""Alert management Pydantic models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .common import BaseResponse, SeverityLevel, StatusEnum

class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"

class AlertSource(str, Enum):
    """Alert source enumeration."""
    PROMETHEUS = "prometheus"
    LOKI = "loki"
    TEMPO = "tempo"
    OPENSEARCH = "opensearch"
    EXTERNAL = "external"

class Alert(BaseModel):
    """Alert model."""
    id: str
    severity: SeverityLevel
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    source: AlertSource
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    assignee: Optional[str] = None
    tenant_id: str
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    fingerprint: str = Field(description="Unique identifier for alert deduplication")
    generator_url: Optional[str] = None
    silence_id: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    updated_at: datetime

class AlertGroup(BaseModel):
    """Alert group model."""
    id: str
    alerts: List[Alert]
    common_labels: Dict[str, str] = Field(default_factory=dict)
    group_key: str
    status: AlertStatus
    created_at: datetime
    updated_at: datetime

class AlertRule(BaseModel):
    """Alert rule model."""
    id: str
    name: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1)
    condition: str = Field(description="Alert condition expression")
    threshold: float
    duration: str = Field(pattern="^[0-9]+[smhd]$", description="Duration (e.g., '5m', '1h')")
    severity: SeverityLevel
    enabled: bool = True
    tenant_id: str
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class AlertWebhookPayload(BaseModel):
    """Webhook payload for incoming alerts."""
    version: str = Field(default="4")
    group_key: str
    status: str
    receiver: str
    group_labels: Dict[str, str] = Field(default_factory=dict)
    common_labels: Dict[str, str] = Field(default_factory=dict)
    common_annotations: Dict[str, str] = Field(default_factory=dict)
    external_url: str
    alerts: List[Dict[str, Any]]

class AlertActionRequest(BaseModel):
    """Alert action request model."""
    alert_ids: List[str] = Field(min_length=1)
    action: str = Field(pattern="^(acknowledge|resolve|assign|silence)$")
    assignee: Optional[str] = None
    comment: Optional[str] = Field(None, max_length=1000)
    silence_duration: Optional[str] = Field(None, pattern="^[0-9]+[smhd]$")

class AlertActionResponse(BaseResponse):
    """Alert action response model."""
    success: bool = True
    message: str = "Action completed"
    affected_alerts: int
    failed_alerts: List[str] = Field(default_factory=list)

class AlertQuery(BaseModel):
    """Alert query parameters."""
    status: Optional[List[AlertStatus]] = None
    severity: Optional[List[SeverityLevel]] = None
    source: Optional[List[AlertSource]] = None
    assignee: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="timestamp")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class AlertsResponse(BaseResponse):
    """Alerts list response model."""
    success: bool = True
    message: str = "Alerts retrieved successfully"
    alerts: List[Alert]
    total: int
    groups: Optional[List[AlertGroup]] = None

class AlertStatistics(BaseModel):
    """Alert statistics model."""
    total: int
    by_status: Dict[AlertStatus, int]
    by_severity: Dict[SeverityLevel, int]
    by_source: Dict[AlertSource, int]
    resolution_time_avg: Optional[float] = None  # Average resolution time in minutes
    mttr: Optional[float] = None  # Mean Time To Resolution in minutes

class AlertNotificationChannel(BaseModel):
    """Alert notification channel model."""
    id: str
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(pattern="^(email|slack|webhook|pagerduty|teams)$")
    config: Dict[str, Any]
    enabled: bool = True
    tenant_id: str
    created_at: datetime
    updated_at: datetime

class AlertNotificationRule(BaseModel):
    """Alert notification rule model."""
    id: str
    name: str = Field(min_length=1, max_length=100)
    conditions: Dict[str, Any] = Field(description="Conditions for triggering notification")
    channels: List[str] = Field(description="List of notification channel IDs")
    enabled: bool = True
    tenant_id: str
    created_at: datetime
    updated_at: datetime

class SilenceRequest(BaseModel):
    """Silence request model."""
    matchers: List[Dict[str, str]] = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime
    created_by: str
    comment: str = Field(max_length=1000)

class Silence(BaseModel):
    """Silence model."""
    id: str
    matchers: List[Dict[str, str]]
    starts_at: datetime
    ends_at: datetime
    created_by: str
    comment: str
    status: str = Field(pattern="^(active|pending|expired)$")
    created_at: datetime
    updated_at: datetime

class AlertEscalationRule(BaseModel):
    """Alert escalation rule model."""
    id: str
    name: str = Field(min_length=1, max_length=100)
    conditions: Dict[str, Any]
    escalation_delay: str = Field(pattern="^[0-9]+[smhd]$")
    target_channels: List[str]
    enabled: bool = True
    tenant_id: str
    created_at: datetime
    updated_at: datetime