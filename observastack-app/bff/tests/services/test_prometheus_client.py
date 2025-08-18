"""Unit tests for Prometheus client."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.services.prometheus_client import PrometheusClient
from app.models.search import (
    SearchQuery, SearchType, TimeRange, SearchFilter, SearchOperator, MetricType
)
from app.exceptions import SearchException


@pytest.fixture
def prometheus_client():
    """Create Prometheus client for testing."""
    return PrometheusClient(base_url="http://test-prometheus:9090", timeout=10)


@pytest.fixture
def sample_search_query():
    """Create sample search query."""
    return SearchQuery(
        free_text="cpu_usage",
        type=SearchType.METRICS,
        time_range=TimeRange(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now()
        ),
        filters=[
            SearchFilter(
                field="service",
                operator=SearchOperator.EQUALS,
                value="api"
            )
        ],
        tenant_id="test-tenant",
        limit=100
    )


@pytest.fixture
def mock_prometheus_response():
    """Create mock Prometheus response."""
    return {
        "status": "success",
        "data": {
            "result": [
                {
                    "metric": {
                        "__name__": "cpu_usage_percent",
                        "service": "api",
                        "instance": "api-1",
                        "tenant_id": "test-tenant"
                    },
                    "values": [
                        ["1640995200", "85.5"],
                        ["1640995260", "92.3"]
                    ]
                },
                {
                    "metric": {
                        "__name__": "memory_usage_bytes",
                        "service": "api",
                        "instance": "api-1",
                        "tenant_id": "test-tenant"
                    },
                    "values": [
                        ["1640995200", "1073741824"],
                        ["1640995260", "1207959552"]
                    ]
                }
            ]
        }
    }


class TestPrometheusClient:
    """Test cases for PrometheusClient."""
    
    @pytest.mark.asyncio
    async def test_search_metrics_success(self, prometheus_client, sample_search_query, mock_prometheus_response):
        """Test successful metrics search."""
        with patch.object(prometheus_client, '_client') as mock_client:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_prometheus_response
            mock_response.raise_for_status.return_value = None
            mock_response.elapsed.total_seconds.return_value = 0.3
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Execute search
            items, stats = await prometheus_client.search_metrics(sample_search_query, "test-tenant")
            
            # Verify results
            assert len(items) == 4  # 2 metrics × 2 time points each
            assert stats.matched == 4
            assert stats.latency_ms == 300
            assert stats.sources["prometheus"] == 4
            
            # Verify first item
            first_item = items[0]  # Should be sorted by timestamp desc
            assert first_item.source == SearchType.METRICS
            assert first_item.service == "api"
            assert first_item.tenant_id == "test-tenant"
            assert first_item.content.name in ["cpu_usage_percent", "memory_usage_bytes"]
            assert first_item.content.type in [MetricType.GAUGE, MetricType.COUNTER]
    
    @pytest.mark.asyncio
    async def test_search_metrics_http_error(self, prometheus_client, sample_search_query):
        """Test metrics search with HTTP error."""
        with patch.object(prometheus_client, '_client') as mock_client:
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            
            with pytest.raises(SearchException, match="Prometheus request failed"):
                await prometheus_client.search_metrics(sample_search_query, "test-tenant")
    
    @pytest.mark.asyncio
    async def test_search_metrics_prometheus_error(self, prometheus_client, sample_search_query):
        """Test metrics search with Prometheus error response."""
        with patch.object(prometheus_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "status": "error",
                "data": {},
                "error": "Invalid PromQL query"
            }
            mock_response.raise_for_status.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(SearchException, match="Prometheus query failed"):
                await prometheus_client.search_metrics(sample_search_query, "test-tenant")
    
    def test_build_promql_query_basic(self, prometheus_client):
        """Test basic PromQL query building."""
        query = SearchQuery(
            free_text="cpu_usage",
            type=SearchType.METRICS,
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            ),
            filters=[],
            tenant_id="test-tenant"
        )
        
        promql = prometheus_client._build_promql_query(query, "test-tenant")
        
        assert 'tenant_id="test-tenant"' in promql
        assert '__name__=~".*cpu_usage.*"' in promql
    
    def test_build_promql_query_with_filters(self, prometheus_client):
        """Test PromQL query building with filters."""
        query = SearchQuery(
            free_text="",
            type=SearchType.METRICS,
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            ),
            filters=[
                SearchFilter(
                    field="service",
                    operator=SearchOperator.EQUALS,
                    value="api"
                ),
                SearchFilter(
                    field="instance",
                    operator=SearchOperator.REGEX,
                    value="api-.*"
                )
            ],
            tenant_id="test-tenant"
        )
        
        promql = prometheus_client._build_promql_query(query, "test-tenant")
        
        assert 'tenant_id="test-tenant"' in promql
        assert 'service="api"' in promql
        assert 'instance=~"api-.*"' in promql
    
    def test_build_filter_clause(self, prometheus_client):
        """Test filter clause building."""
        # Test equals filter
        equals_filter = SearchFilter(
            field="service",
            operator=SearchOperator.EQUALS,
            value="api"
        )
        clause = prometheus_client._build_filter_clause(equals_filter)
        assert clause == 'service="api"'
        
        # Test not equals filter
        not_equals_filter = SearchFilter(
            field="instance",
            operator=SearchOperator.NOT_EQUALS,
            value="test"
        )
        clause = prometheus_client._build_filter_clause(not_equals_filter)
        assert clause == 'instance!="test"'
        
        # Test regex filter
        regex_filter = SearchFilter(
            field="job",
            operator=SearchOperator.REGEX,
            value="api-.*"
        )
        clause = prometheus_client._build_filter_clause(regex_filter)
        assert clause == 'job=~"api-.*"'
    
    def test_calculate_step(self, prometheus_client):
        """Test step calculation for different time ranges."""
        now = datetime.now()
        
        # 30 minutes - should use 30s step
        start = now - timedelta(minutes=30)
        step = prometheus_client._calculate_step(start, now)
        assert step == "30s"
        
        # 6 hours - should use 5m step
        start = now - timedelta(hours=6)
        step = prometheus_client._calculate_step(start, now)
        assert step == "5m"
        
        # 3 days - should use 1h step
        start = now - timedelta(days=3)
        step = prometheus_client._calculate_step(start, now)
        assert step == "1h"
        
        # 2 weeks - should use 6h step
        start = now - timedelta(weeks=2)
        step = prometheus_client._calculate_step(start, now)
        assert step == "6h"
    
    def test_parse_prometheus_response(self, prometheus_client, mock_prometheus_response):
        """Test parsing Prometheus response data."""
        items = prometheus_client._parse_prometheus_response(
            mock_prometheus_response["data"], 
            "test-tenant"
        )
        
        assert len(items) == 4  # 2 metrics × 2 values each
        
        # Items should be sorted by timestamp descending
        timestamps = [item.timestamp for item in items]
        assert timestamps == sorted(timestamps, reverse=True)
        
        # Check metric types and units
        cpu_items = [item for item in items if item.content.name == "cpu_usage_percent"]
        memory_items = [item for item in items if item.content.name == "memory_usage_bytes"]
        
        assert len(cpu_items) == 2
        assert len(memory_items) == 2
        
        # Check CPU metric
        cpu_item = cpu_items[0]
        assert cpu_item.content.type == MetricType.GAUGE
        assert cpu_item.content.unit == "percent"
        assert cpu_item.service == "api"
        
        # Check memory metric
        memory_item = memory_items[0]
        assert memory_item.content.type == MetricType.GAUGE
        assert memory_item.content.unit == "bytes"
    
    def test_infer_metric_type(self, prometheus_client):
        """Test metric type inference."""
        # Counter metrics
        assert prometheus_client._infer_metric_type("requests_total") == MetricType.COUNTER
        assert prometheus_client._infer_metric_type("http_requests_count") == MetricType.COUNTER
        
        # Histogram metrics
        assert prometheus_client._infer_metric_type("request_duration_bucket") == MetricType.HISTOGRAM
        assert prometheus_client._infer_metric_type("response_size_sum") == MetricType.HISTOGRAM
        
        # Summary metrics
        assert prometheus_client._infer_metric_type("request_duration_quantile") == MetricType.SUMMARY
        
        # Gauge metrics (default)
        assert prometheus_client._infer_metric_type("cpu_usage") == MetricType.GAUGE
        assert prometheus_client._infer_metric_type("memory_usage") == MetricType.GAUGE
    
    def test_infer_unit(self, prometheus_client):
        """Test unit inference."""
        # Time units
        assert prometheus_client._infer_unit("request_duration_seconds") == "seconds"
        assert prometheus_client._infer_unit("processing_time") == "seconds"
        
        # Byte units
        assert prometheus_client._infer_unit("memory_usage_bytes") == "bytes"
        assert prometheus_client._infer_unit("response_size") == "bytes"
        
        # Percentage units
        assert prometheus_client._infer_unit("cpu_usage_percent") == "percent"
        assert prometheus_client._infer_unit("error_rate") == "percent"
        
        # Request units
        assert prometheus_client._infer_unit("http_requests_total") == "requests"
        
        # Unknown units
        assert prometheus_client._infer_unit("custom_metric") == ""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, prometheus_client):
        """Test successful health check."""
        with patch.object(prometheus_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            
            is_healthy = await prometheus_client.health_check()
            
            assert is_healthy is True
            mock_client.get.assert_called_once_with("http://test-prometheus:9090/-/healthy")
    
    @pytest.mark.asyncio
    async def test_get_metric_names_success(self, prometheus_client):
        """Test getting metric names."""
        with patch.object(prometheus_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "status": "success",
                "data": ["cpu_usage", "memory_usage", "http_requests_total"]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            
            metric_names = await prometheus_client.get_metric_names("test-tenant")
            
            assert metric_names == ["cpu_usage", "memory_usage", "http_requests_total"]
    
    @pytest.mark.asyncio
    async def test_get_metric_names_error(self, prometheus_client):
        """Test getting metric names with error."""
        with patch.object(prometheus_client, '_client') as mock_client:
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            
            metric_names = await prometheus_client.get_metric_names("test-tenant")
            
            assert metric_names == []