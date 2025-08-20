"""Unit tests for Tempo client."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.services.tempo_client import TempoClient
from app.models.search import (
    SearchQuery, SearchType, TimeRange, SearchFilter, SearchOperator, TraceStatus
)
from app.exceptions import SearchException


@pytest.fixture
def tempo_client():
    """Create Tempo client for testing."""
    return TempoClient(base_url="http://test-tempo:3200", timeout=10)


@pytest.fixture
def sample_search_query():
    """Create sample search query."""
    return SearchQuery(
        free_text="service:api",
        type=SearchType.TRACES,
        time_range=TimeRange(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now()
        ),
        filters=[
            SearchFilter(
                field="status",
                operator=SearchOperator.EQUALS,
                value="error"
            )
        ],
        tenant_id="test-tenant",
        limit=50
    )


@pytest.fixture
def mock_tempo_search_response():
    """Create mock Tempo search response."""
    return {
        "traces": [
            {
                "traceID": "abc123def456",
                "rootServiceName": "api",
                "rootTraceName": "GET /users",
                "startTimeUnixNano": "1640995200000000000",
                "durationMs": 150
            },
            {
                "traceID": "def456ghi789",
                "rootServiceName": "database",
                "rootTraceName": "SELECT users",
                "startTimeUnixNano": "1640995260000000000",
                "durationMs": 75
            }
        ],
        "metrics": {
            "totalBlocks": 10,
            "completedJobs": 8
        }
    }


@pytest.fixture
def mock_trace_details():
    """Create mock trace details response."""
    return {
        "batches": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {"stringValue": "api"}
                        }
                    ]
                },
                "spans": [
                    {
                        "traceId": "abc123def456",
                        "spanId": "span123",
                        "name": "GET /users",
                        "startTimeUnixNano": "1640995200000000000",
                        "endTimeUnixNano": "1640995350000000000",
                        "status": {"code": 2},  # Error status
                        "attributes": [
                            {
                                "key": "http.method",
                                "value": {"stringValue": "GET"}
                            },
                            {
                                "key": "http.status_code",
                                "value": {"intValue": "500"}
                            }
                        ]
                    },
                    {
                        "traceId": "abc123def456",
                        "spanId": "span456",
                        "parentSpanId": "span123",
                        "name": "database query",
                        "startTimeUnixNano": "1640995220000000000",
                        "endTimeUnixNano": "1640995320000000000",
                        "status": {"code": 1},  # OK status
                        "attributes": [
                            {
                                "key": "db.statement",
                                "value": {"stringValue": "SELECT * FROM users"}
                            }
                        ]
                    }
                ]
            }
        ]
    }


class TestTempoClient:
    """Test cases for TempoClient."""
    
    @pytest.mark.asyncio
    async def test_search_traces_success(self, tempo_client, sample_search_query, mock_tempo_search_response):
        """Test successful trace search."""
        with patch.object(tempo_client, '_client') as mock_client:
            # Mock search response
            mock_response = Mock()
            mock_response.json.return_value = mock_tempo_search_response
            mock_response.raise_for_status.return_value = None
            mock_response.elapsed.total_seconds.return_value = 0.4
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Mock trace details (return None to test summary fallback)
            tempo_client._get_trace_details = AsyncMock(return_value=None)
            
            # Execute search
            items, stats = await tempo_client.search_traces(sample_search_query, "test-tenant")
            
            # Verify results
            assert len(items) == 2
            assert stats.matched == 2
            assert stats.latency_ms == 400
            assert stats.sources["tempo"] == 2
            
            # Verify first item
            first_item = items[0]  # Should be sorted by timestamp desc
            assert first_item.source == SearchType.TRACES
            assert first_item.service in ["api", "database"]
            assert first_item.tenant_id == "test-tenant"
            assert first_item.correlation_id in ["abc123def456", "def456ghi789"]
            assert first_item.content.trace_id in ["abc123def456", "def456ghi789"]
    
    @pytest.mark.asyncio
    async def test_search_traces_with_details(self, tempo_client, sample_search_query, mock_tempo_search_response, mock_trace_details):
        """Test trace search with detailed trace data."""
        with patch.object(tempo_client, '_client') as mock_client:
            # Mock search response
            mock_response = Mock()
            mock_response.json.return_value = mock_tempo_search_response
            mock_response.raise_for_status.return_value = None
            mock_response.elapsed.total_seconds.return_value = 0.4
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Mock trace details
            tempo_client._get_trace_details = AsyncMock(return_value=mock_trace_details)
            
            # Execute search
            items, stats = await tempo_client.search_traces(sample_search_query, "test-tenant")
            
            # Should have items from detailed spans
            assert len(items) > 0
            
            # Find the error span
            error_spans = [item for item in items if item.content.status == TraceStatus.ERROR]
            assert len(error_spans) > 0
            
            error_span = error_spans[0]
            assert error_span.content.operation_name == "GET /users"
            assert error_span.content.tags["http.method"] == "GET"
            assert error_span.content.tags["http.status_code"] == "500"
    
    @pytest.mark.asyncio
    async def test_search_traces_http_error(self, tempo_client, sample_search_query):
        """Test trace search with HTTP error."""
        with patch.object(tempo_client, '_client') as mock_client:
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            
            with pytest.raises(SearchException, match="Tempo request failed"):
                await tempo_client.search_traces(sample_search_query, "test-tenant")
    
    def test_build_search_params_basic(self, tempo_client):
        """Test basic search parameters building."""
        query = SearchQuery(
            free_text="service:api",
            type=SearchType.TRACES,
            time_range=TimeRange(
                start=datetime(2022, 1, 1, 10, 0, 0),
                end=datetime(2022, 1, 1, 11, 0, 0)
            ),
            filters=[],
            tenant_id="test-tenant",
            limit=100
        )
        
        params = tempo_client._build_search_params(query, "test-tenant")
        
        # The timestamps should match the datetime objects converted to Unix timestamps
        expected_start = int(datetime(2022, 1, 1, 10, 0, 0).timestamp())
        expected_end = int(datetime(2022, 1, 1, 11, 0, 0).timestamp())
        
        assert params["start"] == expected_start
        assert params["end"] == expected_end
        assert params["limit"] == 100
        assert params["tags"] == "tenant.id=test-tenant"
        assert params["service.name"] == "api"
    
    def test_build_search_params_with_filters(self, tempo_client):
        """Test search parameters building with filters."""
        query = SearchQuery(
            free_text="",
            type=SearchType.TRACES,
            time_range=TimeRange(
                start=datetime(2022, 1, 1, 10, 0, 0),
                end=datetime(2022, 1, 1, 11, 0, 0)
            ),
            filters=[
                SearchFilter(
                    field="service",
                    operator=SearchOperator.EQUALS,
                    value="api"
                ),
                SearchFilter(
                    field="http_method",
                    operator=SearchOperator.EQUALS,
                    value="GET"
                )
            ],
            tenant_id="test-tenant"
        )
        
        params = tempo_client._build_search_params(query, "test-tenant")
        
        assert "tenant.id=test-tenant service.name=api http.method=GET" in params["tags"]
    
    def test_build_filter_param(self, tempo_client):
        """Test filter parameter building."""
        # Test service filter
        service_filter = SearchFilter(
            field="service",
            operator=SearchOperator.EQUALS,
            value="api"
        )
        result = tempo_client._build_filter_param(service_filter)
        assert result == ("service.name", "api")
        
        # Test operation filter
        operation_filter = SearchFilter(
            field="operation",
            operator=SearchOperator.EQUALS,
            value="GET /users"
        )
        result = tempo_client._build_filter_param(operation_filter)
        assert result == ("name", "GET /users")
        
        # Test HTTP method filter
        http_filter = SearchFilter(
            field="http_method",
            operator=SearchOperator.EQUALS,
            value="POST"
        )
        result = tempo_client._build_filter_param(http_filter)
        assert result == ("http.method", "POST")
    
    def test_extract_service_name(self, tempo_client):
        """Test service name extraction from resource."""
        resource = {
            "attributes": [
                {
                    "key": "service.name",
                    "value": {"stringValue": "api-service"}
                },
                {
                    "key": "service.version",
                    "value": {"stringValue": "1.0.0"}
                }
            ]
        }
        
        service_name = tempo_client._extract_service_name(resource)
        assert service_name == "api-service"
        
        # Test with missing service name
        empty_resource = {"attributes": []}
        service_name = tempo_client._extract_service_name(empty_resource)
        assert service_name == "unknown"
    
    def test_create_span_item(self, tempo_client):
        """Test creating search item from span data."""
        span = {
            "traceId": "abc123def456",
            "spanId": "span123",
            "name": "GET /users",
            "startTimeUnixNano": "1640995200000000000",
            "endTimeUnixNano": "1640995350000000000",
            "status": {"code": 2},  # Error
            "attributes": [
                {
                    "key": "http.method",
                    "value": {"stringValue": "GET"}
                },
                {
                    "key": "http.status_code",
                    "value": {"intValue": "500"}
                },
                {
                    "key": "error",
                    "value": {"boolValue": True}
                }
            ]
        }
        
        item = tempo_client._create_span_item(span, "api", "test-tenant")
        
        assert item is not None
        assert item.source == SearchType.TRACES
        assert item.service == "api"
        assert item.tenant_id == "test-tenant"
        assert item.correlation_id == "abc123def456"
        
        # Check trace content
        trace_content = item.content
        assert trace_content.trace_id == "abc123def456"
        assert trace_content.span_id == "span123"
        assert trace_content.operation_name == "GET /users"
        assert trace_content.duration == 150000000  # microseconds (150ms in nanoseconds / 1000)
        assert trace_content.status == TraceStatus.ERROR
        assert trace_content.tags["http.method"] == "GET"
        assert trace_content.tags["http.status_code"] == "500"
        assert trace_content.tags["error"] == "True"
    
    def test_create_item_from_summary(self, tempo_client):
        """Test creating search item from trace summary."""
        trace_summary = {
            "traceID": "abc123def456",
            "rootServiceName": "api",
            "rootTraceName": "GET /users",
            "startTimeUnixNano": "1640995200000000000",
            "durationMs": 150
        }
        
        item = tempo_client._create_item_from_summary(trace_summary, "test-tenant")
        
        assert item is not None
        assert item.source == SearchType.TRACES
        assert item.service == "api"
        assert item.tenant_id == "test-tenant"
        assert item.correlation_id == "abc123def456"
        
        # Check trace content
        trace_content = item.content
        assert trace_content.trace_id == "abc123def456"
        assert trace_content.span_id == "root"
        assert trace_content.operation_name == "GET /users"
        assert trace_content.duration == 150000  # microseconds
        assert trace_content.status == TraceStatus.OK  # Default
    
    @pytest.mark.asyncio
    async def test_get_trace_details_success(self, tempo_client, mock_trace_details):
        """Test getting trace details by ID."""
        with patch.object(tempo_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_trace_details
            mock_response.raise_for_status.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            
            details = await tempo_client._get_trace_details("abc123def456")
            
            assert details == mock_trace_details
            mock_client.get.assert_called_once_with("http://test-tempo:3200/api/traces/abc123def456")
    
    @pytest.mark.asyncio
    async def test_get_trace_details_error(self, tempo_client):
        """Test getting trace details with error."""
        with patch.object(tempo_client, '_client') as mock_client:
            mock_client.get.side_effect = httpx.HTTPError("Not found")
            
            details = await tempo_client._get_trace_details("abc123def456")
            
            assert details is None
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, tempo_client):
        """Test successful health check."""
        with patch.object(tempo_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            
            is_healthy = await tempo_client.health_check()
            
            assert is_healthy is True
            mock_client.get.assert_called_once_with("http://test-tempo:3200/ready")
    
    @pytest.mark.asyncio
    async def test_get_trace_by_id(self, tempo_client, mock_trace_details):
        """Test getting trace by ID (public method)."""
        tempo_client._get_trace_details = AsyncMock(return_value=mock_trace_details)
        
        trace_data = await tempo_client.get_trace_by_id("abc123def456")
        
        assert trace_data == mock_trace_details
        tempo_client._get_trace_details.assert_called_once_with("abc123def456")