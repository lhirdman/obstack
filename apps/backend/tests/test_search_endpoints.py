"""Integration tests for search API endpoints."""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.models.search import (
    SearchQuery, SearchType, TimeRange, SearchItem, SearchStats,
    LogItem, LogLevel, MetricItem, MetricType, TraceItem, TraceStatus,
    StreamingSearchChunk
)


@pytest.fixture
def sample_search_query():
    """Create sample search query."""
    now = datetime.utcnow()
    return {
        "free_text": "error",
        "type": "all",
        "time_range": {
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": now.isoformat()
        },
        "tenant_id": "test-tenant-456",
        "limit": 50,
        "offset": 0,
        "sort_by": "timestamp",
        "sort_order": "desc",
        "filters": []
    }


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


class TestSearchEndpoints:
    """Test class for search API endpoints."""
    
    def test_search_endpoint_success(
        self, 
        client, 
        mock_search_service,
        mock_auth_dependencies,
        sample_search_query, 
        sample_search_items
    ):
        """Test successful search endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        # Setup search service mock
        mock_search_result = MagicMock()
        mock_search_result.items = sample_search_items
        mock_search_result.stats = SearchStats(
            matched=3,
            scanned=100,
            latency_ms=250,
            sources={"loki": 1, "prometheus": 1, "tempo": 1}
        )
        mock_search_result.facets = []
        mock_search_result.next_token = None
        
        mock_search_service.search.return_value = mock_search_result
        
        # Make request
        response = client.post(
            "/api/search",
            json=sample_search_query
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 3
        assert data["stats"]["matched"] == 3
        assert data["stats"]["latency_ms"] == 250
        
        # Verify search service was called correctly
        mock_search_service.search.assert_called_once()
        call_args = mock_search_service.search.call_args
        assert call_args[0][1] == "test-tenant-456"  # tenant_id
    
    def test_search_endpoint_error(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies,
        sample_search_query
    ):
        """Test search endpoint error handling."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        from app.exceptions import SearchException
        mock_search_service.search.side_effect = SearchException("Search service unavailable")
        
        # Make request
        response = client.post(
            "/api/search",
            json=sample_search_query
        )
        
        # Assertions
        assert response.status_code == 500
        assert "Search failed" in response.json()["detail"]
    
    def test_search_stream_endpoint(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies,
        sample_search_query,
        sample_search_items
    ):
        """Test streaming search endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        # Create mock streaming chunks
        async def mock_search_stream(query, tenant_id):
            # Yield chunks of results
            yield StreamingSearchChunk(
                chunk_id=0,
                items=sample_search_items[:2],
                is_final=False
            )
            yield StreamingSearchChunk(
                chunk_id=1,
                items=sample_search_items[2:],
                is_final=False
            )
            yield StreamingSearchChunk(
                chunk_id=2,
                items=[],
                is_final=True,
                stats=SearchStats(
                    matched=3,
                    scanned=100,
                    latency_ms=250,
                    sources={"loki": 1, "prometheus": 1, "tempo": 1}
                )
            )
        
        mock_search_service.search_stream = mock_search_stream
        
        # Make request
        response = client.post(
            "/api/search/stream",
            json=sample_search_query
        )
        
        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse SSE response
        content = response.content.decode()
        lines = content.strip().split('\n')
        
        # Should contain search_started, search_chunk, and search_completed events
        events = []
        for line in lines:
            if line.startswith('event:'):
                events.append(line.split(':', 1)[1].strip())
        
        assert "search_started" in events
        assert "search_chunk" in events
        assert "search_completed" in events
    
    def test_search_health_endpoint(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies
    ):
        """Test search health endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        mock_search_service.health_check.return_value = {
            "loki": True,
            "prometheus": True,
            "tempo": False
        }
        
        # Make request
        response = client.get("/api/search/health")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"  # At least one source is healthy
        assert data["sources"]["loki"] is True
        assert data["sources"]["prometheus"] is True
        assert data["sources"]["tempo"] is False
        assert "timestamp" in data
    
    def test_search_stats_endpoint(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies
    ):
        """Test search statistics endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        mock_stats = {
            "tenant_id": "test-tenant-456",
            "total_searches": 1250,
            "avg_response_time_ms": 245,
            "success_rate": 0.987,
            "data_sources": {
                "loki": {"total_queries": 450, "avg_response_time_ms": 180},
                "prometheus": {"total_queries": 520, "avg_response_time_ms": 120},
                "tempo": {"total_queries": 280, "avg_response_time_ms": 450}
            }
        }
        
        mock_search_service.get_search_statistics.return_value = mock_stats
        
        # Make request
        response = client.get("/api/search/stats")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["tenant_id"] == "test-tenant-456"
        assert data["total_searches"] == 1250
        assert data["avg_response_time_ms"] == 245
        assert "data_sources" in data
    
    def test_search_metrics_endpoint(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies
    ):
        """Test search metrics endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        mock_metrics = {
            "tenant_id": "test-tenant-456",
            "timestamp": datetime.utcnow().isoformat(),
            "availability_score": 0.67,
            "healthy_sources": 2,
            "total_sources": 3,
            "performance_indicators": {
                "query_throughput": 15.2,
                "avg_latency_ms": 245,
                "error_rate": 0.013
            }
        }
        
        mock_search_service.get_performance_metrics.return_value = mock_metrics
        
        # Make request
        response = client.get("/api/search/metrics")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["tenant_id"] == "test-tenant-456"
        assert data["availability_score"] == 0.67
        assert data["healthy_sources"] == 2
        assert "performance_indicators" in data
    
    def test_search_aggregate_endpoint(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies,
        sample_search_query
    ):
        """Test search aggregation endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        mock_aggregation = {
            "aggregation_type": "service",
            "total_items": 3,
            "aggregated_data": {
                "service_counts": {"web-service": 3},
                "service_items": {"web-service": ["log-1", "metric-1", "trace-1"]},
                "service_sources": {"web-service": ["logs", "metrics", "traces"]}
            },
            "stats": {
                "matched": 3,
                "scanned": 100,
                "latency_ms": 250
            }
        }
        
        mock_search_service.search_aggregate.return_value = mock_aggregation
        
        # Make request
        response = client.post(
            "/api/search/aggregate?aggregation_type=service",
            json=sample_search_query
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["aggregation_type"] == "service"
        assert data["total_items"] == 3
        assert "aggregated_data" in data
        assert "service_counts" in data["aggregated_data"]
    
    def test_correlate_signals_endpoint(
        self, 
        client,
        mock_search_service,
        mock_auth_dependencies,
        sample_search_items
    ):
        """Test signal correlation endpoint."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        from app.models.search import CorrelationRequest, CorrelationResponse
        
        correlation_request = CorrelationRequest(
            trace_id="trace-abc-123",
            time_range=TimeRange(
                start=datetime.utcnow() - timedelta(hours=1),
                end=datetime.utcnow()
            )
        )
        
        mock_correlation = CorrelationResponse(
            related_items=sample_search_items,
            correlation_graph={
                "nodes": [{"id": "log-1", "type": "logs"}],
                "edges": [{"source": "log-1", "target": "trace-1"}]
            },
            confidence_score=0.85
        )
        
        mock_search_service.correlate_signals.return_value = mock_correlation
        
        correlation_request_dict = {
            "trace_id": "trace-abc-123",
            "time_range": {
                "start": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        }
        
        # Make request
        response = client.post(
            "/api/search/correlate",
            json=correlation_request_dict
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["related_items"]) == 3
        assert data["confidence_score"] == 0.85
        assert "correlation_graph" in data


class TestSearchEndpointsAsync:
    """Async test class for search endpoints."""
    
    @pytest.mark.asyncio
    async def test_search_stream_async(
        self, 
        test_app,
        mock_search_service,
        mock_auth_dependencies,
        sample_search_query, 
        sample_search_items
    ):
        """Test streaming search with async client."""
        mock_user, mock_get_user, mock_get_tenant = mock_auth_dependencies
        
        # Create mock streaming chunks
        async def mock_search_stream(query, tenant_id):
            yield StreamingSearchChunk(
                chunk_id=0,
                items=sample_search_items,
                is_final=False
            )
            yield StreamingSearchChunk(
                chunk_id=1,
                items=[],
                is_final=True,
                stats=SearchStats(matched=3, scanned=100, latency_ms=250, sources={})
            )
        
        mock_search_service.search_stream = mock_search_stream
        
        # Make async request
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/search/stream",
                json=sample_search_query
            )
            
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # Verify streaming content
            content = response.content.decode()
            assert "event: search_started" in content
            assert "event: search_chunk" in content
            assert "event: search_completed" in content


if __name__ == "__main__":
    pytest.main([__file__])