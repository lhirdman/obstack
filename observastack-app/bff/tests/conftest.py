"""Test configuration and fixtures."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any, List
import json
from faker import Faker

fake = Faker()

# Mock Redis and other external dependencies before any imports
@pytest.fixture(scope="session", autouse=True)
def mock_external_dependencies():
    """Mock external dependencies for all tests."""
    with patch('redis.Redis') as mock_redis_class, \
         patch('httpx.AsyncClient') as mock_httpx_class:
        
        # Mock Redis client
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.delete.return_value = True
        mock_redis_instance.exists.return_value = False
        mock_redis_instance.expire.return_value = True
        
        mock_redis_class.from_url.return_value = mock_redis_instance
        
        # Mock HTTP client
        mock_httpx_instance = AsyncMock()
        mock_httpx_class.return_value = mock_httpx_instance
        
        yield


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return {
        "user_id": "test-user-123",
        "tenant_id": "test-tenant-456",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing."""
    return {
        "user_id": "admin-user-123",
        "tenant_id": "test-tenant-456",
        "username": "adminuser",
        "email": "admin@example.com",
        "roles": ["admin"],
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers for testing."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_auth_headers():
    """Admin authentication headers for testing."""
    return {
        "Authorization": "Bearer admin-test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return {
        "items": [
            {
                "id": "log-1",
                "timestamp": "2025-08-16T07:30:00Z",
                "source": "logs",
                "service": "api-server",
                "correlationId": "trace-123",
                "content": {
                    "message": "Authentication failed for user john.doe",
                    "level": "error",
                    "labels": {"user_id": "user-456"},
                    "fields": {}
                }
            },
            {
                "id": "metric-1",
                "timestamp": "2025-08-16T07:30:00Z",
                "source": "metrics",
                "service": "api-server",
                "content": {
                    "name": "cpu_usage_percent",
                    "value": 85.5,
                    "labels": {"instance": "api-01"}
                }
            }
        ],
        "stats": {
            "matched": 2,
            "scanned": 1000,
            "latencyMs": 125,
            "sources": {"logs": 1, "metrics": 1}
        },
        "facets": []
    }


@pytest.fixture
def mock_alerts():
    """Mock alerts for testing."""
    return [
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
        },
        {
            "id": "alert-2",
            "title": "Memory Usage Warning",
            "description": "Memory usage is above 80%",
            "severity": "high",
            "status": "acknowledged",
            "source": "prometheus",
            "timestamp": "2025-08-16T07:25:00Z",
            "labels": {"service": "database"},
            "tenantId": "test-tenant-456",
            "assignee": "john.doe"
        }
    ]


@pytest.fixture
def mock_cost_summary():
    """Mock cost summary for testing."""
    return {
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
            {"name": "production", "cost": 800.25, "percentage": 64.0},
            {"name": "staging", "cost": 250.50, "percentage": 20.0}
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


@pytest.fixture
def mock_tenant():
    """Mock tenant for testing."""
    return {
        "id": "test-tenant-456",
        "name": "Test Tenant",
        "domain": "test.example.com",
        "settings": {
            "dataRetentionDays": 30,
            "maxUsers": 100,
            "features": ["search", "alerts", "insights"]
        },
        "createdAt": "2025-08-01T00:00:00Z",
        "updatedAt": "2025-08-16T07:30:00Z"
    }


@pytest.fixture
def mock_prometheus_response():
    """Mock Prometheus API response."""
    return {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "cpu_usage_percent",
                        "instance": "api-01",
                        "job": "api-server"
                    },
                    "values": [
                        [1692172200, "85.5"],
                        [1692172260, "87.2"],
                        [1692172320, "89.1"]
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_loki_response():
    """Mock Loki API response."""
    return {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {
                        "level": "error",
                        "service": "api-server"
                    },
                    "values": [
                        ["1692172200000000000", "Authentication failed for user john.doe"],
                        ["1692172260000000000", "Database connection timeout"]
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_tempo_response():
    """Mock Tempo API response."""
    return {
        "traces": [
            {
                "traceID": "trace-123",
                "spans": [
                    {
                        "traceID": "trace-123",
                        "spanID": "span-456",
                        "operationName": "authenticate_user",
                        "startTime": 1692172200000000,
                        "duration": 150000,
                        "tags": [
                            {"key": "service.name", "value": "api-server"},
                            {"key": "http.status_code", "value": "401"}
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_opencost_response():
    """Mock OpenCost API response."""
    return {
        "code": 200,
        "status": "success",
        "data": [
            {
                "name": "production/api-server",
                "properties": {
                    "cluster": "production",
                    "namespace": "production",
                    "controller": "api-server"
                },
                "window": {
                    "start": "2025-08-15T00:00:00Z",
                    "end": "2025-08-16T00:00:00Z"
                },
                "start": "2025-08-15T00:00:00Z",
                "end": "2025-08-16T00:00:00Z",
                "minutes": 1440,
                "cpuCores": 2.5,
                "cpuCoreRequestAverage": 2.0,
                "cpuCoreUsageAverage": 1.8,
                "cpuCost": 12.50,
                "cpuEfficiency": 0.9,
                "gpuCount": 0,
                "gpuCost": 0,
                "ramBytes": 8589934592,
                "ramByteRequestAverage": 6442450944,
                "ramByteUsageAverage": 5368709120,
                "ramCost": 8.75,
                "ramEfficiency": 0.83,
                "pvBytes": 107374182400,
                "pvCost": 5.25,
                "networkCost": 2.15,
                "totalCost": 28.65,
                "totalEfficiency": 0.865
            }
        ]
    }


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
    
    async def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_http_response():
    """Factory for creating mock HTTP responses."""
    def _create_response(data: Dict[str, Any], status_code: int = 200):
        return MockResponse(data, status_code)
    return _create_response