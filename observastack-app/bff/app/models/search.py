"""Search-related Pydantic models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
from .common import BaseResponse

class SearchType(str, Enum):
    """Search type enumeration."""
    LOGS = "logs"
    METRICS = "metrics"
    TRACES = "traces"
    ALL = "all"

class SearchOperator(str, Enum):
    """Search filter operator enumeration."""
    EQUALS = "equals"
    CONTAINS = "contains"
    REGEX = "regex"
    RANGE = "range"
    EXISTS = "exists"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"

class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"

class MetricType(str, Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class TraceStatus(str, Enum):
    """Trace status enumeration."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"

class TimeRange(BaseModel):
    """Time range model for search queries."""
    start: datetime = Field(description="Start time")
    end: datetime = Field(description="End time")

class SearchFilter(BaseModel):
    """Search filter model."""
    field: str = Field(min_length=1)
    operator: SearchOperator
    value: Union[str, int, float, bool, List[Union[str, int, float]]]

class SearchQuery(BaseModel):
    """Search query request model."""
    free_text: str = Field(default="", description="Free text search query")
    type: SearchType = SearchType.ALL
    time_range: TimeRange
    filters: List[SearchFilter] = Field(default_factory=list)
    tenant_id: str
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = Field(default="timestamp")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class LogItem(BaseModel):
    """Log item model."""
    message: str
    level: LogLevel
    labels: Dict[str, str] = Field(default_factory=dict)
    fields: Dict[str, Any] = Field(default_factory=dict)

class MetricItem(BaseModel):
    """Metric item model."""
    name: str
    value: float
    unit: str = Field(default="")
    labels: Dict[str, str] = Field(default_factory=dict)
    type: MetricType

class TraceItem(BaseModel):
    """Trace item model."""
    trace_id: str
    span_id: str
    operation_name: str
    duration: int = Field(ge=0, description="Duration in microseconds")
    status: TraceStatus
    tags: Dict[str, str] = Field(default_factory=dict)
    parent_span_id: Optional[str] = None

class SearchItem(BaseModel):
    """Search result item model."""
    id: str
    timestamp: datetime
    source: SearchType
    service: str
    content: Union[LogItem, MetricItem, TraceItem]
    correlation_id: Optional[str] = None
    tenant_id: str

class SearchStats(BaseModel):
    """Search statistics model."""
    matched: int = Field(ge=0)
    scanned: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    sources: Dict[str, int] = Field(default_factory=dict)
    query_cost: Optional[float] = None

class SearchFacetValue(BaseModel):
    """Search facet value model."""
    value: str
    count: int = Field(ge=0)

class SearchFacet(BaseModel):
    """Search facet model."""
    field: str
    values: List[SearchFacetValue]

class SearchResult(BaseResponse):
    """Search result response model."""
    items: List[SearchItem]
    stats: SearchStats
    facets: List[SearchFacet] = Field(default_factory=list)
    next_token: Optional[str] = None

class StreamingSearchChunk(BaseModel):
    """Streaming search chunk model."""
    chunk_id: int
    items: List[SearchItem]
    is_final: bool = False
    stats: Optional[SearchStats] = None

class SavedSearchRequest(BaseModel):
    """Saved search request model."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    query: SearchQuery
    is_public: bool = False

class SavedSearch(BaseResponse):
    """Saved search model."""
    id: str
    name: str
    description: Optional[str] = None
    query: SearchQuery
    is_public: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    tenant_id: str

class SearchHistoryItem(BaseModel):
    """Search history item model."""
    id: str
    query: SearchQuery
    executed_at: datetime
    result_count: int
    execution_time_ms: int

class SearchSuggestion(BaseModel):
    """Search suggestion model."""
    text: str
    type: str = Field(description="Type of suggestion (field, value, operator)")
    score: float = Field(ge=0, le=1)
    description: Optional[str] = None

class SearchSuggestionsRequest(BaseModel):
    """Search suggestions request model."""
    partial_query: str
    context: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, ge=1, le=50)

class SearchSuggestionsResponse(BaseResponse):
    """Search suggestions response model."""
    suggestions: List[SearchSuggestion]

class CorrelationRequest(BaseModel):
    """Correlation request model."""
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    service: Optional[str] = None
    time_range: TimeRange
    types: List[SearchType] = Field(default_factory=lambda: [SearchType.ALL])

class CorrelationResponse(BaseResponse):
    """Correlation response model."""
    related_items: List[SearchItem]
    correlation_graph: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=1)