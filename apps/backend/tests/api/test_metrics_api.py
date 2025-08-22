"""
Tests for the metrics API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.models import User, Tenant
from app.services.metrics_service import metrics_service
from app.core.error_handling import ExternalServiceError


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user fixture."""
    tenant = Tenant(id=1, name="test-tenant")
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        tenant_id=1,
        roles=["user"]
    )
    user.tenant = tenant
    return user


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer mock-jwt-token"}


class TestMetricsAPI:
    """Test cases for metrics API endpoints."""
    
    @patch('app.api.v1.metrics.get_current_user')
    @patch.object(metrics_service, 'query')
    async def test_query_metrics_success(self, mock_query, mock_get_user, client, mock_user):
        """Test successful metrics query."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_query.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "up", "tenant_id": "1"},
                        "value": [1640995200, "1"]
                    }
                ]
            }
        }
        
        # Make request
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "up"},
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["resultType"] == "vector"
        
        # Verify service was called with correct parameters
        mock_query.assert_called_once_with(
            query="up",
            tenant_id=1,
            time=None
        )
    
    @patch('app.api.v1.metrics.get_current_user')
    @patch.object(metrics_service, 'query')
    async def test_query_metrics_with_time(self, mock_query, mock_get_user, client, mock_user):
        """Test metrics query with specific timestamp."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_query.return_value = {
            "status": "success",
            "data": {"resultType": "vector", "result": []}
        }
        
        # Make request
        response = client.post(
            "/api/v1/metrics/query",
            json={
                "query": "up",
                "time": "2023-01-01T12:00:00Z"
            },
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        mock_query.assert_called_once_with(
            query="up",
            tenant_id=1,
            time="2023-01-01T12:00:00Z"
        )
    
    @patch('app.api.v1.metrics.get_current_user')
    @patch.object(metrics_service, 'query_range')
    async def test_query_range_metrics_success(self, mock_query_range, mock_get_user, client, mock_user):
        """Test successful metrics range query."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_query_range.return_value = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"__name__": "up", "tenant_id": "1"},
                        "values": [[1640995200, "1"], [1640995260, "1"]]
                    }
                ]
            }
        }
        
        # Make request
        response = client.post(
            "/api/v1/metrics/query_range",
            json={
                "query": "rate(http_requests_total[5m])",
                "start": "2023-01-01T12:00:00Z",
                "end": "2023-01-01T13:00:00Z",
                "step": "1m"
            },
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["resultType"] == "matrix"
        
        # Verify service was called with correct parameters
        mock_query_range.assert_called_once_with(
            query="rate(http_requests_total[5m])",
            tenant_id=1,
            start="2023-01-01T12:00:00Z",
            end="2023-01-01T13:00:00Z",
            step="1m"
        )
    
    @patch('app.api.v1.metrics.get_current_user')
    @patch.object(metrics_service, 'get_label_values')
    async def test_get_label_values_success(self, mock_get_label_values, mock_get_user, client, mock_user):
        """Test successful label values retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_label_values.return_value = {
            "status": "success",
            "data": ["prometheus", "node-exporter", "alertmanager"]
        }
        
        # Make request
        response = client.get(
            "/api/v1/metrics/labels/job/values",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        
        # Verify service was called with correct parameters
        mock_get_label_values.assert_called_once_with(
            label="job",
            tenant_id=1
        )
    
    async def test_query_metrics_unauthorized(self, client):
        """Test metrics query without authentication."""
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "up"}
        )
        
        assert response.status_code == 401
    
    @patch('app.api.v1.metrics.get_current_user')
    async def test_query_metrics_invalid_request(self, mock_get_user, client, mock_user):
        """Test metrics query with invalid request data."""
        mock_get_user.return_value = mock_user
        
        response = client.post(
            "/api/v1/metrics/query",
            json={},  # Missing required 'query' field
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.v1.metrics.get_current_user')
    @patch.object(metrics_service, 'query')
    async def test_query_metrics_external_service_error(self, mock_query, mock_get_user, client, mock_user):
        """Test metrics query when service raises ExternalServiceError."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_query.side_effect = ExternalServiceError("Prometheus connection failed")
        
        # Make request
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "up"},
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions - middleware should handle ExternalServiceError
        assert response.status_code == 503
        data = response.json()
        assert "Prometheus connection failed" in data["detail"]
        assert data["type"] == "application_error"
    
    @patch('app.api.v1.metrics.get_current_user')
    @patch.object(metrics_service, 'query')
    async def test_query_metrics_generic_exception(self, mock_query, mock_get_user, client, mock_user):
        """Test metrics query when service raises a generic exception."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_query.side_effect = ValueError("Unexpected error")
        
        # Make request
        response = client.post(
            "/api/v1/metrics/query",
            json={"query": "up"},
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions - middleware should catch and standardize the error
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"
        assert data["type"] == "internal_error"


class TestMetricsService:
    """Test cases for the metrics service."""
    
    def test_inject_tenant_label_simple_metric(self):
        """Test tenant label injection for simple metric."""
        query = "up"
        result = metrics_service._inject_tenant_label(query, 123)
        assert result == 'up{tenant_id="123"}'
    
    def test_inject_tenant_label_complex_query(self):
        """Test tenant label injection with complex query."""
        query = 'sum(rate(http_requests_total{status=~"5.."}[5m])) by (instance)'
        result = metrics_service._inject_tenant_label(query, 123)
        expected = '(sum(rate(http_requests_total{status=~"5.."}[5m])) by (instance)) and on() vector(1){tenant_id="123"}'
        assert result == expected
    
    def test_inject_tenant_label_invalid_tenant_id(self):
        """Test tenant label injection with invalid tenant ID."""
        query = "up"
        with pytest.raises(ValueError, match="Invalid tenant_id"):
            metrics_service._inject_tenant_label(query, 0)
        
        with pytest.raises(ValueError, match="Invalid tenant_id"):
            metrics_service._inject_tenant_label(query, -1)
    
    def test_inject_tenant_label_security(self):
        """Test that tenant label injection prevents injection attacks."""
        query = "up"
        # Test with a valid tenant ID
        result = metrics_service._inject_tenant_label(query, 123)
        assert 'tenant_id="123"' in result
        
        # Test that the function validates tenant_id type
        with pytest.raises(ValueError):
            metrics_service._inject_tenant_label(query, "malicious_string")
    
    @patch('app.services.metrics_service.PrometheusConnect')
    async def test_query_success(self, mock_prometheus_class):
        """Test successful query execution."""
        # Setup mock
        mock_prometheus = MagicMock()
        mock_prometheus_class.return_value = mock_prometheus
        mock_prometheus.custom_query.return_value = [
            {"metric": {"__name__": "up"}, "value": [1640995200, "1"]}
        ]
        
        # Create new service instance to use mocked PrometheusConnect
        from app.services.metrics_service import MetricsService
        service = MetricsService()
        
        # Execute query
        result = await service.query("up", 123)
        
        # Assertions
        assert result["status"] == "success"
        assert result["data"]["resultType"] == "vector"
        mock_prometheus.custom_query.assert_called_once_with(query='up{tenant_id="123"}')
    
    @patch('app.services.metrics_service.PrometheusConnect')
    async def test_query_with_time(self, mock_prometheus_class):
        """Test query execution with specific timestamp."""
        # Setup mock
        mock_prometheus = MagicMock()
        mock_prometheus_class.return_value = mock_prometheus
        mock_prometheus.custom_query.return_value = []
        
        # Create new service instance
        from app.services.metrics_service import MetricsService
        service = MetricsService()
        
        # Execute query
        await service.query("up", 123, time="2023-01-01T12:00:00Z")
        
        # Assertions
        mock_prometheus.custom_query.assert_called_once_with(
            query='up{tenant_id="123"}',
            params={"time": "2023-01-01T12:00:00Z"}
        )
    
    @patch('app.services.metrics_service.PrometheusConnect')
    async def test_query_range_success(self, mock_prometheus_class):
        """Test successful range query execution."""
        # Setup mock
        mock_prometheus = MagicMock()
        mock_prometheus_class.return_value = mock_prometheus
        mock_prometheus.custom_query_range.return_value = [
            {"metric": {"__name__": "up"}, "values": [[1640995200, "1"]]}
        ]
        
        # Create new service instance
        from app.services.metrics_service import MetricsService
        service = MetricsService()
        
        # Execute range query
        result = await service.query_range(
            "up", 123, "2023-01-01T12:00:00Z", "2023-01-01T13:00:00Z", "1m"
        )
        
        # Assertions
        assert result["status"] == "success"
        assert result["data"]["resultType"] == "matrix"
        mock_prometheus.custom_query_range.assert_called_once_with(
            query='up{tenant_id="123"}',
            start_time="2023-01-01T12:00:00Z",
            end_time="2023-01-01T13:00:00Z",
            step="1m"
        )
