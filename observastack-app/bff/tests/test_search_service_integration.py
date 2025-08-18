"""Integration tests for search service functionality."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.search_service import SearchService
from app.models.search import (
    SearchQuery, SearchType, TimeRange, SearchItem, SearchStats,
    LogItem, LogLevel, MetricItem, MetricType, TraceItem, TraceStatus,
    StreamingSearchChunk
)


@pytest.fixture
def mock_clients():
    """Create mock data source clients."""
    loki_client = MagicMock()
    prometheus_client = MagicMock()
    tempo_client = MagicMock()
    
    # Setup async methods
    loki_client.search_logs = AsyncMock()
    loki_client.search_logs_stream = AsyncMock()
    loki_client.health_check = AsyncMock()
    loki_client.close = AsyncMock()
    
    prometheus_client.search_metrics = AsyncMock()
    prometheus_client.search_metrics_stream = AsyncMock()
    prometheus_client.health_check = AsyncMock()
    prometheus_client.close = AsyncMock()
    
    tempo_client.search_traces = AsyncMock()
    tempo_client.search_traces_stream = AsyncMock()
    tempo_client.health_check = AsyncMock()
    tempo_client.close = AsyncMock()
    
    return loki_client, prometheus_client, tempo_client


@pytest.fixture
def search_service(mock_clients):
    """Create search service with mocked clients."""
    loki_client, prometheus_client, tempo_client = mock_clients
    return SearchService(
        loki_client=loki_client,
        prometheus_client=prometheus_client,
        tempo_client=tempo_client
    )


@pytest.fixture
def sample_search_query():
    """Create sample search query."""
    return SearchQuery(
        free_text="error",
        type=SearchType.ALL,
        time_range=TimeRange(
            start=datetime.utcnow() - timedelta(hours=1),
            end=datetime.utcnow()
        ),
        tenant_id="test-tenant-456",
        limit=50
    )


@pytest.fixture
def sample_search_items():
    """Create sample search items."""
    now = datetime.utcnow()
    
    return [
        SearchItem(
            id="log-1",
            timestamp=now - timedelta(minutes=5),
            source=SearchType.LOGS,
            service="web-service",
            content=LogItem(
                message="Error processing request",
                level=LogLevel.ERROR,
                labels={"service": "web-service"},
                fields={"request_id": "req-123"}
            ),
            tenant_id="test-tenant-456"
        ),
        SearchItem(
            id="metric-1",
            timestamp=now - timedelta(minutes=3),
            source=SearchType.METRICS,
            service="web-service",
            content=MetricItem(
                name="http_requests_total",
                value=1250.0,
                unit="requests",
                labels={"service": "web-service", "status": "500"},
                type=MetricType.COUNTER
            ),
            tenant_id="test-tenant-456"
        ),
        SearchItem(
            id="trace-1",
            timestamp=now - timedelta(minutes=2),
            source=SearchType.TRACES,
            service="web-service",
            content=TraceItem(
                trace_id="trace-abc-123",
                span_id="span-def-456",
                operation_name="handle_request",
                duration=150000,  # 150ms in microseconds
                status=TraceStatus.ERROR,
                tags={"service": "web-service", "error": "true"}
            ),
            correlation_id="trace-abc-123",
            tenant_id="test-tenant-456"
        )
    ]


class TestSearchServiceIntegration:
    """Integration tests for SearchService."""
    
    @pytest.mark.asyncio
    async def test_unified_search_success(
        self, 
        search_service, 
        mock_clients, 
        sample_search_query, 
        sample_search_items
    ):
        """Test successful unified search across all data sources."""
        loki_client, prometheus_client, tempo_client = mock_clients
        
        # Setup mock responses
        loki_client.search_logs.return_value = (
            [sample_search_items[0]], 
            SearchStats(matched=1, scanned=10, latency_ms=100, sources={"loki": 1})
        )
        prometheus_client.search_metrics.return_value = (
            [sample_search_items[1]], 
            SearchStats(matched=1, scanned=20, latency_ms=80, sources={"prometheus": 1})
        )
        tempo_client.search_traces.return_value = (
            [sample_search_items[2]], 
            SearchStats(matched=1, scanned=5, latency_ms=200, sources={"tempo": 1})
        )
        
        # Execute search
        result = await search_service.search(sample_search_query, "test-tenant-456")
        
        # Assertions
        assert len(result.items) == 3
        assert result.stats.matched == 3  # Final count after pagination
        assert result.stats.scanned >= 3  # Should be at least the number of items returned
        assert result.stats.latency_ms == 200  # max of all latencies
        assert "loki" in result.stats.sources
        assert "prometheus" in result.stats.sources
        assert "tempo" in result.stats.sources
        
        # Verify all clients were called
        loki_client.search_logs.assert_called_once()
        prometheus_client.search_metrics.assert_called_once()
        tempo_client.search_traces.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_streaming_search(
        self, 
        search_service, 
        mock_clients, 
        sample_search_query, 
        sample_search_items
    ):
        """Test streaming search functionality."""
        loki_client, prometheus_client, tempo_client = mock_clients
        
        # Setup streaming mock responses
        async def mock_loki_stream(query, tenant_id):
            yield [sample_search_items[0]], SearchStats(matched=1, scanned=5, latency_ms=50, sources={"loki": 1})
        
        async def mock_prometheus_stream(query, tenant_id):
            yield [sample_search_items[1]], SearchStats(matched=1, scanned=10, latency_ms=60, sources={"prometheus": 1})
        
        async def mock_tempo_stream(query, tenant_id):
            yield [sample_search_items[2]], SearchStats(matched=1, scanned=3, latency_ms=100, sources={"tempo": 1})
        
        loki_client.search_logs_stream.side_effect = mock_loki_stream
        prometheus_client.search_metrics_stream.side_effect = mock_prometheus_stream
        tempo_client.search_traces_stream.side_effect = mock_tempo_stream
        
        # Execute streaming search
        chunks = []
        async for chunk in search_service.search_stream(sample_search_query, "test-tenant-456"):
            chunks.append(chunk)
        
        # Assertions
        assert len(chunks) >= 1  # At least one chunk should be received
        
        # Check that we got some data chunks and a final chunk
        data_chunks = [c for c in chunks if not c.is_final]
        final_chunks = [c for c in chunks if c.is_final]
        
        assert len(data_chunks) >= 1  # Should have at least one data chunk
        assert len(final_chunks) == 1  # Should have exactly one final chunk
        
        # Verify final chunk has stats
        final_chunk = final_chunks[0]
        assert final_chunk.stats is not None
        assert final_chunk.stats.matched >= 0
    
    @pytest.mark.asyncio
    async def test_search_statistics(self, search_service):
        """Test search statistics functionality."""
        stats = await search_service.get_search_statistics("test-tenant-456")
        
        # Assertions
        assert stats["tenant_id"] == "test-tenant-456"
        assert "total_searches" in stats
        assert "avg_response_time_ms" in stats
        assert "success_rate" in stats
        assert "data_sources" in stats
        
        # Check data sources stats
        assert "loki" in stats["data_sources"]
        assert "prometheus" in stats["data_sources"]
        assert "tempo" in stats["data_sources"]
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, search_service, mock_clients):
        """Test performance metrics functionality."""
        loki_client, prometheus_client, tempo_client = mock_clients
        
        # Setup health check responses
        loki_client.health_check.return_value = True
        prometheus_client.health_check.return_value = True
        tempo_client.health_check.return_value = False
        
        metrics = await search_service.get_performance_metrics("test-tenant-456")
        
        # Assertions
        assert metrics["tenant_id"] == "test-tenant-456"
        assert metrics["availability_score"] == 2/3  # 2 out of 3 sources healthy
        assert metrics["healthy_sources"] == 2
        assert metrics["total_sources"] == 3
        assert "performance_indicators" in metrics
        assert "resource_usage" in metrics
    
    @pytest.mark.asyncio
    async def test_search_aggregation(
        self, 
        search_service, 
        mock_clients, 
        sample_search_query, 
        sample_search_items
    ):
        """Test search aggregation functionality."""
        loki_client, prometheus_client, tempo_client = mock_clients
        
        # Setup mock responses for regular search (used by aggregation)
        loki_client.search_logs.return_value = (
            [sample_search_items[0]], 
            SearchStats(matched=1, scanned=10, latency_ms=100, sources={"loki": 1})
        )
        prometheus_client.search_metrics.return_value = (
            [sample_search_items[1]], 
            SearchStats(matched=1, scanned=20, latency_ms=80, sources={"prometheus": 1})
        )
        tempo_client.search_traces.return_value = (
            [sample_search_items[2]], 
            SearchStats(matched=1, scanned=5, latency_ms=200, sources={"tempo": 1})
        )
        
        # Test service aggregation
        result = await search_service.search_aggregate(
            sample_search_query, 
            "service", 
            "test-tenant-456"
        )
        
        # Assertions
        assert result["aggregation_type"] == "service"
        assert result["total_items"] == 3
        assert "aggregated_data" in result
        assert "service_counts" in result["aggregated_data"]
        assert "web-service" in result["aggregated_data"]["service_counts"]
        assert result["aggregated_data"]["service_counts"]["web-service"] == 3
    
    @pytest.mark.asyncio
    async def test_health_check(self, search_service, mock_clients):
        """Test health check functionality."""
        loki_client, prometheus_client, tempo_client = mock_clients
        
        # Setup health check responses
        loki_client.health_check.return_value = True
        prometheus_client.health_check.return_value = False
        tempo_client.health_check.return_value = True
        
        health_status = await search_service.health_check()
        
        # Assertions
        assert health_status["loki"] is True
        assert health_status["prometheus"] is False
        assert health_status["tempo"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling(
        self, 
        search_service, 
        mock_clients, 
        sample_search_query
    ):
        """Test error handling in search operations."""
        loki_client, prometheus_client, tempo_client = mock_clients
        
        # Setup one client to fail
        loki_client.search_logs.side_effect = Exception("Loki connection failed")
        prometheus_client.search_metrics.return_value = ([], SearchStats(matched=0, scanned=0, latency_ms=0, sources={}))
        tempo_client.search_traces.return_value = ([], SearchStats(matched=0, scanned=0, latency_ms=0, sources={}))
        
        # Search should still work with partial failures
        result = await search_service.search(sample_search_query, "test-tenant-456")
        
        # Should get results from working clients
        assert result is not None
        assert result.stats.matched >= 0  # Should not crash


if __name__ == "__main__":
    pytest.main([__file__])