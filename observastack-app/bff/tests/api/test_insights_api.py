"""Unit tests for insights API endpoints."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
import json

from app.main import app
from app.models.insights import (
    CostOptimizationRequest, CostOptimizationResponse, 
    TrendAnalysisRequest, ResourceUtilization, Recommendation,
    RecommendationType, ImpactLevel, EffortLevel
)
from app.auth.models import UserContext


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create mock user context."""
    return UserContext(
        user_id="test-user-123",
        tenant_id="test-tenant-123",
        roles=["user"],
        permissions=["read:insights", "write:insights"]
    )


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # In a real test, you would generate a valid JWT token
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_cost_optimization_response():
    """Create sample cost optimization response."""
    return CostOptimizationResponse(
        success=True,
        current_cost=1000.0,
        optimized_cost=750.0,
        potential_savings=250.0,
        savings_percentage=25.0,
        recommendations=[
            Recommendation(
                id="rec1",
                type=RecommendationType.RIGHTSIZING,
                title="Downsize CPU allocation for web-service",
                description="CPU utilization is low, consider reducing allocation",
                impact=ImpactLevel.MEDIUM,
                effort=EffortLevel.LOW,
                estimated_savings=150.0,
                created_at=datetime.utcnow()
            )
        ],
        implementation_plan=[
            {
                "phase": 1,
                "title": "Quick Wins",
                "recommendations": ["rec1"],
                "estimated_duration": "1-2 weeks"
            }
        ],
        risk_assessment={
            "overall_risk": "low",
            "risk_score": 1,
            "factors": {"downsize_recommendations": 1}
        }
    )


@pytest.fixture
def sample_utilization_data():
    """Create sample resource utilization data."""
    return [
        ResourceUtilization(
            resource="web-service_cpu",
            current=2.0,
            capacity=4.0,
            utilization=50.0,
            trend=[
                {"timestamp": datetime.utcnow() - timedelta(hours=i), "value": 2.0}
                for i in range(24)
            ],
            recommendations=[],
            threshold_breaches=0,
            last_updated=datetime.utcnow()
        ),
        ResourceUtilization(
            resource="api-service_memory",
            current=4.0,
            capacity=8.0,
            utilization=50.0,
            trend=[
                {"timestamp": datetime.utcnow() - timedelta(hours=i), "value": 4.0}
                for i in range(24)
            ],
            recommendations=[],
            threshold_breaches=0,
            last_updated=datetime.utcnow()
        )
    ]


