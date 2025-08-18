"""Integration tests for API endpoints with test database."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from typing import Dict, Any


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def async_client(self):
        """Async test client for FastAPI app."""
        from app.main import app
        return AsyncClient(app=app, base_url="http://test")

    @pytest.mark.asyncio
    async def test_full_search_workflow(self, async_client, auth_headers, mock_search_results):
        """Test complete search workflow from API to service layer."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.loki_client.LokiClient.query_range') as mock_loki, \
             patch('app.services.prometheus_client.PrometheusClient.query_range') as mock_prometheus:
            
            # Mock authentication
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Mock service responses
            mock_loki.return_value = {
                "status": "success",
                "data": {
                    "resultType": "streams",
                    "result": [
                        {
                            "stream": {"level": "error", "service": "api-server"},
                            "values": [["1692172200000000000", "Authentication failed"]]
                        }
                    ]
                }
            }
            
            mock_prometheus.return_value = {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"__name__": "cpu_usage", "instance": "api-01"},
                            "values": [[1692172200, "85.5"]]
                        }
                    ]
                }
            }
            
            # Make search request
            response = await async_client.post(
                "/api/v1/search",
                json={
                    "freeText": "authentication failed",
                    "type": "all",
                    "timeRange": {"from": "now-1h", "to": "now"},
                    "filters": [],
                    "tenantId": "test-tenant-456",
                    "limit": 100
                },
                headers=auth_headers
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "stats" in data
            assert len(data["items"]) > 0

    @pytest.mark.asyncio
    async def test_alert_management_workflow(self, async_client, auth_headers, mock_alerts):
        """Test complete alert management workflow."""
        with patch('app.api.v1.alerts.get_current_user') as mock_get_user, \
             patch('app.services.alert_service.AlertService.get_alerts') as mock_get_alerts, \
             patch('app.services.alert_service.AlertService.acknowledge_alert') as mock_acknowledge:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["operator"]
            }
            
            mock_get_alerts.return_value = {
                "alerts": mock_alerts,
                "total": len(mock_alerts),
                "hasMore": False
            }
            
            mock_acknowledge.return_value = {"success": True}
            
            # Get alerts
            response = await async_client.get(
                "/api/v1/alerts",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert len(data["alerts"]) == 2
            
            # Acknowledge alert
            response = await async_client.post(
                "/api/v1/alerts/alert-1/acknowledge",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            mock_acknowledge.assert_called_once_with("alert-1", "test-tenant-456")

    @pytest.mark.asyncio
    async def test_cost_monitoring_workflow(self, async_client, auth_headers, mock_cost_summary):
        """Test complete cost monitoring workflow."""
        with patch('app.api.v1.costs.get_current_user') as mock_get_user, \
             patch('app.services.opencost_client.OpenCostClient.get_allocation') as mock_opencost:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_opencost.return_value = {
                "code": 200,
                "data": [
                    {
                        "name": "production/api-server",
                        "totalCost": 28.65,
                        "cpuCost": 12.50,
                        "ramCost": 8.75,
                        "pvCost": 5.25,
                        "networkCost": 2.15
                    }
                ]
            }
            
            # Get cost summary
            response = await async_client.get(
                "/api/v1/costs/summary",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "totalCost" in data
            assert "breakdown" in data

    @pytest.mark.asyncio
    async def test_tenant_management_workflow(self, async_client, admin_auth_headers, mock_tenant):
        """Test complete tenant management workflow."""
        with patch('app.api.v1.tenants.get_current_user') as mock_get_user, \
             patch('app.services.tenant_service.TenantService.create_tenant') as mock_create, \
             patch('app.services.tenant_service.TenantService.get_tenant') as mock_get, \
             patch('app.services.tenant_service.TenantService.update_tenant') as mock_update:
            
            mock_get_user.return_value = {
                "user_id": "admin-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["admin"]
            }
            
            mock_create.return_value = mock_tenant
            mock_get.return_value = mock_tenant
            mock_update.return_value = mock_tenant
            
            # Create tenant
            response = await async_client.post(
                "/api/v1/tenants",
                json={
                    "name": "New Tenant",
                    "domain": "new.example.com",
                    "settings": {
                        "dataRetentionDays": 30,
                        "maxUsers": 50
                    }
                },
                headers=admin_auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Tenant"
            
            # Get tenant
            response = await async_client.get(
                "/api/v1/tenants/test-tenant-456",
                headers=admin_auth_headers
            )
            
            assert response.status_code == 200
            
            # Update tenant
            response = await async_client.put(
                "/api/v1/tenants/test-tenant-456",
                json={
                    "name": "Updated Tenant",
                    "settings": {
                        "dataRetentionDays": 60
                    }
                },
                headers=admin_auth_headers
            )
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_grafana_integration_workflow(self, async_client, auth_headers):
        """Test Grafana integration workflow."""
        with patch('app.api.v1.grafana.get_current_user') as mock_get_user, \
             patch('app.services.grafana_client.GrafanaClient.get_dashboard') as mock_get_dashboard, \
             patch('app.services.grafana_client.GrafanaClient.proxy_request') as mock_proxy:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_get_dashboard.return_value = {
                "dashboard": {
                    "id": 1,
                    "title": "System Metrics",
                    "panels": []
                }
            }
            
            mock_proxy.return_value = {
                "status": "success",
                "data": "dashboard_content"
            }
            
            # Get dashboard
            response = await async_client.get(
                "/api/v1/grafana/dashboards/system-metrics",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            
            # Proxy request
            response = await async_client.get(
                "/api/v1/grafana/proxy/api/datasources",
                headers=auth_headers
            )
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, async_client, auth_headers):
        """Test error handling across API layers."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Test service error
            mock_search.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
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

    @pytest.mark.asyncio
    async def test_authentication_integration(self, async_client):
        """Test authentication integration."""
        # Test without authentication
        response = await async_client.get("/api/v1/search/history")
        assert response.status_code == 401
        
        # Test with invalid token
        response = await async_client.get(
            "/api/v1/search/history",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, async_client, auth_headers):
        """Test rate limiting integration."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.core.rate_limiter.is_rate_limited') as mock_rate_limit:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_rate_limit.return_value = True
            
            response = await async_client.post(
                "/api/v1/search",
                json={
                    "freeText": "rate limited query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_caching_integration(self, async_client, auth_headers, mock_search_results):
        """Test caching integration across requests."""
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
            
            response1 = await async_client.post(
                "/api/v1/search",
                json={
                    "freeText": "cached query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response1.status_code == 200
            mock_search.assert_called_once()
            mock_cache_set.assert_called_once()
            
            # Second request - cache hit
            mock_cache_get.return_value = mock_search_results
            mock_search.reset_mock()
            
            response2 = await async_client.post(
                "/api/v1/search",
                json={
                    "freeText": "cached query",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            assert response2.status_code == 200
            mock_search.assert_not_called()  # Should use cache

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client, auth_headers, mock_search_results):
        """Test handling of concurrent requests."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = mock_search_results
            
            # Make multiple concurrent requests
            tasks = []
            for i in range(5):
                task = async_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": f"concurrent query {i}",
                        "type": "logs",
                        "tenantId": "test-tenant-456"
                    },
                    headers=auth_headers
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_integration(self, async_client):
        """Test health check endpoint integration."""
        with patch('app.services.loki_client.LokiClient.health_check') as mock_loki_health, \
             patch('app.services.prometheus_client.PrometheusClient.health_check') as mock_prom_health, \
             patch('app.services.tempo_client.TempoClient.health_check') as mock_tempo_health:
            
            mock_loki_health.return_value = {"status": "healthy"}
            mock_prom_health.return_value = {"status": "healthy"}
            mock_tempo_health.return_value = {"status": "healthy"}
            
            response = await async_client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data
            assert data["services"]["loki"]["status"] == "healthy"
            assert data["services"]["prometheus"]["status"] == "healthy"
            assert data["services"]["tempo"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_metrics_endpoint_integration(self, async_client):
        """Test metrics endpoint integration."""
        with patch('app.core.monitoring.get_application_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "requests_total": 1500,
                "requests_per_second": 25.5,
                "error_rate": 0.02,
                "avg_response_time": 125.5
            }
            
            response = await async_client.get("/api/v1/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["requests_total"] == 1500
            assert data["requests_per_second"] == 25.5

    @pytest.mark.asyncio
    async def test_openapi_spec_integration(self, async_client):
        """Test OpenAPI specification endpoint."""
        response = await async_client.get("/openapi.json")
        
        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        
        # Verify key endpoints are documented
        assert "/api/v1/search" in spec["paths"]
        assert "/api/v1/alerts" in spec["paths"]
        assert "/api/v1/costs/summary" in spec["paths"]