"""Tests for Grafana client service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi import HTTPException

from app.services.grafana_client import GrafanaClient
from app.auth.models import UserContext
from app.exceptions import GrafanaException


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def user_context():
    """User context for testing."""
    return UserContext(
        user_id="test-user",
        tenant_id="test-tenant",
        roles=["user"],
        token_id="test-token",
        expires_at=None
    )


@pytest.fixture
def grafana_client(mock_httpx_client):
    """Grafana client with mocked HTTP client."""
    client = GrafanaClient(
        base_url="http://localhost:3000",
        admin_user="admin",
        admin_password="admin"
    )
    client.client = mock_httpx_client
    return client


class TestGrafanaClientInit:
    """Test Grafana client initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        with patch.dict("os.environ", {}, clear=True):
            client = GrafanaClient()
            assert client.base_url == "http://localhost:3000"
            assert client.admin_user == "admin"
            assert client.admin_password == "admin"
    
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        env_vars = {
            "GRAFANA_URL": "http://grafana:3000",
            "GRAFANA_ADMIN_USER": "custom-admin",
            "GRAFANA_ADMIN_PASSWORD": "custom-password"
        }
        
        with patch.dict("os.environ", env_vars):
            client = GrafanaClient()
            assert client.base_url == "http://grafana:3000"
            assert client.admin_user == "custom-admin"
            assert client.admin_password == "custom-password"
    
    def test_init_removes_trailing_slash(self):
        """Test that trailing slash is removed from base URL."""
        client = GrafanaClient(base_url="http://localhost:3000/")
        assert client.base_url == "http://localhost:3000"


class TestHealthCheck:
    """Test health check functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, grafana_client, mock_httpx_client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.get.return_value = mock_response
        
        result = await grafana_client.health_check()
        
        assert result is True
        mock_httpx_client.get.assert_called_once_with("http://localhost:3000/api/health")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, grafana_client, mock_httpx_client):
        """Test health check failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_httpx_client.get.return_value = mock_response
        
        result = await grafana_client.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, grafana_client, mock_httpx_client):
        """Test health check with exception."""
        mock_httpx_client.get.side_effect = httpx.RequestError("Connection failed")
        
        result = await grafana_client.health_check()
        
        assert result is False