class TestInsightsAPI:
    """Test cases for insights API endpoints."""
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_get_insights_dashboard_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test successful insights dashboard retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_service.analyze_cost_optimization = AsyncMock(return_value=CostOptimizationResponse(
            success=True,
            current_cost=1000.0,
            optimized_cost=800.0,
            potential_savings=200.0,
            savings_percentage=20.0,
            recommendations=[],
            implementation_plan=[],
            risk_assessment={}
        ))
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(
            "/api/v1/insights/dashboard",
            headers=auth_headers,
            params={
                "time_range_start": "2024-01-01T00:00:00Z",
                "time_range_end": "2024-01-02T00:00:00Z"
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "cost_insights" in data
        assert "resource_utilization" in data
        assert "capacity_forecasts" in data
        assert "summary_metrics" in data
        assert "generated_at" in data
        
        # Verify summary metrics
        summary = data["summary_metrics"]
        assert "total_services" in summary
        assert "avg_cpu_utilization" in summary
        assert "avg_memory_utilization" in summary
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_get_insights_dashboard_with_filters(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test insights dashboard with category and service filters."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_service.analyze_cost_optimization = AsyncMock(return_value=CostOptimizationResponse(
            success=True,
            current_cost=500.0,
            optimized_cost=400.0,
            potential_savings=100.0,
            savings_percentage=20.0,
            recommendations=[],
            implementation_plan=[],
            risk_assessment={}
        ))
        mock_get_service.return_value = mock_service
        
        # Make request with filters
        response = client.get(
            "/api/v1/insights/dashboard",
            headers=auth_headers,
            params={
                "categories": ["cost", "capacity"],
                "services": ["web-service", "api-service"],
                "severity_filter": ["high", "medium"],
                "include_recommendations": True
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        
        # Verify service was called with correct parameters
        mock_service.get_resource_utilization.assert_called_once()
        call_args = mock_service.get_resource_utilization.call_args
        assert call_args[0][0] == ["web-service", "api-service"]  # services parameter
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_analyze_cost_optimization_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_cost_optimization_response,
        auth_headers
    ):
        """Test successful cost optimization analysis."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.analyze_cost_optimization = AsyncMock(return_value=sample_cost_optimization_response)
        mock_get_service.return_value = mock_service
        
        # Prepare request data
        request_data = {
            "services": ["web-service", "api-service"],
            "time_range": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-02T00:00:00Z"
            },
            "optimization_goals": ["reduce_costs", "improve_efficiency"]
        }
        
        # Make request
        response = client.post(
            "/api/v1/insights/cost-optimization",
            headers=auth_headers,
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["current_cost"] == 1000.0
        assert data["optimized_cost"] == 750.0
        assert data["potential_savings"] == 250.0
        assert data["savings_percentage"] == 25.0
        assert len(data["recommendations"]) == 1
        assert len(data["implementation_plan"]) == 1
        assert "overall_risk" in data["risk_assessment"]
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_analyze_trends_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user,
        auth_headers
    ):
        """Test successful trend analysis."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.analyze_trends = AsyncMock(return_value=MagicMock(
            success=True,
            trends={"cpu_usage": [{"timestamp": "2024-01-01T00:00:00", "value": 50.0}]},
            correlations={"cpu_vs_memory": 0.75},
            forecasts={"cpu_usage": [{"timestamp": "2024-01-02T00:00:00", "value": 52.0}]},
            insights=["CPU usage has increased by 10% in recent period"]
        ))
        mock_get_service.return_value = mock_service
        
        # Prepare request data
        request_data = {
            "metrics": ["cpu_usage", "memory_usage"],
            "time_range": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-02T00:00:00Z"
            },
            "services": ["web-service"],
            "aggregation": "avg",
            "granularity": "1h"
        }
        
        # Make request
        response = client.post(
            "/api/v1/insights/trend-analysis",
            headers=auth_headers,
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "trends" in data
        assert "correlations" in data
        assert "forecasts" in data
        assert "insights" in data
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_get_resource_utilization_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test successful resource utilization retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(
            "/api/v1/insights/resource-utilization",
            headers=auth_headers,
            params={
                "services": ["web-service", "api-service"],
                "time_range_start": "2024-01-01T00:00:00Z",
                "time_range_end": "2024-01-02T00:00:00Z"
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify first resource
        resource = data[0]
        assert resource["resource"] == "web-service_cpu"
        assert resource["current"] == 2.0
        assert resource["capacity"] == 4.0
        assert resource["utilization"] == 50.0
        assert "trend" in resource
        assert "last_updated" in resource
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_get_cost_breakdown_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test successful cost breakdown retrieval."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_service.cost_per_cpu_hour = 0.05
        mock_service.cost_per_gb_memory_hour = 0.01
        mock_service.cost_per_gb_storage_hour = 0.0001
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(
            "/api/v1/insights/cost-breakdown",
            headers=auth_headers,
            params={
                "group_by": "service",
                "time_range_start": "2024-01-01T00:00:00Z",
                "time_range_end": "2024-01-02T00:00:00Z"
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "breakdown" in data
        assert "total_cost" in data
        assert "group_by" in data
        assert "currency" in data
        assert data["group_by"] == "service"
        assert data["currency"] == "USD"
        
        # Verify breakdown structure
        breakdown = data["breakdown"]
        assert isinstance(breakdown, dict)
        
        # Should have entries for web-service and api-service
        for service_name in breakdown.keys():
            service_data = breakdown[service_name]
            assert "total_cost" in service_data
            assert "cpu_cost" in service_data
            assert "memory_cost" in service_data
            assert "storage_cost" in service_data
            assert "resources" in service_data
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_stream_recommendations_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test successful streaming recommendations."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_service.generate_rightsizing_recommendations = AsyncMock(return_value=[
            Recommendation(
                id="rec1",
                type=RecommendationType.RIGHTSIZING,
                title="Test recommendation",
                description="Test description",
                impact=ImpactLevel.MEDIUM,
                effort=EffortLevel.LOW,
                estimated_savings=100.0,
                created_at=datetime.utcnow()
            )
        ])
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(
            "/api/v1/insights/recommendations/stream",
            headers=auth_headers,
            params={
                "services": ["web-service"],
                "time_range_start": "2024-01-01T00:00:00Z",
                "time_range_end": "2024-01-02T00:00:00Z"
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Verify streaming content
        content = response.text
        assert "data:" in content
        assert "type" in content
        assert "status" in content or "recommendation" in content
    
    @patch('app.api.v1.insights.get_current_user')
    def test_perform_benchmarking_placeholder(
        self, 
        mock_get_user, 
        client, 
        mock_user,
        auth_headers
    ):
        """Test benchmarking endpoint (placeholder implementation)."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        # Prepare request data
        request_data = {
            "service": "web-service",
            "metrics": ["cpu_utilization", "memory_utilization"],
            "time_range": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-02T00:00:00Z"
            },
            "comparison_type": "historical"
        }
        
        # Make request
        response = client.post(
            "/api/v1/insights/benchmarking",
            headers=auth_headers,
            json=request_data
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["service"] == "web-service"
        assert "benchmarks" in data
        assert "performance_score" in data
        assert "recommendations" in data
        assert "comparison_data" in data
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_error_handling(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user,
        auth_headers
    ):
        """Test error handling in insights endpoints."""
        # Setup mocks to raise exception
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        mock_get_service.return_value = mock_service
        
        # Make request that should fail
        response = client.get(
            "/api/v1/insights/resource-utilization",
            headers=auth_headers
        )
        
        # Verify error response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower()
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to insights endpoints."""
        # Make request without authentication
        response = client.get("/api/v1/insights/dashboard")
        
        # Should return 401 or 403 depending on middleware configuration
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_default_time_range_handling(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test default time range handling when not provided."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_get_service.return_value = mock_service
        
        # Make request without time range parameters
        response = client.get(
            "/api/v1/insights/resource-utilization",
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with default time range (last 24 hours)
        mock_service.get_resource_utilization.assert_called_once()
        call_args = mock_service.get_resource_utilization.call_args
        time_range = call_args[0][1]  # Second argument is time_range
        
        assert "start" in time_range
        assert "end" in time_range
        
        # Verify it's approximately 24 hours
        start_time = datetime.fromisoformat(time_range["start"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(time_range["end"].replace('Z', '+00:00'))
        duration = end_time - start_time
        
        # Should be approximately 24 hours (allow some tolerance for test execution time)
        assert 23.5 <= duration.total_seconds() / 3600 <= 24.5
    
    @patch('app.api.v1.insights.get_current_user')
    @patch('app.api.v1.insights.get_cost_optimization_service')
    def test_cost_breakdown_grouping_options(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        mock_user, 
        sample_utilization_data,
        auth_headers
    ):
        """Test different grouping options for cost breakdown."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_service = MagicMock()
        mock_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        mock_service.cost_per_cpu_hour = 0.05
        mock_service.cost_per_gb_memory_hour = 0.01
        mock_service.cost_per_gb_storage_hour = 0.0001
        mock_get_service.return_value = mock_service
        
        # Test different grouping options
        for group_by in ["service", "resource_type", "time"]:
            response = client.get(
                "/api/v1/insights/cost-breakdown",
                headers=auth_headers,
                params={"group_by": group_by}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["group_by"] == group_by
            assert "breakdown" in data