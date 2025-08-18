"""System and health monitoring Pydantic models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .common import BaseResponse, HealthStatus

class ServiceStatus(str, Enum):
    """Service status enumeration."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

class ServiceHealth(BaseModel):
    """Service health model."""
    name: str = Field(min_length=1)
    status: ServiceStatus
    latency: Optional[float] = Field(None, ge=0, description="Response latency in milliseconds")
    error_rate: Optional[float] = Field(None, ge=0, le=100, description="Error rate percentage")
    last_check: datetime
    uptime: Optional[float] = Field(None, ge=0, description="Uptime percentage")
    version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemHealth(BaseResponse):
    """System health response model."""
    status: HealthStatus
    services: List[ServiceHealth]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_uptime: Optional[float] = Field(None, ge=0, le=100)
    active_incidents: int = Field(ge=0)

class FeatureFlag(BaseModel):
    """Feature flag model."""
    name: str = Field(min_length=1)
    enabled: bool
    description: str = Field(max_length=500)
    rollout_percentage: Optional[float] = Field(None, ge=0, le=100)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class SystemConfiguration(BaseModel):
    """System configuration model."""
    key: str = Field(min_length=1)
    value: Any
    description: Optional[str] = Field(None, max_length=500)
    is_secret: bool = False
    category: str = Field(default="general")
    updated_at: datetime
    updated_by: str

class SystemMetrics(BaseModel):
    """System metrics model."""
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    disk_usage: float = Field(ge=0, le=100)
    network_io: Dict[str, float] = Field(default_factory=dict)
    active_connections: int = Field(ge=0)
    request_rate: float = Field(ge=0)
    error_rate: float = Field(ge=0, le=100)
    response_time_p95: float = Field(ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: str
    user_id: str
    tenant_id: str
    action: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None

class AuditLogQuery(BaseModel):
    """Audit log query parameters."""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    success: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class AuditLogResponse(BaseResponse):
    """Audit log response model."""
    entries: List[AuditLogEntry]
    total: int

class SystemAlert(BaseModel):
    """System alert model."""
    id: str
    type: str = Field(pattern="^(performance|security|capacity|error)$")
    severity: str = Field(pattern="^(critical|high|medium|low)$")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    service: Optional[str] = None
    metric: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

class MaintenanceWindow(BaseModel):
    """Maintenance window model."""
    id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    services: List[str] = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    created_by: str
    status: str = Field(pattern="^(scheduled|active|completed|cancelled)$")
    impact_level: str = Field(pattern="^(none|low|medium|high)$")
    notification_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BackupStatus(BaseModel):
    """Backup status model."""
    id: str
    type: str = Field(pattern="^(full|incremental|differential)$")
    status: str = Field(pattern="^(running|completed|failed|cancelled)$")
    started_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: Optional[int] = Field(None, ge=0)
    location: str
    retention_days: int = Field(ge=1)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemInfo(BaseResponse):
    """System information response model."""
    version: str
    build_date: str
    commit_hash: str
    environment: str = Field(pattern="^(development|staging|production)$")
    uptime: float = Field(ge=0, description="Uptime in seconds")
    features: List[FeatureFlag] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    resource_limits: Dict[str, Any] = Field(default_factory=dict)

class DatabaseHealth(BaseModel):
    """Database health model."""
    name: str = Field(min_length=1)
    status: ServiceStatus
    connection_count: int = Field(ge=0)
    query_performance: Dict[str, float] = Field(default_factory=dict)
    storage_usage: float = Field(ge=0, le=100)
    replication_lag: Optional[float] = Field(None, ge=0)
    last_backup: Optional[datetime] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)

class CacheHealth(BaseModel):
    """Cache health model."""
    name: str = Field(min_length=1)
    status: ServiceStatus
    hit_rate: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    eviction_rate: float = Field(ge=0)
    connection_count: int = Field(ge=0)
    last_check: datetime = Field(default_factory=datetime.utcnow)

class QueueHealth(BaseModel):
    """Queue health model."""
    name: str = Field(min_length=1)
    status: ServiceStatus
    message_count: int = Field(ge=0)
    consumer_count: int = Field(ge=0)
    processing_rate: float = Field(ge=0)
    error_rate: float = Field(ge=0, le=100)
    oldest_message_age: Optional[float] = Field(None, ge=0)
    last_check: datetime = Field(default_factory=datetime.utcnow)