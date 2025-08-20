"""Unit tests for Loki client."""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx

from app.services.loki_client import LokiClient
from app.models.search import SearchQuery, SearchType, TimeRange, SearchFilter, SearchOperator
from app.exceptions import SearchException


@pytest.fixture
def loki_client():
    """Create Loki client for testing."""
    return LokiClient(base_url="http://test-loki:3100", timeout=10)


@pytest.fixture
def sample_search_query():
    """Create sample search query."""
    return SearchQuery(
        free_text="error",
        type=SearchType.LOGS,
        time_range=TimeRange(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now()
        ),
        filters=[
            SearchFilter(
                field="level",
                operator=SearchOperator.EQUALS,
                value="error"
            )
        ],
        tenant_id="test-tenant",
        limit=100
    )


@pytest.fixture
def mock_loki_response():
    """Create mock Loki response."""
    return {
        "status": "success",
        "data": {
            "result": [
                {
                    "stream": {
                        "service": "api",
                        "level": "error",
                        "tenant_id": "test-tenant"
                    },
                    "values": [
                        ["1640995200000000000", '{"message": "Database connection failed", "level": "error"}'],
                        ["1640995260000000000", "Plain text error message"]
                    ]
                }
            ]
        }
    }


class TestLokiClient:
    """Test cases for LokiClient."""
    
    @pytest.mark.asyncio
    async def test_search_logs_success(self, loki_client, sample_search_query, mock_loki_response):
        """Test successful log search."""
        with patch.object(loki_client, '_client') as mock_client:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_loki_response
            mock_response.raise_for_status.return_value = None
            mock_response.elapsed.total_seconds.return_value = 0.5
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Execute search
            items, stats = await loki_client.search_logs(sample_search_query, "test-tenant")
            
            # Verify results
            assert len(items) == 2
            assert stats.matched == 2
            assert stats.latency_ms == 500
            assert stats.sources["loki"] == 2
            
            # Verify first item (structured log)
            first_item = items[0]
            assert first_item.source == SearchType.LOGS
            assert first_item.service == "api"
            assert first_item.tenant_id == "test-tenant"
            assert first_item.content.message == "Database connection failed"
            assert first_item.content.level.value == "error"
            
            # Verify second item (plain text log)
            second_item = items[1]
            assert second_item.content.message == "Plain text error message"
            assert second_item.content.level.value == "info"  # Default level
    
    @pytest.mark.asyncio
    async def test_search_logs_http_error(self, loki_client, sample_search_query):
        """Test log search with HTTP error."""
        with patch.object(loki_client, '_client') as mock_client:
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            
            with pytest.raises(SearchException, match="Loki request failed"):
                await loki_client.search_logs(sample_search_query, "test-tenant")
    
    @pytest.mark.asyncio
    async def test_search_logs_loki_error(self, loki_client, sample_search_query):
        """Test log search with Loki error response."""
        with patch.object(loki_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "status": "error",
                "data": {"error": "Invalid query"}
            }
            mock_response.raise_for_status.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(SearchException, match="Loki query failed"):
                await loki_client.search_logs(sample_search_query, "test-tenant")
    
    def test_build_logql_query_basic(self, loki_client):
        """Test basic LogQL query building."""
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
        
        logql = loki_client._build_logql_query(query, "test-tenant")
        
        assert 'tenant_id="test-tenant"' in logql
        assert '|~ "(?i).*error.*"' in logql
    
    def test_build_logql_query_with_filters(self, loki_client):
        """Test LogQL query building with filters."""
        query = SearchQuery(
            free_text="",
            type=SearchType.LOGS,
            time_range=TimeRange(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now()
            ),
            filters=[
                SearchFilter(
                    field="level",
                    operator=SearchOperator.EQUALS,
                    value="error"
                ),
                SearchFilter(
                    field="service",
                    operator=SearchOperator.CONTAINS,
                    value="api"
                )
            ],
            tenant_id="test-tenant"
        )
        
        logql = loki_client._build_logql_query(query, "test-tenant")
        
        assert 'tenant_id="test-tenant"' in logql
        assert '| json | level="error"' in logql
        assert '| json | service=~".*api.*"' in logql
    
    def test_build_filter_clause(self, loki_client):
        """Test filter clause building."""
        # Test equals filter
        equals_filter = SearchFilter(
            field="level",
            operator=SearchOperator.EQUALS,
            value="error"
        )
        clause = loki_client._build_filter_clause(equals_filter)
        assert clause == '| json | level="error"'
        
        # Test contains filter
        contains_filter = SearchFilter(
            field="message",
            operator=SearchOperator.CONTAINS,
            value="database"
        )
        clause = loki_client._build_filter_clause(contains_filter)
        assert clause == '| json | message=~".*database.*"'
        
        # Test regex filter
        regex_filter = SearchFilter(
            field="service",
            operator=SearchOperator.REGEX,
            value="api-.*"
        )
        clause = loki_client._build_filter_clause(regex_filter)
        assert clause == '| json | service=~"api-.*"'
    
    def test_parse_loki_response(self, loki_client, mock_loki_response):
        """Test parsing Loki response data."""
        items = loki_client._parse_loki_response(
            mock_loki_response["data"], 
            "test-tenant"
        )
        
        assert len(items) == 2
        
        # Check first item (structured JSON log)
        first_item = items[0]
        assert first_item.service == "api"
        assert first_item.tenant_id == "test-tenant"
        assert first_item.content.message == "Database connection failed"
        assert first_item.content.level.value == "error"
        assert "service" in first_item.content.labels
        
        # Check second item (plain text log)
        second_item = items[1]
        assert second_item.content.message == "Plain text error message"
        assert second_item.content.level.value == "info"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, loki_client):
        """Test successful health check."""
        with patch.object(loki_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            
            is_healthy = await loki_client.health_check()
            
            assert is_healthy is True
            mock_client.get.assert_called_once_with("http://test-loki:3100/ready")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, loki_client):
        """Test failed health check."""
        with patch.object(loki_client, '_client') as mock_client:
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            
            is_healthy = await loki_client.health_check()
            
            assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_close(self, loki_client):
        """Test client cleanup."""
        with patch.object(loki_client, '_client') as mock_client:
            mock_client.aclose = AsyncMock()
            
            await loki_client.close()
            
            mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_parameters(self, loki_client, sample_search_query):
        """Test that correct query parameters are sent to Loki."""
        with patch.object(loki_client, '_client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "success", "data": {"result": []}}
            mock_response.raise_for_status.return_value = None
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Execute search
            await loki_client.search_logs(sample_search_query, "test-tenant")
            
            # Verify the call was made with correct parameters
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://test-loki:3100/loki/api/v1/query_range"
            
            params = call_args[1]["params"]
            assert "query" in params
            assert "start" in params
            assert "end" in params
            assert "limit" in params
            assert params["limit"] == 100
            assert params["direction"] == "backward"  # desc sort order