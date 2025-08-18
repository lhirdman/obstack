"""Comprehensive tests for search service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.search_service import SearchService
from app.models.search import SearchQuery, SearchFilter, TimeRange
from app.exceptions import SearchError, TenantIsolationError


class TestSearchServiceComprehensive:
    """Comprehensive test cases for SearchService."""

    @pytest.fixture
    def search_service(self):
        """Create SearchService instance for testing."""
        with patch('app.services.loki_client.LokiClient') as mock_loki, \
             patch('app.services.prometheus_client.PrometheusClient') as mock_prometheus, \
             patch('app.services.tempo_client.TempoClient') as mock_tempo:
            
            service = SearchService(
                loki_client=mock_loki.return_value,
                prometheus_client=mock_prometheus.return_value,
                tempo_client=mock_tempo.return_value
            )
            return service

    @pytest.mark.asyncio
    async def test_search_logs_success(self, search_service, mock_loki_response):
        """Test successful log search."""
        # Mock Loki client response
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        
        query = SearchQuery(
            freeText="authentication failed",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        assert result is not None
        assert "items" in result
        assert "stats" in result
        search_service.loki.query_range.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_metrics_success(self, search_service, mock_prometheus_response):
        """Test successful metrics search."""
        search_service.prometheus.query_range = AsyncMock(return_value=mock_prometheus_response)
        
        query = SearchQuery(
            freeText="cpu_usage",
            type="metrics",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        assert result is not None
        assert "items" in result
        assert "stats" in result
        search_service.prometheus.query_range.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_traces_success(self, search_service, mock_tempo_response):
        """Test successful trace search."""
        search_service.tempo.search = AsyncMock(return_value=mock_tempo_response)
        
        query = SearchQuery(
            freeText="authenticate_user",
            type="traces",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        assert result is not None
        assert "items" in result
        assert "stats" in result
        search_service.tempo.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_unified_success(self, search_service, mock_loki_response, 
                                        mock_prometheus_response, mock_tempo_response):
        """Test successful unified search across all sources."""
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        search_service.prometheus.query_range = AsyncMock(return_value=mock_prometheus_response)
        search_service.tempo.search = AsyncMock(return_value=mock_tempo_response)
        
        query = SearchQuery(
            freeText="authentication",
            type="all",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        assert result is not None
        assert "items" in result
        assert "stats" in result
        
        # Verify all clients were called
        search_service.loki.query_range.assert_called_once()
        search_service.prometheus.query_range.assert_called_once()
        search_service.tempo.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_service, mock_loki_response):
        """Test search with filters applied."""
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        
        query = SearchQuery(
            freeText="error",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[
                SearchFilter(field="level", operator="equals", value="error"),
                SearchFilter(field="service", operator="contains", value="api")
            ],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        assert result is not None
        
        # Verify filters were applied to query
        call_args = search_service.loki.query_range.call_args
        query_string = call_args[0][0]
        assert "level=\"error\"" in query_string
        assert "service=~\".*api.*\"" in query_string

    @pytest.mark.asyncio
    async def test_search_tenant_isolation(self, search_service):
        """Test that search enforces tenant isolation."""
        query = SearchQuery(
            freeText="test",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="different-tenant-789",
            limit=100
        )
        
        with pytest.raises(TenantIsolationError):
            await search_service.search(query, "test-tenant-456")

    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_service):
        """Test search with empty query text."""
        query = SearchQuery(
            freeText="",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        with pytest.raises(SearchError, match="Search query cannot be empty"):
            await search_service.search(query, "test-tenant-456")

    @pytest.mark.asyncio
    async def test_search_invalid_time_range(self, search_service):
        """Test search with invalid time range."""
        query = SearchQuery(
            freeText="test",
            type="logs",
            timeRange=TimeRange(from_="now", to="now-1h"),  # Invalid: from > to
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        with pytest.raises(SearchError, match="Invalid time range"):
            await search_service.search(query, "test-tenant-456")

    @pytest.mark.asyncio
    async def test_search_client_error(self, search_service):
        """Test search when client raises an error."""
        search_service.loki.query_range = AsyncMock(side_effect=Exception("Loki unavailable"))
        
        query = SearchQuery(
            freeText="test",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        with pytest.raises(SearchError, match="Search operation failed"):
            await search_service.search(query, "test-tenant-456")

    @pytest.mark.asyncio
    async def test_search_by_correlation_success(self, search_service, mock_loki_response, 
                                               mock_tempo_response):
        """Test successful correlation search."""
        search_service.tempo.get_trace = AsyncMock(return_value=mock_tempo_response)
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        
        result = await search_service.search_by_correlation("trace-123", "test-tenant-456")
        
        assert result is not None
        assert "items" in result
        search_service.tempo.get_trace.assert_called_once_with("trace-123")

    @pytest.mark.asyncio
    async def test_search_streaming(self, search_service, mock_loki_response):
        """Test streaming search functionality."""
        async def mock_stream():
            yield {"type": "result", "data": {"id": "log-1", "message": "test"}}
            yield {"type": "stats", "data": {"matched": 1}}
            yield {"type": "complete", "data": {}}
        
        search_service.loki.query_range_stream = AsyncMock(return_value=mock_stream())
        
        query = SearchQuery(
            freeText="streaming test",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        results = []
        async for item in search_service.search_streaming(query, "test-tenant-456"):
            results.append(item)
        
        assert len(results) == 3
        assert results[0]["type"] == "result"
        assert results[1]["type"] == "stats"
        assert results[2]["type"] == "complete"

    @pytest.mark.asyncio
    async def test_get_search_history(self, search_service):
        """Test retrieving search history."""
        with patch('app.core.cache.get_user_search_history') as mock_get_history:
            mock_history = [
                {
                    "id": "history-1",
                    "query": "authentication failed",
                    "timestamp": "2025-08-16T07:00:00Z",
                    "type": "logs"
                }
            ]
            mock_get_history.return_value = mock_history
            
            result = await search_service.get_search_history("test-user-123", "test-tenant-456")
            
            assert len(result) == 1
            assert result[0]["query"] == "authentication failed"

    @pytest.mark.asyncio
    async def test_save_search(self, search_service):
        """Test saving a search."""
        with patch('app.core.cache.save_user_search') as mock_save_search:
            mock_save_search.return_value = {"id": "saved-search-1"}
            
            query = SearchQuery(
                freeText="error rate",
                type="logs",
                timeRange=TimeRange(from_="now-1h", to="now"),
                filters=[],
                tenantId="test-tenant-456",
                limit=100
            )
            
            result = await search_service.save_search(
                "My Saved Search", query, "test-user-123", "test-tenant-456"
            )
            
            assert result["id"] == "saved-search-1"
            mock_save_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, search_service):
        """Test getting search suggestions."""
        with patch('app.services.search_service.SearchService._get_field_suggestions') as mock_fields, \
             patch('app.services.search_service.SearchService._get_value_suggestions') as mock_values, \
             patch('app.services.search_service.SearchService._get_service_suggestions') as mock_services:
            
            mock_fields.return_value = [{"text": "authentication", "type": "field"}]
            mock_values.return_value = [{"text": "error", "type": "value"}]
            mock_services.return_value = [{"text": "api-server", "type": "service"}]
            
            result = await search_service.get_search_suggestions("auth", "test-tenant-456")
            
            assert len(result) == 3
            assert any(s["text"] == "authentication" for s in result)
            assert any(s["text"] == "error" for s in result)
            assert any(s["text"] == "api-server" for s in result)

    @pytest.mark.asyncio
    async def test_get_facets(self, search_service):
        """Test getting search facets."""
        search_service.loki.get_label_values = AsyncMock(return_value=["api-server", "database"])
        search_service.prometheus.get_label_values = AsyncMock(return_value=["production", "staging"])
        
        query = SearchQuery(
            freeText="authentication",
            type="all",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.get_facets(query, "test-tenant-456")
        
        assert "services" in result
        assert "environments" in result
        assert len(result["services"]) == 2
        assert len(result["environments"]) == 2

    @pytest.mark.asyncio
    async def test_export_search_results(self, search_service, mock_search_results):
        """Test exporting search results."""
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        
        query = SearchQuery(
            freeText="export test",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=1000
        )
        
        result = await search_service.export_search_results(query, "csv", "test-tenant-456")
        
        assert isinstance(result, str)
        assert "timestamp" in result  # CSV header
        assert "message" in result    # CSV header

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, search_service):
        """Test getting search performance metrics."""
        with patch('app.core.metrics.get_search_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "avgLatencyMs": 125.5,
                "totalQueries": 1500,
                "errorRate": 0.02,
                "cacheHitRate": 0.85
            }
            
            result = await search_service.get_performance_metrics("test-tenant-456")
            
            assert result["avgLatencyMs"] == 125.5
            assert result["totalQueries"] == 1500
            assert result["errorRate"] == 0.02
            assert result["cacheHitRate"] == 0.85

    @pytest.mark.asyncio
    async def test_search_with_caching(self, search_service, mock_loki_response):
        """Test search with result caching."""
        with patch('app.core.cache.get_cached_result') as mock_cache_get, \
             patch('app.core.cache.set_cached_result') as mock_cache_set:
            
            # First call - cache miss
            mock_cache_get.return_value = None
            search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
            
            query = SearchQuery(
                freeText="cached query",
                type="logs",
                timeRange=TimeRange(from_="now-1h", to="now"),
                filters=[],
                tenantId="test-tenant-456",
                limit=100
            )
            
            result1 = await search_service.search(query, "test-tenant-456")
            
            assert result1 is not None
            search_service.loki.query_range.assert_called_once()
            mock_cache_set.assert_called_once()
            
            # Second call - cache hit
            mock_cache_get.return_value = result1
            search_service.loki.query_range.reset_mock()
            
            result2 = await search_service.search(query, "test-tenant-456")
            
            assert result2 == result1
            search_service.loki.query_range.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_with_rate_limiting(self, search_service):
        """Test search with rate limiting."""
        with patch('app.core.rate_limiter.check_rate_limit') as mock_rate_limit:
            mock_rate_limit.side_effect = Exception("Rate limit exceeded")
            
            query = SearchQuery(
                freeText="rate limited query",
                type="logs",
                timeRange=TimeRange(from_="now-1h", to="now"),
                filters=[],
                tenantId="test-tenant-456",
                limit=100
            )
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await search_service.search(query, "test-tenant-456")

    @pytest.mark.asyncio
    async def test_search_result_aggregation(self, search_service, mock_loki_response, 
                                           mock_prometheus_response):
        """Test aggregation of results from multiple sources."""
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        search_service.prometheus.query_range = AsyncMock(return_value=mock_prometheus_response)
        
        query = SearchQuery(
            freeText="aggregation test",
            type="all",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        # Verify results are properly aggregated
        assert "items" in result
        assert "stats" in result
        assert result["stats"]["sources"]["logs"] > 0
        assert result["stats"]["sources"]["metrics"] > 0

    @pytest.mark.asyncio
    async def test_search_timeout_handling(self, search_service):
        """Test search timeout handling."""
        import asyncio
        
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow query
            return {"data": {"result": []}}
        
        search_service.loki.query_range = slow_query
        
        query = SearchQuery(
            freeText="timeout test",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        with pytest.raises(SearchError, match="Search timeout"):
            await asyncio.wait_for(
                search_service.search(query, "test-tenant-456"),
                timeout=1.0
            )

    @pytest.mark.asyncio
    async def test_search_result_formatting(self, search_service, mock_loki_response):
        """Test proper formatting of search results."""
        search_service.loki.query_range = AsyncMock(return_value=mock_loki_response)
        
        query = SearchQuery(
            freeText="formatting test",
            type="logs",
            timeRange=TimeRange(from_="now-1h", to="now"),
            filters=[],
            tenantId="test-tenant-456",
            limit=100
        )
        
        result = await search_service.search(query, "test-tenant-456")
        
        # Verify result structure
        assert "items" in result
        assert "stats" in result
        assert "facets" in result
        
        # Verify item structure
        for item in result["items"]:
            assert "id" in item
            assert "timestamp" in item
            assert "source" in item
            assert "content" in item
        
        # Verify stats structure
        stats = result["stats"]
        assert "matched" in stats
        assert "scanned" in stats
        assert "latencyMs" in stats
        assert "sources" in stats