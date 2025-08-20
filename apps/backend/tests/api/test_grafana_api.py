"""Tests for Grafana API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.auth.models import UserContext
from app.services.grafana_client import GrafanaClient
from app.exceptions import GrafanaException


@pytest.fixture
def mock_grafana_client():
    """Mock Grafana client for testing."""
    client = AsyncMock(spec=GrafanaClient)
    client.base_url = "http://localhost:3000"
    return client


@pytest.fixture
def mock_user_context():
    """Mock user context for testing."""
    return UserContext(
        user_id="test-user",
        tenant_id="test-tenant",
        roles=["user"],
        token_id="test-token",
        expires_at=None
    )


class TestGrafanaHealth:
    """Test Grafana health endpoint."""
    
    def test_grafana_health_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful Grafana health check."""
        mock_grafana_client.health_check.return_value = True
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "grafana"
        mock_grafana_client.health_check.assert_called_once()
        mock_grafana_client.close.assert_called_once()
    
    def test_grafana_health_failure(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test Grafana health check failure."""
        mock_grafana_client.health_check.return_value = False
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        mock_grafana_client.close.assert_called_once()
    
    def test_grafana_health_exception(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test Grafana health check with exception."""
        mock_grafana_client.health_check.side_effect = Exception("Connection failed")
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/health", headers=auth_headers)
        
        assert response.status_code == 503
        mock_grafana_client.close.assert_called_once()


class TestDashboardList:
    """Test dashboard listing endpoint."""
    
    def test_list_dashboards_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful dashboard listing."""
        mock_dashboards = [
            {
                "uid": "dashboard-1",
                "title": "Test Dashboard 1",
                "tags": ["monitoring"],
                "url": "/d/dashboard-1",
                "folderTitle": "Test Folder"
            },
            {
                "uid": "dashboard-2",
                "title": "Test Dashboard 2",
                "tags": ["alerts"],
                "url": "/d/dashboard-2",
                "folderTitle": None
            }
        ]
        
        mock_grafana_client.get_dashboards_for_tenant.return_value = mock_dashboards
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/dashboards", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["dashboards"]) == 2
        assert data["dashboards"][0]["uid"] == "dashboard-1"
        assert data["dashboards"][0]["title"] == "Test Dashboard 1"
        mock_grafana_client.close.assert_called_once()
    
    def test_list_dashboards_grafana_error(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test dashboard listing with Grafana error."""
        mock_grafana_client.get_dashboards_for_tenant.side_effect = GrafanaException("Grafana error")
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/dashboards", headers=auth_headers)
        
        assert response.status_code == 502
        mock_grafana_client.close.assert_called_once()


class TestDashboardDetail:
    """Test dashboard detail endpoint."""
    
    def test_get_dashboard_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful dashboard retrieval."""
        mock_dashboard = {
            "dashboard": {
                "uid": "test-dashboard",
                "title": "Test Dashboard",
                "panels": []
            },
            "meta": {
                "slug": "test-dashboard"
            }
        }
        
        mock_grafana_client.get_dashboard_by_uid.return_value = mock_dashboard
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/dashboards/test-dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["dashboard"]["uid"] == "test-dashboard"
        mock_grafana_client.get_dashboard_by_uid.assert_called_once_with("test-dashboard", pytest.any)
        mock_grafana_client.close.assert_called_once()
    
    def test_get_dashboard_not_found(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test dashboard not found."""
        from fastapi import HTTPException, status
        
        mock_grafana_client.get_dashboard_by_uid.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/dashboards/nonexistent", headers=auth_headers)
        
        assert response.status_code == 404
        mock_grafana_client.close.assert_called_once()


class TestDashboardUrl:
    """Test dashboard URL generation endpoint."""
    
    def test_generate_dashboard_url_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful dashboard URL generation."""
        mock_grafana_client.get_dashboard_url.return_value = "http://localhost:3000/d/test-dashboard?auth_token=token"
        mock_grafana_client.get_embed_url.return_value = "http://localhost:3000/d-solo/test-dashboard?kiosk=true"
        
        request_data = {
            "dashboard_uid": "test-dashboard",
            "panel_id": 1,
            "theme": "dark"
        }
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.post("/api/v1/grafana/dashboards/url", json=request_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "embed_url" in data
        mock_grafana_client.get_dashboard_url.assert_called_once()
        mock_grafana_client.get_embed_url.assert_called_once()
        mock_grafana_client.close.assert_called_once()


class TestEmbedConfig:
    """Test embed configuration endpoint."""
    
    def test_get_embed_config_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful embed config retrieval."""
        mock_grafana_client.get_or_create_tenant_token.return_value = "test-token"
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/embed/config", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["grafana_url"] == "http://localhost:3000"
        assert data["theme"] == "light"
        assert data["tenant_id"] == "test-tenant"
        assert data["auth_token"] == "test-token"
        mock_grafana_client.close.assert_called_once()


class TestGrafanaProxy:
    """Test Grafana proxy endpoint."""
    
    def test_proxy_get_request_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful GET request proxy."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.headers = {"content-type": "application/json"}
        
        mock_grafana_client.proxy_request.return_value = mock_response
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/proxy/api/search", headers=auth_headers)
        
        assert response.status_code == 200
        mock_grafana_client.proxy_request.assert_called_once()
        mock_grafana_client.close.assert_called_once()
    
    def test_proxy_post_request_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful POST request proxy."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'{"id": 123}'
        mock_response.headers = {"content-type": "application/json"}
        
        mock_grafana_client.proxy_request.return_value = mock_response
        
        request_data = {"query": "test"}
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.post(
                "/api/v1/grafana/proxy/api/annotations",
                json=request_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        mock_grafana_client.proxy_request.assert_called_once()
        mock_grafana_client.close.assert_called_once()
    
    def test_proxy_grafana_error(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test proxy with Grafana error."""
        mock_grafana_client.proxy_request.side_effect = GrafanaException("Grafana error")
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/proxy/api/search", headers=auth_headers)
        
        assert response.status_code == 502
        mock_grafana_client.close.assert_called_once()
    
    def test_proxy_http_status_error(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test proxy with HTTP status error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        http_error = httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
        mock_grafana_client.proxy_request.side_effect = http_error
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/proxy/api/nonexistent", headers=auth_headers)
        
        assert response.status_code == 404
        mock_grafana_client.close.assert_called_once()


class TestDashboardSnapshot:
    """Test dashboard snapshot endpoint."""
    
    def test_create_snapshot_success(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test successful snapshot creation."""
        mock_snapshot = {
            "id": 123,
            "key": "snapshot-key",
            "url": "http://localhost:3000/dashboard/snapshot/snapshot-key",
            "expires": "2025-08-16T00:00:00Z"
        }
        
        mock_grafana_client.create_dashboard_snapshot.return_value = mock_snapshot
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.post(
                "/api/v1/grafana/dashboards/test-dashboard/snapshot",
                params={"expires": 7200},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123
        assert data["key"] == "snapshot-key"
        mock_grafana_client.create_dashboard_snapshot.assert_called_once_with(
            dashboard_uid="test-dashboard",
            user_context=pytest.any,
            expires=7200
        )
        mock_grafana_client.close.assert_called_once()


class TestAuthentication:
    """Test authentication requirements."""
    
    def test_endpoints_require_authentication(self, client: TestClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            "/api/v1/grafana/health",
            "/api/v1/grafana/dashboards",
            "/api/v1/grafana/dashboards/test",
            "/api/v1/grafana/embed/config",
            "/api/v1/grafana/proxy/api/search"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_post_endpoints_require_authentication(self, client: TestClient):
        """Test that POST endpoints require authentication."""
        endpoints = [
            ("/api/v1/grafana/dashboards/url", {"dashboard_uid": "test"}),
            ("/api/v1/grafana/dashboards/test/snapshot", {})
        ]
        
        for endpoint, data in endpoints:
            response = client.post(endpoint, json=data)
            assert response.status_code == 401


class TestTenantIsolation:
    """Test tenant isolation in Grafana integration."""
    
    def test_tenant_context_passed_to_client(self, client: TestClient, mock_grafana_client, auth_headers):
        """Test that tenant context is properly passed to Grafana client."""
        mock_grafana_client.get_dashboards_for_tenant.return_value = []
        
        with patch("app.api.v1.grafana.get_grafana_client", return_value=mock_grafana_client):
            response = client.get("/api/v1/grafana/dashboards", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify that the user context passed has the correct tenant
        call_args = mock_grafana_client.get_dashboards_for_tenant.call_args[0]
        user_context = call_args[0]
        assert user_context.tenant_id == "test-tenant"
        mock_grafana_client.close.assert_called_once()