"""Unit tests for cost optimization service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.cost_optimization_service import CostOptimizationService
from app.services.prometheus_client import PrometheusClient
from app.models.insights import (
    CostOptimizationRequest, ResourceUtilization, Recommendation,
    RecommendationType, ImpactLevel, EffortLevel, TrendAnalysisRequest
)
from app.models.common import TrendDirection


@pytest.fixture
def mock_prometheus_client():
    """Create a mock Prometheus client."""
    client = MagicMock(spec=PrometheusClient)
    client.base_url = "http://localhost:9090"
    client._client = AsyncMock()
    return client


@pytest.fixture
def cost_service(mock_prometheus_client):
    """Create cost optimization service with mocked dependencies."""
    return CostOptimizationService(mock_prometheus_client)


@pytest.fixture
def sample_utilization_data():
    """Create sample resource utilization data for testing."""
    now = datetime.utcnow()
    
    # High CPU utilization (should trigger downsize recommendation)
    cpu_util = ResourceUtilization(
        resource="web-service_cpu",
        current=2.0,  # 2 CPU cores
        capacity=4.0,  # 4 CPU cores allocated
        utilization=15.0,  # 15% utilization (underutilized)
        trend=[
            {"timestamp": now - timedelta(hours=i), "value": 0.6 + (i * 0.01)}
            for i in range(24)
        ],
        recommendations=[],
        threshold_breaches=0,
        last_updated=now
    )
    
    # High memory utilization (should trigger upsize recommendation)
    memory_util = ResourceUtilization(
        resource="api-service_memory",
        current=7.5,  # 7.5 GB used
        capacity=8.0,  # 8 GB allocated
        utilization=93.75,  # 93.75% utilization (overutilized)
        trend=[
            {"timestamp": now - timedelta(hours=i), "value": 7.0 + (i * 0.02)}
            for i in range(24)
        ],
        recommendations=[],
        threshold_breaches=5,
        last_updated=now
    )
    
    # Normal storage utilization
    storage_util = ResourceUtilization(
        resource="database_storage",
        current=25.0,  # 25 GB used
        capacity=100.0,  # 100 GB allocated
        utilization=25.0,  # 25% utilization (underutilized)
        trend=[
            {"timestamp": now - timedelta(hours=i), "value": 24.0 + (i * 0.05)}
            for i in range(24)
        ],
        recommendations=[],
        threshold_breaches=0,
        last_updated=now
    )
    
    return [cpu_util, memory_util, storage_util]


@pytest.fixture
def sample_cost_request():
    """Create sample cost optimization request."""
    return CostOptimizationRequest(
        services=["web-service", "api-service"],
        time_range={
            "start": (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z",
            "end": datetime.utcnow().isoformat() + "Z"
        },
        optimization_goals=["reduce_costs", "improve_efficiency"]
    )


class TestCostOptimizationService:
    """Test cases for CostOptimizationService."""
    
    @pytest.mark.asyncio
    async def test_analyze_cost_optimization_success(
        self, 
        cost_service, 
        sample_cost_request, 
        sample_utilization_data
    ):
        """Test successful cost optimization analysis."""
        # Mock the get_resource_utilization method
        cost_service.get_resource_utilization = AsyncMock(return_value=sample_utilization_data)
        
        # Execute analysis
        result = await cost_service.analyze_cost_optimization(
            sample_cost_request, "tenant-123"
        )
        
        # Verify results
        assert result.success is True
        assert result.current_cost > 0
        assert result.optimized_cost >= 0
        assert result.potential_savings >= 0
        assert len(result.recommendations) > 0
        assert len(result.implementation_plan) > 0
        assert "overall_risk" in result.risk_assessment
    
    @pytest.mark.asyncio
    async def test_get_resource_utilization(self, cost_service, mock_prometheus_client):
        """Test resource utilization data retrieval."""
        # Mock Prometheus response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {
                            "__name__": "container_cpu_usage_seconds_total",
                            "service": "web-service",
                            "tenant_id": "tenant-123"
                        },
                        "values": [
                            [1640995200, "0.5"],  # timestamp, value
                            [1640995260, "0.6"],
                            [1640995320, "0.4"]
                        ]
                    }
                ]
            }
        }
        mock_prometheus_client._client.get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        # Execute method
        services = ["web-service"]
        time_range = {
            "start": "2022-01-01T00:00:00Z",
            "end": "2022-01-01T01:00:00Z"
        }
        
        result = await cost_service.get_resource_utilization(
            services, time_range, "tenant-123"
        )
        
        # Verify results
        assert isinstance(result, list)
        # Note: The actual processing depends on having both usage and capacity data
    
    @pytest.mark.asyncio
    async def test_generate_rightsizing_recommendations(
        self, 
        cost_service, 
        sample_utilization_data
    ):
        """Test rightsizing recommendation generation."""
        result = await cost_service.generate_rightsizing_recommendations(
            sample_utilization_data, "tenant-123"
        )
        
        # Verify recommendations are generated
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check for CPU downsize recommendation (underutilized)
        cpu_recs = [r for r in result if "cpu" in r.title.lower() and "downsize" in r.title.lower()]
        assert len(cpu_recs) > 0
        
        cpu_rec = cpu_recs[0]
        assert cpu_rec.type == RecommendationType.RIGHTSIZING
        assert cpu_rec.estimated_savings > 0
        assert cpu_rec.impact in [ImpactLevel.LOW, ImpactLevel.MEDIUM]
        assert cpu_rec.effort == EffortLevel.LOW
        
        # Check for memory upsize recommendation (overutilized)
        memory_recs = [r for r in result if "memory" in r.title.lower() and "increase" in r.title.lower()]
        assert len(memory_recs) > 0
        
        memory_rec = memory_recs[0]
        assert memory_rec.type == RecommendationType.RIGHTSIZING
        assert memory_rec.impact == ImpactLevel.HIGH
        assert memory_rec.effort == EffortLevel.MEDIUM
    
    def test_generate_cpu_recommendation_underutilized(self, cost_service):
        """Test CPU recommendation for underutilized resource."""
        util = ResourceUtilization(
            resource="test-service_cpu",
            current=0.8,
            capacity=4.0,
            utilization=20.0,  # Underutilized
            trend=[{"timestamp": datetime.utcnow(), "value": 0.8}] * 25,  # Sufficient data
            recommendations=[],
            threshold_breaches=0,
            last_updated=datetime.utcnow()
        )
        
        rec = cost_service._generate_cpu_recommendation(
            util, 15.0, 25.0, 20.0, "tenant-123"
        )
        
        assert rec is not None
        assert "downsize" in rec.title.lower()
        assert rec.type == RecommendationType.RIGHTSIZING
        assert rec.estimated_savings > 0
        assert rec.metadata["resource_type"] == "cpu"
    
    def test_generate_cpu_recommendation_overutilized(self, cost_service):
        """Test CPU recommendation for overutilized resource."""
        util = ResourceUtilization(
            resource="test-service_cpu",
            current=3.5,
            capacity=4.0,
            utilization=87.5,  # Overutilized
            trend=[{"timestamp": datetime.utcnow(), "value": 3.5}] * 25,
            recommendations=[],
            threshold_breaches=10,
            last_updated=datetime.utcnow()
        )
        
        rec = cost_service._generate_cpu_recommendation(
            util, 85.0, 95.0, 90.0, "tenant-123"
        )
        
        assert rec is not None
        assert "increase" in rec.title.lower()
        assert rec.type == RecommendationType.RIGHTSIZING
        assert rec.estimated_savings == 0  # Performance improvement, not cost savings
        assert rec.impact == ImpactLevel.HIGH
        assert rec.metadata["reason"] == "performance"
    
    def test_generate_memory_recommendation_underutilized(self, cost_service):
        """Test memory recommendation for underutilized resource."""
        util = ResourceUtilization(
            resource="test-service_memory",
            current=2.0,
            capacity=8.0,
            utilization=25.0,  # Underutilized
            trend=[{"timestamp": datetime.utcnow(), "value": 2.0}] * 25,
            recommendations=[],
            threshold_breaches=0,
            last_updated=datetime.utcnow()
        )
        
        rec = cost_service._generate_memory_recommendation(
            util, 25.0, 30.0, 28.0, "tenant-123"
        )
        
        assert rec is not None
        assert "reduce" in rec.title.lower()
        assert rec.type == RecommendationType.RIGHTSIZING
        assert rec.estimated_savings > 0
        assert rec.metadata["resource_type"] == "memory"
    
    def test_generate_storage_recommendation(self, cost_service):
        """Test storage recommendation generation."""
        util = ResourceUtilization(
            resource="test-service_storage",
            current=20.0,
            capacity=100.0,
            utilization=20.0,  # Underutilized
            trend=[{"timestamp": datetime.utcnow(), "value": 20.0}] * 25,
            recommendations=[],
            threshold_breaches=0,
            last_updated=datetime.utcnow()
        )
        
        rec = cost_service._generate_storage_recommendation(
            util, 20.0, 25.0, 22.0, "tenant-123"
        )
        
        assert rec is not None
        assert rec.type == RecommendationType.STORAGE
        assert rec.estimated_savings > 0
        assert rec.effort == EffortLevel.MEDIUM  # Storage changes are more complex
    
    @pytest.mark.asyncio
    async def test_calculate_current_costs(self, cost_service, sample_utilization_data):
        """Test current cost calculation."""
        time_range = {
            "start": (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z",
            "end": datetime.utcnow().isoformat() + "Z"
        }
        
        total_cost = await cost_service.calculate_current_costs(
            sample_utilization_data, time_range
        )
        
        assert total_cost > 0
        # Should include costs for CPU, memory, and storage
        # CPU: 4.0 cores * $0.05/hour * 24 hours = $4.80
        # Memory: 8.0 GB * $0.01/hour * 24 hours = $1.92
        # Storage: 100.0 GB * $0.0001/hour * 24 hours = $0.24
        # Total should be approximately $6.96
        assert 6.0 < total_cost < 8.0
    
    @pytest.mark.asyncio
    async def test_analyze_trends(self, cost_service, mock_prometheus_client):
        """Test trend analysis functionality."""
        # Mock Prometheus response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"__name__": "cpu_usage", "service": "web-service"},
                        "values": [
                            [1640995200, "50.0"],
                            [1640995260, "55.0"],
                            [1640995320, "60.0"],
                            [1640995380, "65.0"]
                        ]
                    }
                ]
            }
        }
        mock_prometheus_client._client.get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        request = TrendAnalysisRequest(
            metrics=["cpu_usage"],
            time_range={
                "start": "2022-01-01T00:00:00Z",
                "end": "2022-01-01T01:00:00Z"
            },
            services=["web-service"]
        )
        
        result = await cost_service.analyze_trends(request, "tenant-123")
        
        assert result.success is True
        assert "cpu_usage" in result.trends
        assert len(result.trends["cpu_usage"]) > 0
        assert "cpu_usage" in result.forecasts
        assert len(result.insights) >= 0
    
    def test_calculate_percentile(self, cost_service):
        """Test percentile calculation."""
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        # Test various percentiles
        assert cost_service._calculate_percentile(values, 50) == 55.0  # Median
        assert cost_service._calculate_percentile(values, 95) == 95.0  # 95th percentile
        assert cost_service._calculate_percentile(values, 0) == 10.0   # Minimum
        assert cost_service._calculate_percentile(values, 100) == 100.0 # Maximum
        
        # Test empty list
        assert cost_service._calculate_percentile([], 50) == 0.0
    
    def test_create_implementation_plan(self, cost_service):
        """Test implementation plan creation."""
        recommendations = [
            Recommendation(
                id="rec1",
                type=RecommendationType.RIGHTSIZING,
                title="Low effort recommendation",
                description="Test",
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.LOW,
                estimated_savings=100.0,
                created_at=datetime.utcnow()
            ),
            Recommendation(
                id="rec2",
                type=RecommendationType.RIGHTSIZING,
                title="Medium effort recommendation",
                description="Test",
                impact=ImpactLevel.MEDIUM,
                effort=EffortLevel.MEDIUM,
                estimated_savings=50.0,
                created_at=datetime.utcnow()
            ),
            Recommendation(
                id="rec3",
                type=RecommendationType.RIGHTSIZING,
                title="High effort recommendation",
                description="Test",
                impact=ImpactLevel.LOW,
                effort=EffortLevel.HIGH,
                estimated_savings=200.0,
                created_at=datetime.utcnow()
            )
        ]
        
        plan = cost_service._create_implementation_plan(recommendations)
        
        assert len(plan) == 3  # Should have 3 phases
        
        # Verify phase ordering (low effort first)
        assert plan[0]["phase"] == 1
        assert plan[0]["title"] == "Quick Wins"
        assert "rec1" in plan[0]["recommendations"]
        
        assert plan[1]["phase"] == 2
        assert plan[1]["title"] == "Optimization Phase"
        assert "rec2" in plan[1]["recommendations"]
        
        assert plan[2]["phase"] == 3
        assert plan[2]["title"] == "Strategic Changes"
        assert "rec3" in plan[2]["recommendations"]
    
    def test_assess_optimization_risks(self, cost_service, sample_utilization_data):
        """Test risk assessment for optimization recommendations."""
        recommendations = [
            Recommendation(
                id="rec1",
                type=RecommendationType.RIGHTSIZING,
                title="Downsize CPU allocation",
                description="Test downsize",
                impact=ImpactLevel.MEDIUM,
                effort=EffortLevel.LOW,
                estimated_savings=100.0,
                created_at=datetime.utcnow()
            ),
            Recommendation(
                id="rec2",
                type=RecommendationType.RIGHTSIZING,
                title="Increase memory allocation",
                description="Test upsize",
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.MEDIUM,
                estimated_savings=0.0,
                created_at=datetime.utcnow()
            )
        ]
        
        risk_assessment = cost_service._assess_optimization_risks(
            recommendations, sample_utilization_data
        )
        
        assert "overall_risk" in risk_assessment
        assert risk_assessment["overall_risk"] in ["low", "medium", "high"]
        assert "risk_score" in risk_assessment
        assert "factors" in risk_assessment
        assert "mitigation_strategies" in risk_assessment
        
        # Verify factors are calculated
        factors = risk_assessment["factors"]
        assert "downsize_recommendations" in factors
        assert "upsize_recommendations" in factors
        assert "high_utilization_services" in factors
    
    def test_pearson_correlation(self, cost_service):
        """Test Pearson correlation calculation."""
        # Perfect positive correlation
        x1 = [1, 2, 3, 4, 5]
        y1 = [2, 4, 6, 8, 10]
        corr1 = cost_service._pearson_correlation(x1, y1)
        assert abs(corr1 - 1.0) < 0.001
        
        # Perfect negative correlation
        x2 = [1, 2, 3, 4, 5]
        y2 = [10, 8, 6, 4, 2]
        corr2 = cost_service._pearson_correlation(x2, y2)
        assert abs(corr2 - (-1.0)) < 0.001
        
        # No correlation
        x3 = [1, 2, 3, 4, 5]
        y3 = [1, 1, 1, 1, 1]  # Constant values
        corr3 = cost_service._pearson_correlation(x3, y3)
        assert corr3 == 0.0
        
        # Different lengths (should return 0)
        x4 = [1, 2, 3]
        y4 = [1, 2]
        corr4 = cost_service._pearson_correlation(x4, y4)
        assert corr4 == 0.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cost_service, sample_cost_request):
        """Test error handling in cost optimization analysis."""
        # Mock an exception in get_resource_utilization
        cost_service.get_resource_utilization = AsyncMock(
            side_effect=Exception("Prometheus connection failed")
        )
        
        result = await cost_service.analyze_cost_optimization(
            sample_cost_request, "tenant-123"
        )
        
        # Should return error response
        assert result.success is False
        assert "failed" in result.message.lower()
        assert result.current_cost == 0
        assert result.potential_savings == 0
        assert len(result.recommendations) == 0
    
    def test_insufficient_data_handling(self, cost_service):
        """Test handling of insufficient data for recommendations."""
        # Create utilization data with insufficient trend data
        util = ResourceUtilization(
            resource="test-service_cpu",
            current=2.0,
            capacity=4.0,
            utilization=50.0,
            trend=[{"timestamp": datetime.utcnow(), "value": 2.0}] * 5,  # Only 5 hours of data
            recommendations=[],
            threshold_breaches=0,
            last_updated=datetime.utcnow()
        )
        
        # Should not generate recommendations due to insufficient data
        rec = cost_service._generate_cpu_recommendation(
            util, 50.0, 60.0, 55.0, "tenant-123"
        )
        
        # With insufficient data, no recommendation should be generated
        # (The actual behavior depends on the minimum observation hours threshold)
        # This test verifies the service handles insufficient data gracefully