class TestServiceAccountManagement:
    """Test service account management."""
    
    @pytest.mark.asyncio
    async def test_create_service_account_success(self, grafana_client, mock_httpx_client):
        """Test successful service account creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123, "name": "test-account"}
        mock_httpx_client.post.return_value = mock_response
        
        result = await grafana_client.create_service_account("test-account", "Viewer")
        
        assert result == {"id": 123, "name": "test-account"}
        mock_httpx_client.post.assert_called_once_with(
            "http://localhost:3000/api/serviceaccounts",
            json={"name": "test-account", "role": "Viewer", "isDisabled": False}
        )
    
    @pytest.mark.asyncio
    async def test_create_service_account_already_exists(self, grafana_client, mock_httpx_client):
        """Test service account creation when account already exists."""
        # Mock POST response (conflict)
        mock_post_response = MagicMock()
        mock_post_response.status_code = 409
        
        # Mock GET response (search)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "serviceAccounts": [{"id": 123, "name": "test-account"}]
        }
        
        mock_httpx_client.post.return_value = mock_post_response
        mock_httpx_client.get.return_value = mock_get_response
        
        result = await grafana_client.create_service_account("test-account")
        
        assert result == {"id": 123, "name": "test-account"}
        mock_httpx_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_service_account_error(self, grafana_client, mock_httpx_client):
        """Test service account creation error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_httpx_client.post.return_value = mock_response
        
        with pytest.raises(GrafanaException, match="Failed to create service account"):
            await grafana_client.create_service_account("test-account")
    
    @pytest.mark.asyncio
    async def test_create_service_account_token_success(self, grafana_client, mock_httpx_client):
        """Test successful service account token creation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "test-token"}
        mock_httpx_client.post.return_value = mock_response
        
        result = await grafana_client.create_service_account_token(123, "test-token")
        
        assert result == "test-token"
        mock_httpx_client.post.assert_called_once_with(
            "http://localhost:3000/api/serviceaccounts/123/tokens",
            json={"name": "test-token", "role": "Viewer"}
        )
    
    @pytest.mark.asyncio
    async def test_get_or_create_tenant_token_success(self, grafana_client, mock_httpx_client):
        """Test successful tenant token creation."""
        # Mock service account creation
        mock_sa_response = MagicMock()
        mock_sa_response.status_code = 201
        mock_sa_response.json.return_value = {"id": 123, "name": "tenant-test-tenant"}
        
        # Mock token creation
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"key": "tenant-token"}
        
        mock_httpx_client.post.side_effect = [mock_sa_response, mock_token_response]
        
        result = await grafana_client.get_or_create_tenant_token("test-tenant")
        
        assert result == "tenant-token"
        assert mock_httpx_client.post.call_count == 2


class TestProxyRequest:
    """Test proxy request functionality."""
    
    @pytest.mark.asyncio
    async def test_proxy_request_success(self, grafana_client, mock_httpx_client, user_context):
        """Test successful proxy request."""
        # Mock tenant token creation
        grafana_client.get_or_create_tenant_token = AsyncMock(return_value="tenant-token")
        
        # Mock HTTP request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_httpx_client.request.return_value = mock_response
        
        result = await grafana_client.proxy_request(
            method="GET",
            path="/api/search",
            user_context=user_context,
            params={"query": "test"}
        )
        
        assert result == mock_response
        mock_httpx_client.request.assert_called_once()
        
        # Verify request parameters
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["url"] == "http://localhost:3000/api/search"
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer tenant-token"
    
    @pytest.mark.asyncio
    async def test_proxy_request_with_tenant_filter(self, grafana_client, mock_httpx_client, user_context):
        """Test proxy request with tenant filtering."""
        grafana_client.get_or_create_tenant_token = AsyncMock(return_value="tenant-token")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.request.return_value = mock_response
        
        await grafana_client.proxy_request(
            method="GET",
            path="/api/search",
            user_context=user_context,
            params={"type": "dash-db"}
        )
        
        # Verify tenant filter was added
        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert "tag" in params
        assert "tenant:test-tenant" in params["tag"]
    
    @pytest.mark.asyncio
    async def test_proxy_request_error(self, grafana_client, mock_httpx_client, user_context):
        """Test proxy request with error."""
        grafana_client.get_or_create_tenant_token = AsyncMock(return_value="tenant-token")
        mock_httpx_client.request.side_effect = httpx.RequestError("Connection failed")
        
        with pytest.raises(GrafanaException, match="Proxy request failed"):
            await grafana_client.proxy_request(
                method="GET",
                path="/api/search",
                user_context=user_context
            )


class TestDashboardOperations:
    """Test dashboard operations."""
    
    @pytest.mark.asyncio
    async def test_get_dashboards_for_tenant_success(self, grafana_client, user_context):
        """Test successful dashboard retrieval for tenant."""
        mock_dashboards = [
            {"uid": "dash-1", "title": "Dashboard 1"},
            {"uid": "dash-2", "title": "Dashboard 2"}
        ]
        
        grafana_client.proxy_request = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_dashboards
        grafana_client.proxy_request.return_value = mock_response
        
        result = await grafana_client.get_dashboards_for_tenant(user_context)
        
        assert result == mock_dashboards
        grafana_client.proxy_request.assert_called_once_with(
            method="GET",
            path="/api/search",
            user_context=user_context,
            params={"type": "dash-db"}
        )
    
    @pytest.mark.asyncio
    async def test_get_dashboard_by_uid_success(self, grafana_client, user_context):
        """Test successful dashboard retrieval by UID."""
        mock_dashboard = {
            "dashboard": {"uid": "test-dash", "title": "Test Dashboard"},
            "meta": {"slug": "test-dashboard"}
        }
        
        grafana_client.proxy_request = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_dashboard
        grafana_client.proxy_request.return_value = mock_response
        
        result = await grafana_client.get_dashboard_by_uid("test-dash", user_context)
        
        assert result == mock_dashboard
        grafana_client.proxy_request.assert_called_once_with(
            method="GET",
            path="/api/dashboards/uid/test-dash",
            user_context=user_context
        )
    
    @pytest.mark.asyncio
    async def test_get_dashboard_by_uid_not_found(self, grafana_client, user_context):
        """Test dashboard retrieval when not found."""
        grafana_client.proxy_request = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        grafana_client.proxy_request.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await grafana_client.get_dashboard_by_uid("nonexistent", user_context)
        
        assert exc_info.value.status_code == 404


class TestUrlGeneration:
    """Test URL generation functionality."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_url_success(self, grafana_client, user_context):
        """Test successful dashboard URL generation."""
        grafana_client.get_or_create_tenant_token = AsyncMock(return_value="tenant-token")
        
        result = await grafana_client.get_dashboard_url(
            dashboard_uid="test-dash",
            user_context=user_context,
            panel_id=1,
            time_from="now-1h",
            time_to="now",
            refresh="5s",
            variables={"env": "prod"}
        )
        
        assert "test-dash" in result
        assert "auth_token=tenant-token" in result
        assert "tenant=test-tenant" in result
        assert "panelId=1" in result
        assert "from=now-1h" in result
        assert "to=now" in result
        assert "refresh=5s" in result
        assert "var-env=prod" in result
    
    def test_get_embed_url(self, grafana_client):
        """Test embed URL generation."""
        result = grafana_client.get_embed_url(
            dashboard_uid="test-dash",
            panel_id=1,
            theme="dark",
            time_from="now-1h",
            time_to="now",
            variables={"env": "prod"}
        )
        
        assert "/d-solo/test-dash" in result
        assert "panelId=1" in result
        assert "theme=dark" in result
        assert "kiosk=true" in result
        assert "from=now-1h" in result
        assert "to=now" in result
        assert "var-env=prod" in result
    
    def test_get_embed_url_full_dashboard(self, grafana_client):
        """Test embed URL generation for full dashboard."""
        result = grafana_client.get_embed_url(
            dashboard_uid="test-dash",
            theme="light"
        )
        
        assert "/d/test-dash" in result
        assert "panelId" not in result
        assert "theme=light" in result
        assert "kiosk=true" in result


