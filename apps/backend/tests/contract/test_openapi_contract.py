"""Contract tests for OpenAPI specification validation."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
from jsonschema import validate, ValidationError
from typing import Dict, Any


class TestOpenAPIContract:
    """Test cases for OpenAPI contract validation."""

    @pytest.fixture
    def openapi_spec(self, client: TestClient) -> Dict[str, Any]:
        """Get OpenAPI specification."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        return response.json()

    def test_openapi_spec_structure(self, openapi_spec):
        """Test OpenAPI specification has required structure."""
        # Required top-level fields
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec
        assert "components" in openapi_spec
        
        # Info section
        info = openapi_spec["info"]
        assert "title" in info
        assert "version" in info
        assert "description" in info
        
        # Paths section
        paths = openapi_spec["paths"]
        assert len(paths) > 0

    def test_search_endpoint_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test search endpoint matches OpenAPI contract."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {
                "items": [
                    {
                        "id": "log-1",
                        "timestamp": "2025-08-16T07:30:00Z",
                        "source": "logs",
                        "service": "api-server",
                        "content": {
                            "message": "Test log message",
                            "level": "info",
                            "labels": {},
                            "fields": {}
                        }
                    }
                ],
                "stats": {
                    "matched": 1,
                    "scanned": 100,
                    "latencyMs": 45,
                    "sources": {"logs": 1}
                },
                "facets": []
            }
            
            # Make request
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "test query",
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
            
            assert response.status_code == 200
            
            # Validate response against schema
            search_path = openapi_spec["paths"]["/api/v1/search"]
            response_schema = search_path["post"]["responses"]["200"]["content"]["application/json"]["schema"]
            
            # Resolve schema references if needed
            if "$ref" in response_schema:
                schema_name = response_schema["$ref"].split("/")[-1]
                response_schema = openapi_spec["components"]["schemas"][schema_name]
            
            # Validate response data
            try:
                validate(instance=response.json(), schema=response_schema)
            except ValidationError as e:
                pytest.fail(f"Response does not match OpenAPI schema: {e}")

    def test_alerts_endpoint_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test alerts endpoint matches OpenAPI contract."""
        with patch('app.api.v1.alerts.get_current_user') as mock_get_user, \
             patch('app.services.alert_service.AlertService.get_alerts') as mock_get_alerts:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["operator"]
            }
            
            mock_get_alerts.return_value = {
                "alerts": [
                    {
                        "id": "alert-1",
                        "title": "High CPU Usage",
                        "description": "CPU usage is above 90%",
                        "severity": "critical",
                        "status": "active",
                        "source": "prometheus",
                        "timestamp": "2025-08-16T07:30:00Z",
                        "labels": {"service": "api-server"},
                        "tenantId": "test-tenant-456"
                    }
                ],
                "total": 1,
                "hasMore": False
            }
            
            response = client.get("/api/v1/alerts", headers=auth_headers)
            assert response.status_code == 200
            
            # Validate against OpenAPI schema
            alerts_path = openapi_spec["paths"]["/api/v1/alerts"]
            response_schema = alerts_path["get"]["responses"]["200"]["content"]["application/json"]["schema"]
            
            if "$ref" in response_schema:
                schema_name = response_schema["$ref"].split("/")[-1]
                response_schema = openapi_spec["components"]["schemas"][schema_name]
            
            try:
                validate(instance=response.json(), schema=response_schema)
            except ValidationError as e:
                pytest.fail(f"Response does not match OpenAPI schema: {e}")

    def test_costs_endpoint_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test costs endpoint matches OpenAPI contract."""
        with patch('app.api.v1.costs.get_current_user') as mock_get_user, \
             patch('app.services.cost_optimization_service.CostOptimizationService.get_cost_summary') as mock_costs:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_costs.return_value = {
                "totalCost": 1250.75,
                "previousPeriodCost": 1100.50,
                "trend": "up",
                "trendPercentage": 13.6,
                "breakdown": {
                    "compute": 750.25,
                    "storage": 300.50,
                    "network": 150.00,
                    "other": 50.00
                },
                "topNamespaces": [
                    {"name": "production", "cost": 800.25, "percentage": 64.0}
                ],
                "alerts": {
                    "budgetExceeded": 2,
                    "anomaliesDetected": 1,
                    "optimizationOpportunities": 5
                },
                "efficiency": {
                    "cpuUtilization": 65.5,
                    "memoryUtilization": 78.2,
                    "storageUtilization": 82.1,
                    "overallScore": 75.3
                }
            }
            
            response = client.get("/api/v1/costs/summary", headers=auth_headers)
            assert response.status_code == 200
            
            # Validate against OpenAPI schema
            costs_path = openapi_spec["paths"]["/api/v1/costs/summary"]
            response_schema = costs_path["get"]["responses"]["200"]["content"]["application/json"]["schema"]
            
            if "$ref" in response_schema:
                schema_name = response_schema["$ref"].split("/")[-1]
                response_schema = openapi_spec["components"]["schemas"][schema_name]
            
            try:
                validate(instance=response.json(), schema=response_schema)
            except ValidationError as e:
                pytest.fail(f"Response does not match OpenAPI schema: {e}")

    def test_error_response_contract(self, client: TestClient, openapi_spec):
        """Test error responses match OpenAPI contract."""
        # Test 401 Unauthorized
        response = client.get("/api/v1/search/history")
        assert response.status_code == 401
        
        # Validate error response structure
        error_data = response.json()
        assert "detail" in error_data
        
        # Test 422 Validation Error
        with patch('app.api.v1.search.get_current_user') as mock_get_user:
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "",  # Invalid empty query
                    "type": "invalid_type"  # Invalid type
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 422
            error_data = response.json()
            assert "detail" in error_data

    def test_request_validation_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test request validation matches OpenAPI contract."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user:
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Test missing required fields
            response = client.post(
                "/api/v1/search",
                json={},  # Missing required fields
                headers=auth_headers
            )
            
            assert response.status_code == 422
            
            # Test invalid field types
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": 123,  # Should be string
                    "type": "logs",
                    "limit": "invalid"  # Should be integer
                },
                headers=auth_headers
            )
            
            assert response.status_code == 422

    def test_authentication_contract(self, client: TestClient, openapi_spec):
        """Test authentication requirements match OpenAPI contract."""
        # Check that protected endpoints require authentication
        protected_endpoints = [
            "/api/v1/search",
            "/api/v1/alerts",
            "/api/v1/costs/summary",
            "/api/v1/tenants"
        ]
        
        for endpoint in protected_endpoints:
            if endpoint in openapi_spec["paths"]:
                path_spec = openapi_spec["paths"][endpoint]
                
                # Check if endpoint has security requirements
                for method_spec in path_spec.values():
                    if isinstance(method_spec, dict) and "security" in method_spec:
                        # Test that endpoint returns 401 without auth
                        response = client.get(endpoint)
                        assert response.status_code == 401

    def test_response_headers_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test response headers match OpenAPI contract."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {"items": [], "stats": {"matched": 0}}
            
            response = client.post(
                "/api/v1/search",
                json={
                    "freeText": "test",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            # Check standard headers
            assert "content-type" in response.headers
            assert response.headers["content-type"] == "application/json"

    def test_parameter_validation_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test parameter validation matches OpenAPI contract."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user:
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Test query parameter validation
            response = client.get(
                "/api/v1/search/suggestions",
                params={"q": ""},  # Empty query parameter
                headers=auth_headers
            )
            
            # Should handle empty parameter gracefully
            assert response.status_code in [200, 400]

    def test_content_type_contract(self, client: TestClient, openapi_spec, auth_headers):
        """Test content type requirements match OpenAPI contract."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user:
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Test with wrong content type
            response = client.post(
                "/api/v1/search",
                data="invalid json data",
                headers={
                    **auth_headers,
                    "Content-Type": "text/plain"
                }
            )
            
            assert response.status_code == 422

    def test_schema_definitions_contract(self, openapi_spec):
        """Test that all schema definitions are valid."""
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check that key schemas exist
        required_schemas = [
            "SearchQuery",
            "SearchResponse", 
            "Alert",
            "CostSummary",
            "Tenant",
            "ErrorResponse"
        ]
        
        for schema_name in required_schemas:
            assert schema_name in schemas, f"Required schema {schema_name} not found"
            
            schema = schemas[schema_name]
            assert "type" in schema or "$ref" in schema
            
            if "properties" in schema:
                # Validate that properties have types
                for prop_name, prop_schema in schema["properties"].items():
                    assert "type" in prop_schema or "$ref" in prop_schema

    def test_endpoint_documentation_contract(self, openapi_spec):
        """Test that all endpoints have proper documentation."""
        paths = openapi_spec["paths"]
        
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if isinstance(method_spec, dict):
                    # Check required documentation fields
                    assert "summary" in method_spec, f"Missing summary for {method} {path}"
                    assert "responses" in method_spec, f"Missing responses for {method} {path}"
                    
                    # Check that 200 response is documented for GET requests
                    if method.lower() == "get":
                        assert "200" in method_spec["responses"], f"Missing 200 response for GET {path}"

    def test_security_scheme_contract(self, openapi_spec):
        """Test that security schemes are properly defined."""
        components = openapi_spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        # Should have JWT bearer authentication
        assert "bearerAuth" in security_schemes
        bearer_auth = security_schemes["bearerAuth"]
        assert bearer_auth["type"] == "http"
        assert bearer_auth["scheme"] == "bearer"
        assert bearer_auth["bearerFormat"] == "JWT"

    def test_api_versioning_contract(self, openapi_spec):
        """Test API versioning consistency."""
        paths = openapi_spec["paths"]
        
        # All paths should start with /api/v1
        for path in paths.keys():
            assert path.startswith("/api/v1/"), f"Path {path} does not follow versioning convention"

    def test_response_status_codes_contract(self, openapi_spec):
        """Test that appropriate status codes are documented."""
        paths = openapi_spec["paths"]
        
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if isinstance(method_spec, dict) and "responses" in method_spec:
                    responses = method_spec["responses"]
                    
                    # POST endpoints should have 201 for creation
                    if method.lower() == "post" and "create" in method_spec.get("summary", "").lower():
                        assert "201" in responses, f"POST {path} should have 201 response"
                    
                    # All endpoints should have error responses
                    assert "400" in responses or "422" in responses, f"{method} {path} should have validation error response"
                    assert "401" in responses, f"{method} {path} should have unauthorized response"
                    assert "500" in responses, f"{method} {path} should have server error response"