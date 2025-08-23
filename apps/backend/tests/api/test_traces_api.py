"""
Tests for the traces API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.models import User, Tenant
from app.services.tempo_service import tempo_service
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


@pytest.fixture
def mock_trace_data():
    """Mock trace data fixture."""
    return {
        "batches": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "tenant_id",
                            "value": {"stringValue": "1"}
                        },
                        {
                            "key": "service.name",
                            "value": {"stringValue": "frontend"}
                        }
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "1234567890abcdef",
                                "spanId": "abcdef1234567890",
                                "name": "GET /api/users",
                                "startTimeUnixNano": "1640995200000000000",
                                "endTimeUnixNano": "1640995201000000000",
                                "attributes": [
                                    {
                                        "key": "http.method",
                                        "value": {"stringValue": "GET"}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


class TestTracesAPI:
    """Test cases for traces API endpoints."""
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'get_trace')
    async def test_get_trace_success(self, mock_get_trace, mock_get_user, client, mock_user, mock_trace_data):
        """Test successful trace retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_trace.return_value = mock_trace_data
        
        # Make request
        response = client.get(
            "/api/v1/traces/1234567890abcdef",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "batches" in data
        assert len(data["batches"]) == 1
        
        # Verify service was called with correct parameters
        mock_get_trace.assert_called_once_with(
            trace_id="1234567890abcdef",
            tenant_id=1
        )
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'get_trace')
    async def test_get_trace_not_found(self, mock_get_trace, mock_get_user, client, mock_user):
        """Test trace retrieval when trace is not found."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_trace.side_effect = ExternalServiceError("Trace not found", status_code=404)
        
        # Make request
        response = client.get(
            "/api/v1/traces/nonexistent",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Trace not found"
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'get_trace')
    async def test_get_trace_tenant_isolation(self, mock_get_trace, mock_get_user, client, mock_user):
        """Test that users can only access traces from their tenant."""
        # Setup mocks - simulate trace belonging to different tenant
        mock_get_user.return_value = mock_user
        mock_get_trace.side_effect = ExternalServiceError("Trace not found", status_code=404)
        
        # Make request
        response = client.get(
            "/api/v1/traces/1234567890abcdef",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 404
        mock_get_trace.assert_called_once_with(
            trace_id="1234567890abcdef",
            tenant_id=1  # User's tenant ID
        )
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'search_traces')
    async def test_search_traces_success(self, mock_search_traces, mock_get_user, client, mock_user):
        """Test successful trace search."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_search_traces.return_value = {
            "traces": [
                {
                    "traceID": "1234567890abcdef",
                    "spans": [
                        {
                            "traceID": "1234567890abcdef",
                            "spanID": "abcdef1234567890",
                            "operationName": "GET /api/users",
                            "startTime": 1640995200000000,
                            "duration": 1000000
                        }
                    ]
                }
            ]
        }
        
        # Make request
        response = client.post(
            "/api/v1/traces/search",
            json={
                "service": "frontend",
                "operation": "GET /api/users",
                "start": 1640995200,
                "end": 1641081600,
                "limit": 20
            },
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "traces" in data
        assert len(data["traces"]) == 1
        
        # Verify service was called with correct parameters
        mock_search_traces.assert_called_once_with(
            tenant_id=1,
            service="frontend",
            operation="GET /api/users",
            start=1640995200,
            end=1641081600,
            limit=20
        )
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'search_traces')
    async def test_search_traces_minimal_params(self, mock_search_traces, mock_get_user, client, mock_user):
        """Test trace search with minimal parameters."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_search_traces.return_value = {"traces": []}
        
        # Make request with minimal parameters
        response = client.post(
            "/api/v1/traces/search",
            json={},
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        
        # Verify service was called with tenant_id and default limit
        mock_search_traces.assert_called_once_with(
            tenant_id=1,
            service=None,
            operation=None,
            start=None,
            end=None,
            limit=20  # Default limit
        )
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'search_traces')
    async def test_list_recent_traces_success(self, mock_search_traces, mock_get_user, client, mock_user):
        """Test successful recent traces listing."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_search_traces.return_value = {"traces": []}
        
        # Make request
        response = client.get(
            "/api/v1/traces/?limit=10",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        
        # Verify service was called with correct parameters
        mock_search_traces.assert_called_once_with(
            tenant_id=1,
            limit=10
        )
    
    async def test_get_trace_unauthorized(self, client):
        """Test trace retrieval without authentication."""
        response = client.get("/api/v1/traces/1234567890abcdef")
        assert response.status_code == 401
    
    async def test_search_traces_unauthorized(self, client):
        """Test trace search without authentication."""
        response = client.post(
            "/api/v1/traces/search",
            json={"service": "frontend"}
        )
        assert response.status_code == 401
    
    @patch('app.api.v1.traces.get_current_user')
    async def test_search_traces_invalid_limit(self, mock_get_user, client, mock_user):
        """Test trace search with invalid limit parameter."""
        mock_get_user.return_value = mock_user
        
        # Test limit too high
        response = client.post(
            "/api/v1/traces/search",
            json={"limit": 200},  # Max is 100
            headers={"Authorization": "Bearer mock-token"}
        )
        assert response.status_code == 422  # Validation error
        
        # Test limit too low
        response = client.post(
            "/api/v1/traces/search",
            json={"limit": 0},  # Min is 1
            headers={"Authorization": "Bearer mock-token"}
        )
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'get_trace')
    async def test_get_trace_service_error(self, mock_get_trace, mock_get_user, client, mock_user):
        """Test trace retrieval when service raises an error."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_get_trace.side_effect = ExternalServiceError("Tempo connection failed")
        
        # Make request
        response = client.get(
            "/api/v1/traces/1234567890abcdef",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to retrieve trace"
    
    @patch('app.api.v1.traces.get_current_user')
    @patch.object(tempo_service, 'search_traces')
    async def test_search_traces_service_error(self, mock_search_traces, mock_get_user, client, mock_user):
        """Test trace search when service raises an error."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_search_traces.side_effect = ExternalServiceError("Tempo connection failed")
        
        # Make request
        response = client.post(
            "/api/v1/traces/search",
            json={"service": "frontend"},
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to search traces"


class TestTempoService:
    """Test cases for the Tempo service."""
    
    def test_validate_tenant_access_valid(self, mock_trace_data):
        """Test tenant access validation with valid tenant."""
        result = tempo_service._validate_tenant_access(mock_trace_data, 1)
        assert result is True
    
    def test_validate_tenant_access_invalid_tenant(self, mock_trace_data):
        """Test tenant access validation with invalid tenant."""
        result = tempo_service._validate_tenant_access(mock_trace_data, 2)
        assert result is False
    
    def test_validate_tenant_access_no_tenant_id(self):
        """Test tenant access validation with trace missing tenant_id."""
        trace_data = {
            "batches": [
                {
                    "resource": {
                        "attributes": [
                            {
                                "key": "service.name",
                                "value": {"stringValue": "frontend"}
                            }
                        ]
                    },
                    "scopeSpans": []
                }
            ]
        }
        result = tempo_service._validate_tenant_access(trace_data, 1)
        assert result is False
    
    def test_validate_tenant_access_empty_data(self):
        """Test tenant access validation with empty trace data."""
        result = tempo_service._validate_tenant_access({}, 1)
        assert result is False
        
        result = tempo_service._validate_tenant_access(None, 1)
        assert result is False
    
    @patch('httpx.AsyncClient')
    async def test_get_trace_success(self, mock_client_class, mock_trace_data):
        """Test successful trace retrieval."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_trace_data
        mock_client.get.return_value = mock_response
        
        # Execute
        result = await tempo_service.get_trace("1234567890abcdef", 1)
        
        # Assertions
        assert result == mock_trace_data
        mock_client.get.assert_called_once_with("http://localhost:3200/api/traces/1234567890abcdef")
    
    @patch('httpx.AsyncClient')
    async def test_get_trace_not_found(self, mock_client_class):
        """Test trace retrieval when trace is not found."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        
        # Execute and assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await tempo_service.get_trace("nonexistent", 1)
        
        assert exc_info.value.status_code == 404
        assert "Trace not found" in str(exc_info.value)
    
    @patch('httpx.AsyncClient')
    async def test_get_trace_invalid_trace_id(self, mock_client_class):
        """Test trace retrieval with invalid trace ID."""
        # Execute and assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await tempo_service.get_trace("invalid-trace-id!", 1)
        
        assert "Invalid trace ID format" in str(exc_info.value)
    
    @patch('httpx.AsyncClient')
    async def test_search_traces_success(self, mock_client_class):
        """Test successful trace search."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"traces": []}
        mock_client.get.return_value = mock_response
        
        # Execute
        result = await tempo_service.search_traces(
            tenant_id=1,
            service="frontend",
            operation="GET /api/users",
            start=1640995200,
            end=1641081600,
            limit=20
        )
        
        # Assertions
        assert result == {"traces": []}
        mock_client.get.assert_called_once()
        
        # Check that the call was made with correct parameters
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://localhost:3200/api/search"
        params = call_args[1]["params"]
        assert params["tags"] == "tenant_id=1"
        assert params["service"] == "frontend"
        assert params["operation"] == "GET /api/users"
        assert params["start"] == 1640995200
        assert params["end"] == 1641081600
        assert params["limit"] == 20