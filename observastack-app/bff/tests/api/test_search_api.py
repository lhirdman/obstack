"""Tests for search API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.models.search import SearchQuery, TimeRange


class TestSearchAPI:
    """Test cases for search API endpoints."""

    def test_search_endpoint_success(self, client: TestClient, auth_headers, mock_search_results):
        """Test successful search request."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            # Mock user authentication
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Mock search service
            mock_search.return_value = mock_search_results
            
            # Make request
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "authentication failed",
                    "type": "logs",
                    "timeRange": {
                        "from": "now-1h",
                        "to": "now"
                    },
                    "filters": [],
                    "tenantId": "test-tenant-456",
                    "limit": 100
                },
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "stats" in data
            assert len(data["items"]) == 2
            assert data["stats"]["matched"] == 2
            
            # Verify search service was called with correct parameters
            mock_search.assert_called_once()
            call_args = mock_search.call_args[0]
            assert call_args[0].freeText == "authentication failed"
            assert call_args[0].type == "logs"
            assert call_args[1] == "test-tenant-456"

    def test_search_endpoint_validation_error(self, client: TestClient, auth_headers):
        """Test search request with validation errors."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user:
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Make request with invalid data
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "",  # Empty search text
                    "type": "invalid_type",  # Invalid search type
                    "limit": -1  # Invalid limit
                },
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

    def test_search_endpoint_unauthorized(self, client: TestClient):
        """Test search request without authentication."""
        response = client.post(
            "/api/v1/search",
            json={
                "freeText": "test query",
                "type": "logs"
            }
        )
        
        assert response.status_code == 401

    def test_search_endpoint_tenant_isolation(self, client: TestClient, auth_headers):
        """Test that search respects tenant isolation."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {"items": [], "stats": {"matched": 0}}
            
            # Make request with different tenant ID
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "test query",
                    "type": "logs",
                    "tenantId": "different-tenant-789"
                },
                headers=auth_headers
            )
            
            # Should reject request due to tenant mismatch
            assert response.status_code == 403

    def test_search_endpoint_service_error(self, client: TestClient, auth_headers):
        """Test search request when service fails."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Mock service error
            mock_search.side_effect = Exception("Search service unavailable")
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "test query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Search operation failed" in data["detail"]

    def test_search_streaming_endpoint(self, client: TestClient, auth_headers):
        """Test streaming search endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search_streaming') as mock_search_stream:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Mock streaming response
            async def mock_stream():
                yield {"type": "result", "data": {"id": "log-1", "message": "test"}}
                yield {"type": "stats", "data": {"matched": 1}}
                yield {"type": "complete", "data": {}}
            
            mock_search_stream.return_value = mock_stream()
            
            response = client.get(
                "/api/v1/search/stream",
                params={
                    "freeText": "test query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

    def test_search_history_endpoint(self, client: TestClient, auth_headers):
        """Test search history endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.get_search_history') as mock_get_history:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_history = [
                {
                    "id": "history-1",
                    "query": "authentication failed",
                    "timestamp": "2025-08-16T07:00:00Z",
                    "type": "logs"
                }
            ]
            mock_get_history.return_value = mock_history
            
            response = client.get(
                "/api/v1/search/history",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["query"] == "authentication failed"

    def test_save_search_endpoint(self, client: TestClient, auth_headers):
        """Test save search endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.save_search') as mock_save_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_save_search.return_value = {"id": "saved-search-1"}
            
            response = client.post(
                "/api/v1/search/save",
                json={
                    "name": "My Saved Search",
                    "query": {
                        "freeText": "error rate",
                        "type": "logs",
                        "filters": []
                    }
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "saved-search-1"

    def test_correlation_search_endpoint(self, client: TestClient, auth_headers, mock_search_results):
        """Test correlation search endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search_by_correlation') as mock_correlation_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_correlation_search.return_value = mock_search_results
            
            response = client.get(
                "/api/v1/search/correlation/trace-123",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "stats" in data
            
            mock_correlation_search.assert_called_once_with(
                "trace-123", "test-tenant-456"
            )

    def test_search_suggestions_endpoint(self, client: TestClient, auth_headers):
        """Test search suggestions endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.get_search_suggestions') as mock_suggestions:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_suggestions.return_value = [
                {"text": "authentication", "type": "field"},
                {"text": "error", "type": "value"},
                {"text": "api-server", "type": "service"}
            ]
            
            response = client.get(
                "/api/v1/search/suggestions",
                params={"q": "auth"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            assert data[0]["text"] == "authentication"

    def test_search_facets_endpoint(self, client: TestClient, auth_headers):
        """Test search facets endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.get_facets') as mock_facets:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_facets.return_value = {
                "services": [
                    {"name": "api-server", "count": 150},
                    {"name": "database", "count": 75}
                ],
                "levels": [
                    {"name": "error", "count": 45},
                    {"name": "warning", "count": 30}
                ]
            }
            
            response = client.post(
                "/api/v1/search/facets",
                json={
                    "freeText": "authentication",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "services" in data
            assert "levels" in data
            assert len(data["services"]) == 2

    def test_search_export_endpoint(self, client: TestClient, auth_headers):
        """Test search export endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.export_search_results') as mock_export:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_export.return_value = "csv_data_here"
            
            response = client.post(
                "/api/v1/search/export",
                json={
                    "freeText": "error",
                    "type": "logs",
                    "format": "csv",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"
            assert "csv_data_here" in response.text

    def test_search_performance_metrics(self, client: TestClient, auth_headers):
        """Test search performance metrics endpoint."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.get_performance_metrics') as mock_metrics:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["admin"]
            }
            
            mock_metrics.return_value = {
                "avgLatencyMs": 125.5,
                "totalQueries": 1500,
                "errorRate": 0.02,
                "cacheHitRate": 0.85
            }
            
            response = client.get(
                "/api/v1/search/metrics",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["avgLatencyMs"] == 125.5
            assert data["totalQueries"] == 1500

    def test_search_with_filters(self, client: TestClient, auth_headers, mock_search_results):
        """Test search with complex filters."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = mock_search_results
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "authentication",
                    "type": "logs",
                    "timeRange": {
                        "from": "2025-08-15T00:00:00Z",
                        "to": "2025-08-16T00:00:00Z"
                    },
                    "filters": [
                        {
                            "field": "level",
                            "operator": "equals",
                            "value": "error"
                        },
                        {
                            "field": "service",
                            "operator": "contains",
                            "value": "api"
                        }
                    ],
                    "tenantId": "test-tenant-456",
                    "limit": 50
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            
            # Verify filters were passed to search service
            call_args = mock_search.call_args[0]
            assert len(call_args[0].filters) == 2
            assert call_args[0].filters[0].field == "level"
            assert call_args[0].filters[1].field == "service"

    def test_search_rate_limiting(self, client: TestClient, auth_headers):
        """Test search rate limiting."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search, \
             patch('app.core.rate_limiter.is_rate_limited') as mock_rate_limit:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Mock rate limiting
            mock_rate_limit.return_value = True
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "test query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 429
            data = response.json()
            assert "Rate limit exceeded" in data["detail"]

    def test_search_caching(self, client: TestClient, auth_headers, mock_search_results):
        """Test search result caching."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search, \
             patch('app.core.cache.get_cached_result') as mock_cache_get, \
             patch('app.core.cache.set_cached_result') as mock_cache_set:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # First request - cache miss
            mock_cache_get.return_value = None
            mock_search.return_value = mock_search_results
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "cached query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            mock_search.assert_called_once()
            mock_cache_set.assert_called_once()
            
            # Second request - cache hit
            mock_cache_get.return_value = mock_search_results
            mock_search.reset_mock()
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "cached query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            mock_search.assert_not_called()  # Should use cache