class TestTenantFiltering:
    """Test tenant filtering functionality."""
    
    def test_requires_tenant_filter_true(self, grafana_client):
        """Test paths that require tenant filtering."""
        paths_requiring_filter = [
            "/api/search",
            "/api/dashboards/home",
            "/api/annotations",
            "/api/alerts",
            "/api/datasources/proxy/1/query"
        ]
        
        for path in paths_requiring_filter:
            assert grafana_client._requires_tenant_filter(path) is True
    
    def test_requires_tenant_filter_false(self, grafana_client):
        """Test paths that don't require tenant filtering."""
        paths_not_requiring_filter = [
            "/api/health",
            "/api/user/preferences",
            "/api/org/users",
            "/api/admin/stats"
        ]
        
        for path in paths_not_requiring_filter:
            assert grafana_client._requires_tenant_filter(path) is False
    
    def test_add_tenant_filters(self, grafana_client):
        """Test adding tenant filters to parameters."""
        params = {"type": "dash-db"}
        
        result = grafana_client._add_tenant_filters(params, "test-tenant")
        
        assert "tag" in result
        assert "tenant:test-tenant" in result["tag"]
    
    def test_add_tenant_filters_existing_tags(self, grafana_client):
        """Test adding tenant filters with existing tags."""
        params = {"tag": ["monitoring"]}
        
        result = grafana_client._add_tenant_filters(params, "test-tenant")
        
        assert "tenant:test-tenant" in result["tag"]
        assert "monitoring" in result["tag"]
    
    def test_add_tenant_filters_string_tag(self, grafana_client):
        """Test adding tenant filters with existing string tag."""
        params = {"tag": "monitoring"}
        
        result = grafana_client._add_tenant_filters(params, "test-tenant")
        
        assert isinstance(result["tag"], list)
        assert "tenant:test-tenant" in result["tag"]
        assert "monitoring" in result["tag"]


class TestCleanup:
    """Test cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_close(self, grafana_client, mock_httpx_client):
        """Test client cleanup."""
        await grafana_client.close()
        
        mock_httpx_client.aclose.assert_called_once()