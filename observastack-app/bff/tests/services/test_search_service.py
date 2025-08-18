"""Unit tests for unified search service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from app.services.search_service import SearchService
from app.services.loki_client import LokiClient
from app.services.prometheus_client import PrometheusClient
from app.services.tempo_client import TempoClient
from app.models.search import (
    SearchQuery, SearchType, TimeRange, SearchItem, SearchStats,
    LogItem, MetricItem, TraceItem, LogLevel, MetricType, TraceStatus,
    CorrelationRequest, CorrelationResponse
)
from app.exceptions import SearchException


@pytest.fixture
def mock_loki_client():
    """Create mock Loki client."""
    return Mock(spec=LokiClient)


@pytest.fixture
def mock_prometheus_client():
    """Create mock Prometheus client."""
    return Mock(spec=PrometheusClient)


@pytest.fixture
def mock_tempo_client():
    """Create mock Tempo client."""
    return Mock(spec=TempoClient)


@pytest.fixture
def search_service(mock_loki_client, mock_prometheus_client, mock_tempo_client):
    """Create search service with mocked clients."""
    return SearchService(
        loki_client=mock_loki_client,
        prometheus_client=mock_prometheus_client,
        tempo_client=mock_tempo_client
    )


@pytest.fixture
def sample_search_query():
    """Create sample search query."""
    return SearchQuery(
        free_text="error",
        type=SearchType.ALL,
        time_range=TimeRange(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now()
        ),
        filters=[],
        tenant_id="test-tenant",
        limit=100
    )


@pytest.fixture
def sample_log_items():
    """Create sample log items."""
    return [
        SearchItem(
            id="log1",
            timestamp=datetime.now() - timedelta(minutes=5),
            source=SearchType.LOGS,
            service="api",
            content=LogItem(
                message="Database connection error",
                level=LogLevel.ERROR,
                labels={"service": "api"},
                fields={"trace_id": "abc123"}
            ),
            tenant_id="test-tenant"
        ),
        SearchItem(
            id="log2",
            timestamp=datetime.now() - timedelta(minutes=3),
            source=SearchType.LOGS,
            service="api",
            content=LogItem(
                message="Request completed successfully",
                level=LogLevel.INFO,
                labels={"service": "api"}
            ),
            tenant_id="test-tenant"
        )
    ]


@pytest.fixture
def sample_metric_items():
    """Create sample metric items."""
    return [
        SearchItem(
            id="metric1",
            timestamp=datetime.now() - timedelta(minutes=4),
            source=SearchType.METRICS,
            service="api",
            content=MetricItem(
                name="error_rate",
                value=0.05,
                unit="percent",
                labels={"service": "api"},
                type=MetricType.GAUGE
            ),
            tenant_id="test-tenant"
        )
    ]


@pytest.fixture
def sample_trace_items():
    """Create sample trace items."""
    return [
        SearchItem(
            id="trace1",
            timestamp=datetime.now() - timedelta(minutes=5),
            source=SearchType.TRACES,
            service="api",
            content=TraceItem(
                trace_id="abc123",
                span_id="span1",
                operation_name="GET /users",
                duration=150000,
                status=TraceStatus.ERROR,
                tags={"http.method": "GET", "http.status_code": "500"}
            ),
            correlation_id="abc123",
            tenant_id="test-tenant"
        )
    ]


class TestSearchService:
    """Test cases for SearchService."""
    
    @pytest.mark.asyncio
    async def test_search_all_sources_success(
        self, 
        search_service, 
        sample_search_query,
        sample_log_items,
        sample_metric_items,
        sample_trace_items,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test successful search across all sources."""
        # Mock client responses
        mock_loki_client.search_logs.return_value = (
            sample_log_items,
            SearchStats(matched=2, scanned=2, latency_ms=100, sources={"loki": 2})
        )
        mock_prometheus_client.search_metrics.return_value = (
            sample_metric_items,
            SearchStats(matched=1, scanned=1, latency_ms=150, sources={"prometheus": 1})
        )
        mock_tempo_client.search_traces.return_value = (
            sample_trace_items,
            SearchStats(matched=1, scanned=1, latency_ms=200, sources={"tempo": 1})
        )
        
        # Execute search
        result = await search_service.search(sample_search_query, "test-tenant")
        
        # Verify results
        assert len(result.items) == 4  # 2 logs + 1 metric + 1 trace
        assert result.stats.matched == 4
        assert result.stats.scanned == 4
        assert result.stats.latency_ms == 200  # Max latency
        assert result.stats.sources == {"loki": 2, "prometheus": 1, "tempo": 1}
        
        # Verify items are sorted by timestamp (desc)
        timestamps = [item.timestamp for item in result.items]
        assert timestamps == sorted(timestamps, reverse=True)
        
        # Verify correlation was applied
        correlated_items = [item for item in result.items if item.correlation_id]
        assert len(correlated_items) > 0
    
    @pytest.mark.asyncio
    async def test_search_logs_only(
        self,
        search_service,
        sample_log_items,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test search for logs only."""
        query = SearchQuery(
            free_text="error",
            type=SearchType.LOGS,
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            ),
            filters=[],
            tenant_id="test-tenant"
        )
        
        mock_loki_client.search_logs.return_value = (
            sample_log_items,
            SearchStats(matched=2, scanned=2, latency_ms=100, sources={"loki": 2})
        )
        
        result = await search_service.search(query, "test-tenant")
        
        # Only Loki should be called
        mock_loki_client.search_logs.assert_called_once()
        mock_prometheus_client.search_metrics.assert_not_called()
        mock_tempo_client.search_traces.assert_not_called()
        
        assert len(result.items) == 2
        assert all(item.source == SearchType.LOGS for item in result.items)
    
    @pytest.mark.asyncio
    async def test_search_with_client_error(
        self,
        search_service,
        sample_search_query,
        sample_log_items,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test search with one client failing."""
        # Mock successful responses
        mock_loki_client.search_logs.return_value = (
            sample_log_items,
            SearchStats(matched=2, scanned=2, latency_ms=100, sources={"loki": 2})
        )
        
        # Mock Prometheus failure
        mock_prometheus_client.search_metrics.side_effect = SearchException("Prometheus unavailable")
        
        # Mock successful Tempo
        mock_tempo_client.search_traces.return_value = (
            [],
            SearchStats(matched=0, scanned=0, latency_ms=50, sources={})
        )
        
        # Search should continue with available results
        result = await search_service.search(sample_search_query, "test-tenant")
        
        # Should have logs despite Prometheus failure
        assert len(result.items) == 2
        assert result.stats.sources == {"loki": 2}
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        search_service,
        sample_log_items,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test search with pagination."""
        query = SearchQuery(
            free_text="",
            type=SearchType.ALL,
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            ),
            filters=[],
            tenant_id="test-tenant",
            limit=1,
            offset=1
        )
        
        # Create more items than the limit
        all_items = sample_log_items * 3  # 6 items total
        
        mock_loki_client.search_logs.return_value = (
            all_items,
            SearchStats(matched=6, scanned=6, latency_ms=100, sources={"loki": 6})
        )
        mock_prometheus_client.search_metrics.return_value = ([], SearchStats(matched=0, scanned=0, latency_ms=0, sources={}))
        mock_tempo_client.search_traces.return_value = ([], SearchStats(matched=0, scanned=0, latency_ms=0, sources={}))
        
        result = await search_service.search(query, "test-tenant")
        
        # Should return only 1 item (limit) starting from offset 1
        assert len(result.items) == 1
        assert result.stats.matched == 1
        assert result.stats.scanned == 6  # Total items found
    
    @pytest.mark.asyncio
    async def test_apply_correlation(self, search_service, sample_log_items, sample_trace_items):
        """Test cross-signal correlation."""
        # Combine items from different sources
        all_items = sample_log_items + sample_trace_items
        
        # Apply correlation
        time_range = TimeRange(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now()
        )
        correlated_items = await search_service._apply_correlation(all_items, time_range)
        
        # Check that correlation was applied
        trace_item = next(item for item in correlated_items if item.source == SearchType.TRACES)
        log_with_trace = next(
            (item for item in correlated_items 
             if item.source == SearchType.LOGS and "abc123" in item.content.message),
            None
        )
        
        if log_with_trace:
            assert log_with_trace.correlation_id == trace_item.content.trace_id
    
    @pytest.mark.asyncio
    async def test_correlate_signals_by_trace_id(self, search_service, sample_trace_items):
        """Test signal correlation by trace ID."""
        request = CorrelationRequest(
            trace_id="abc123",
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            )
        )
        
        # Mock finding items by trace ID
        search_service._find_items_by_trace_id = AsyncMock(return_value=sample_trace_items)
        
        response = await search_service.correlate_signals(request, "test-tenant")
        
        assert isinstance(response, CorrelationResponse)
        assert len(response.related_items) == 1
        assert response.confidence_score > 0
        assert "nodes" in response.correlation_graph
        assert "edges" in response.correlation_graph
    
    @pytest.mark.asyncio
    async def test_correlate_signals_by_service(self, search_service, sample_trace_items):
        """Test signal correlation by service."""
        request = CorrelationRequest(
            service="api",
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            )
        )
        
        # Mock search method
        mock_result = Mock()
        mock_result.items = sample_trace_items
        search_service.search = AsyncMock(return_value=mock_result)
        
        response = await search_service.correlate_signals(request, "test-tenant")
        
        assert isinstance(response, CorrelationResponse)
        assert len(response.related_items) == 1
        search_service.search.assert_called_once()
    
    def test_build_correlation_graph(self, search_service, sample_log_items, sample_trace_items):
        """Test correlation graph building."""
        # Set correlation IDs
        sample_log_items[0].correlation_id = "abc123"
        sample_trace_items[0].correlation_id = "abc123"
        
        all_items = sample_log_items + sample_trace_items
        graph = search_service._build_correlation_graph(all_items)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert "clusters" in graph
        
        # Should have nodes for all items
        assert len(graph["nodes"]) == len(all_items)
        
        # Should have edges between correlated items
        correlated_items = [item for item in all_items if item.correlation_id == "abc123"]
        if len(correlated_items) > 1:
            assert len(graph["edges"]) > 0
    
    def test_calculate_correlation_confidence(self, search_service, sample_log_items, sample_trace_items):
        """Test correlation confidence calculation."""
        # Test with no items
        confidence = search_service._calculate_correlation_confidence([])
        assert confidence == 0.0
        
        # Test with mixed signal types and correlation IDs
        sample_log_items[0].correlation_id = "abc123"
        sample_trace_items[0].correlation_id = "abc123"
        
        all_items = sample_log_items + sample_trace_items
        confidence = search_service._calculate_correlation_confidence(all_items)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0  # Should have some confidence with correlated items
    
    @pytest.mark.asyncio
    async def test_find_items_by_trace_id(
        self,
        search_service,
        sample_trace_items,
        sample_log_items,
        mock_tempo_client,
        mock_loki_client,
        mock_prometheus_client
    ):
        """Test finding items by trace ID."""
        # Mock client responses
        mock_tempo_client.search_traces.return_value = (sample_trace_items, Mock())
        mock_loki_client.search_logs.return_value = (sample_log_items, Mock())
        mock_prometheus_client.search_metrics.return_value = ([], Mock())
        
        query = SearchQuery(
            free_text="",
            type=SearchType.ALL,
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            ),
            filters=[],
            tenant_id="test-tenant"
        )
        
        items = await search_service._find_items_by_trace_id("abc123", query, "test-tenant")
        
        # Should find the trace and related items
        assert len(items) > 0
        trace_items = [item for item in items if item.source == SearchType.TRACES]
        assert len(trace_items) > 0
    
    @pytest.mark.asyncio
    async def test_health_check(
        self,
        search_service,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test health check for all clients."""
        # Mock health check responses
        mock_loki_client.health_check.return_value = True
        mock_prometheus_client.health_check.return_value = False
        mock_tempo_client.health_check.return_value = True
        
        health_status = await search_service.health_check()
        
        assert health_status["loki"] is True
        assert health_status["prometheus"] is False
        assert health_status["tempo"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_with_exceptions(
        self,
        search_service,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test health check with client exceptions."""
        # Mock health check with exception
        mock_loki_client.health_check.side_effect = Exception("Connection failed")
        mock_prometheus_client.health_check.return_value = True
        mock_tempo_client.health_check.return_value = True
        
        health_status = await search_service.health_check()
        
        assert health_status["loki"] is False  # Exception should result in False
        assert health_status["prometheus"] is True
        assert health_status["tempo"] is True
    
    @pytest.mark.asyncio
    async def test_close(
        self,
        search_service,
        mock_loki_client,
        mock_prometheus_client,
        mock_tempo_client
    ):
        """Test closing all client connections."""
        # Mock close methods
        mock_loki_client.close = AsyncMock()
        mock_prometheus_client.close = AsyncMock()
        mock_tempo_client.close = AsyncMock()
        
        await search_service.close()
        
        # All clients should be closed
        mock_loki_client.close.assert_called_once()
        mock_prometheus_client.close.assert_called_once()
        mock_tempo_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service, sample_search_query):
        """Test search with general error."""
        # Mock all clients to raise exceptions
        search_service.loki_client = Mock()
        search_service.prometheus_client = Mock()
        search_service.tempo_client = Mock()
        
        search_service.loki_client.search_logs.side_effect = Exception("General error")
        search_service.prometheus_client.search_metrics.side_effect = Exception("General error")
        search_service.tempo_client.search_traces.side_effect = Exception("General error")
        
        # Should still return results (empty) rather than raising
        result = await search_service.search(sample_search_query, "test-tenant")
        
        assert len(result.items) == 0
        assert result.stats.matched == 0