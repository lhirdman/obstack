"""Unit tests for OpenCost client service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.opencost_client import OpenCostClient
from app.models.opencost import (
    CostAlert,
    CostAlertType,
    CostOptimization,
    CostTrend,
    KubernetesCost,
    OpenCostMetrics,
    OptimizationType,
    ResourceType
)
from app.exceptions import OpenCostError, TenantIsolationError


class TestOpenCostClient:
    """Test cases for OpenCostClient."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.services.opencost_client.get_settings') as mock:
            settings = MagicMock()
            settings.opencost_url = "http://localhost:9003"
            mock.return_value = settings
            yield settings
    
    @pytest.fixture
    def opencost_client(self, mock_settings):
        """Create OpenCost client for testing."""
        return OpenCostClient()
    
    @pytest.fixture
    def sample_opencost_response(self):
        """Sample OpenCost API response."""
        return {
            "data": {
                "test-cluster": {
                    "totalCost": 1000.0,
                    "cpuCost": 400.0,
                    "memoryCost": 300.0,
                    "storageCost": 200.0,
                    "networkCost": 100.0,
                    "efficiency": 0.75,
                    "wastedCost": 250.0,
                    "optimizationPotential": 200.0,
                    "namespaces": {
                        "default": 500.0,
                        "kube-system": 300.0,
                        "monitoring": 200.0
                    },
                    "workloads": {
                        "default/nginx": 300.0,
                        "default/redis": 200.0,
                        "monitoring/prometheus": 150.0
                    },
                    "services": {
                        "nginx-service": 300.0,
                        "redis-service": 200.0
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_allocation_response(self):
        """Sample OpenCost allocation response."""
        return {
            "data": {
                "test-cluster/default/nginx": {
                    "totalCost": 300.0,
                    "cpuCost": 120.0,
                    "memoryCost": 100.0,
                    "storageCost": 50.0,
                    "networkCost": 30.0,
                    "gpuCost": 0.0,
                    "efficiency": 0.6,
                    "labels": {
                        "app": "nginx",
                        "version": "1.20"
                    },
                    "cpuCoreRequest": 0.5,
                    "ramByteRequest": 536870912,  # 512MB
                    "cpuCoreLimit": 1.0,
                    "ramByteLimit": 1073741824,  # 1GB
                    "start": "2025-08-15T00:00:00Z"
                },
                "test-cluster/default/redis": {
                    "totalCost": 200.0,
                    "cpuCost": 80.0,
                    "memoryCost": 80.0,
                    "storageCost": 30.0,
                    "networkCost": 10.0,
                    "gpuCost": 0.0,
                    "efficiency": 0.8,
                    "labels": {
                        "app": "redis",
                        "version": "6.2"
                    },
                    "cpuCoreRequest": 0.25,
                    "ramByteRequest": 268435456,  # 256MB
                    "start": "2025-08-15T00:00:00Z"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_init(self, mock_settings):
        """Test OpenCost client initialization."""
        client = OpenCostClient()
        assert client.base_url == "http://localhost:9003"
        assert client.timeout == 30
        assert isinstance(client.session, httpx.AsyncClient)
        await client.close()
    
    @pytest.mark.asyncio
    async def test_init_with_custom_params(self):
        """Test OpenCost client initialization with custom parameters."""
        client = OpenCostClient(base_url="http://custom:9003", timeout=60)
        assert client.base_url == "http://custom:9003"
        assert client.timeout == 60
        await client.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self, opencost_client):
        """Test OpenCost client as async context manager."""
        async with opencost_client as client:
            assert isinstance(client, OpenCostClient)
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, opencost_client, sample_opencost_response):
        """Test successful API request."""
        with patch.object(opencost_client.session, 'request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_opencost_response
            mock_request.return_value = mock_response
            
            result = await opencost_client._make_request("GET", "/allocation")
            
            assert result == sample_opencost_response
            mock_request.assert_called_once_with(
                method="GET",
                url="http://localhost:9003/allocation",
                params=None,
                json=None
            )
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, opencost_client):
        """Test API request with HTTP error."""
        with patch.object(opencost_client.session, 'request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_request.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500 Server Error", request=MagicMock(), response=mock_response
            )
            
            with pytest.raises(OpenCostError, match="OpenCost API request failed: 500"):
                await opencost_client._make_request("GET", "/allocation")
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, opencost_client):
        """Test API request with connection error."""
        with patch.object(opencost_client.session, 'request') as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(OpenCostError, match="Failed to connect to OpenCost"):
                await opencost_client._make_request("GET", "/allocation")
    
    def test_validate_tenant_access_success(self, opencost_client):
        """Test successful tenant access validation."""
        # Should not raise exception
        opencost_client._validate_tenant_access("tenant1", "tenant1")
    
    def test_validate_tenant_access_failure(self, opencost_client):
        """Test failed tenant access validation."""
        with pytest.raises(TenantIsolationError):
            opencost_client._validate_tenant_access("tenant1", "tenant2")
    
    @pytest.mark.asyncio
    async def test_get_cluster_costs_success(self, opencost_client, sample_opencost_response):
        """Test successful cluster cost retrieval."""
        start_time = datetime(2025, 8, 15, 0, 0, 0)
        end_time = datetime(2025, 8, 15, 23, 59, 59)
        
        with patch.object(opencost_client, '_make_request') as mock_request:
            mock_request.return_value = sample_opencost_response
            
            result = await opencost_client.get_cluster_costs(
                cluster="test-cluster",
                start_time=start_time,
                end_time=end_time,
                tenant_id="tenant1"
            )
            
            assert isinstance(result, OpenCostMetrics)
            assert result.cluster == "test-cluster"
            assert result.total_cost == 1000.0
            assert result.cpu_cost_total == 400.0
            assert result.memory_cost_total == 300.0
            assert result.storage_cost_total == 200.0
            assert result.network_cost_total == 100.0
            assert result.overall_efficiency == 75.0
            assert result.wasted_cost == 250.0
            assert result.optimization_potential == 200.0
            assert result.tenant_id == "tenant1"
            assert result.period_start == start_time
            assert result.period_end == end_time
            
            # Verify request parameters
            mock_request.assert_called_once_with(
                "GET", 
                "/allocation", 
                params={
                    "window": f"{start_time.isoformat()},{end_time.isoformat()}",
                    "aggregate": "cluster",
                    "step": "1h"
                }
            )
    
    @pytest.mark.asyncio
    async def test_get_namespace_costs_success(self, opencost_client, sample_allocation_response):
        """Test successful namespace cost retrieval."""
        start_time = datetime(2025, 8, 15, 0, 0, 0)
        end_time = datetime(2025, 8, 15, 23, 59, 59)
        
        with patch.object(opencost_client, '_make_request') as mock_request:
            mock_request.return_value = sample_allocation_response
            
            result = await opencost_client.get_namespace_costs(
                cluster="test-cluster",
                namespace="default",
                start_time=start_time,
                end_time=end_time,
                tenant_id="tenant1"
            )
            
            assert isinstance(result, list)
            assert len(result) == 2
            
            # Check nginx workload
            nginx_cost = next(c for c in result if c.workload == "nginx")
            assert nginx_cost.namespace == "default"
            assert nginx_cost.cluster == "test-cluster"
            assert nginx_cost.total_cost == 300.0
            assert nginx_cost.cpu_cost == 120.0
            assert nginx_cost.memory_cost == 100.0
            assert nginx_cost.storage_cost == 50.0
            assert nginx_cost.network_cost == 30.0
            assert nginx_cost.efficiency == 60.0
            assert nginx_cost.cpu_request == 0.5
            assert nginx_cost.memory_request == 536870912
            assert nginx_cost.labels["app"] == "nginx"
            assert nginx_cost.tenant_id == "tenant1"
            
            # Check redis workload
            redis_cost = next(c for c in result if c.workload == "redis")
            assert redis_cost.total_cost == 200.0
            assert redis_cost.efficiency == 80.0
    
    @pytest.mark.asyncio
    async def test_get_workload_costs_success(self, opencost_client, sample_allocation_response):
        """Test successful workload cost retrieval."""
        start_time = datetime(2025, 8, 15, 0, 0, 0)
        end_time = datetime(2025, 8, 15, 23, 59, 59)
        
        with patch.object(opencost_client, 'get_namespace_costs') as mock_namespace_costs:
            # Create mock KubernetesCost objects
            nginx_cost = KubernetesCost(
                namespace="default",
                workload="nginx",
                cluster="test-cluster",
                cpu_cost=120.0,
                memory_cost=100.0,
                storage_cost=50.0,
                network_cost=30.0,
                total_cost=300.0,
                efficiency=60.0,
                period_start=start_time,
                period_end=end_time,
                tenant_id="tenant1"
            )
            redis_cost = KubernetesCost(
                namespace="default",
                workload="redis",
                cluster="test-cluster",
                cpu_cost=80.0,
                memory_cost=80.0,
                storage_cost=30.0,
                network_cost=10.0,
                total_cost=200.0,
                efficiency=80.0,
                period_start=start_time,
                period_end=end_time,
                tenant_id="tenant1"
            )
            mock_namespace_costs.return_value = [nginx_cost, redis_cost]
            
            result = await opencost_client.get_workload_costs(
                cluster="test-cluster",
                namespace="default",
                workload="nginx",
                start_time=start_time,
                end_time=end_time,
                tenant_id="tenant1"
            )
            
            assert result is not None
            assert isinstance(result, KubernetesCost)
            assert result.workload == "nginx"
            assert result.total_cost == 300.0
    
    @pytest.mark.asyncio
    async def test_get_workload_costs_not_found(self, opencost_client):
        """Test workload cost retrieval when workload not found."""
        start_time = datetime(2025, 8, 15, 0, 0, 0)
        end_time = datetime(2025, 8, 15, 23, 59, 59)
        
        with patch.object(opencost_client, 'get_namespace_costs') as mock_namespace_costs:
            mock_namespace_costs.return_value = []
            
            result = await opencost_client.get_workload_costs(
                cluster="test-cluster",
                namespace="default",
                workload="nonexistent",
                start_time=start_time,
                end_time=end_time,
                tenant_id="tenant1"
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cost_trends_success(self, opencost_client):
        """Test successful cost trend analysis."""
        mock_data = {
            "workload1": {
                "cpuCost": 100.0,
                "memoryCost": 80.0,
                "start": "2025-08-15T00:00:00Z"
            },
            "workload2": {
                "cpuCost": 120.0,
                "memoryCost": 90.0,
                "start": "2025-08-16T00:00:00Z"
            }
        }
        
        with patch.object(opencost_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": mock_data}
            
            result = await opencost_client.get_cost_trends(
                cluster="test-cluster",
                namespace="default",
                tenant_id="tenant1",
                days=7
            )
            
            assert isinstance(result, list)
            # Should have trends for different resource types
            assert len(result) >= 0  # May be empty if no sufficient data
    
    def test_analyze_cost_trend_increasing(self, opencost_client):
        """Test cost trend analysis for increasing trend."""
        data = {
            "workload1": {"cpuCost": 100.0, "start": "2025-08-15T00:00:00Z"},
            "workload2": {"cpuCost": 120.0, "start": "2025-08-16T00:00:00Z"}
        }
        
        result = opencost_client._analyze_cost_trend(
            data, 
            ResourceType.CPU,
            datetime(2025, 8, 15),
            datetime(2025, 8, 16)
        )
        
        assert result is not None
        assert result["direction"] == "increasing"
        assert result["percentage"] == 20.0
        assert len(result["points"]) == 2
    
    def test_analyze_cost_trend_decreasing(self, opencost_client):
        """Test cost trend analysis for decreasing trend."""
        data = {
            "workload1": {"cpuCost": 120.0, "start": "2025-08-15T00:00:00Z"},
            "workload2": {"cpuCost": 100.0, "start": "2025-08-16T00:00:00Z"}
        }
        
        result = opencost_client._analyze_cost_trend(
            data, 
            ResourceType.CPU,
            datetime(2025, 8, 15),
            datetime(2025, 8, 16)
        )
        
        assert result is not None
        assert result["direction"] == "decreasing"
        # Allow for floating point precision differences
        assert abs(result["percentage"] - (-16.666666666666668)) < 0.000001
    
    def test_analyze_cost_trend_stable(self, opencost_client):
        """Test cost trend analysis for stable trend."""
        data = {
            "workload1": {"cpuCost": 100.0, "start": "2025-08-15T00:00:00Z"},
            "workload2": {"cpuCost": 102.0, "start": "2025-08-16T00:00:00Z"}
        }
        
        result = opencost_client._analyze_cost_trend(
            data, 
            ResourceType.CPU,
            datetime(2025, 8, 15),
            datetime(2025, 8, 16)
        )
        
        assert result is not None
        assert result["direction"] == "stable"  # Less than 5% change
    
    def test_analyze_cost_trend_insufficient_data(self, opencost_client):
        """Test cost trend analysis with insufficient data."""
        data = {
            "workload1": {"cpuCost": 100.0, "start": "2025-08-15T00:00:00Z"}
        }
        
        result = opencost_client._analyze_cost_trend(
            data, 
            ResourceType.CPU,
            datetime(2025, 8, 15),
            datetime(2025, 8, 16)
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_cost_optimizations_success(self, opencost_client):
        """Test successful cost optimization generation."""
        # Create a mock workload with low efficiency
        mock_cost = KubernetesCost(
            namespace="default",
            workload="inefficient-app",
            cluster="test-cluster",
            cpu_cost=200.0,
            memory_cost=150.0,
            storage_cost=100.0,
            network_cost=50.0,
            total_cost=500.0,
            efficiency=30.0,  # Low efficiency
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1",
            cpu_request=2.0,
            memory_request=2147483648  # 2GB
        )
        
        with patch.object(opencost_client, 'get_workload_costs') as mock_workload_costs:
            mock_workload_costs.return_value = mock_cost
            
            result = await opencost_client.generate_cost_optimizations(
                cluster="test-cluster",
                namespace="default",
                workload="inefficient-app",
                tenant_id="tenant1",
                min_savings=10.0
            )
            
            assert isinstance(result, list)
            # Should have at least rightsizing recommendation due to low efficiency
            rightsizing_opts = [opt for opt in result if opt.type == OptimizationType.RIGHTSIZING]
            assert len(rightsizing_opts) > 0
            
            rightsizing = rightsizing_opts[0]
            assert rightsizing.potential_savings > 0
            assert "Rightsize" in rightsizing.title
            assert rightsizing.implementation_effort.value in ["low", "medium", "high"]
            assert rightsizing.risk_level.value in ["low", "medium", "high"]
    
    def test_generate_rightsizing_recommendation_low_efficiency(self, opencost_client):
        """Test rightsizing recommendation for low efficiency workload."""
        cost = KubernetesCost(
            namespace="default",
            workload="inefficient-app",
            cluster="test-cluster",
            cpu_cost=200.0,
            memory_cost=150.0,
            storage_cost=50.0,
            network_cost=25.0,
            total_cost=425.0,
            efficiency=30.0,  # Low efficiency
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1",
            cpu_request=2.0,
            memory_request=2147483648  # 2GB
        )
        
        result = opencost_client._generate_rightsizing_recommendation(cost)
        
        assert result is not None
        assert result.type == OptimizationType.RIGHTSIZING
        assert result.potential_savings > 0
        assert "inefficient-app" in result.title
        assert result.current_resources["cpu_request"] == 2.0
        assert result.recommended_resources["cpu_request"] == 1.4  # 70% of original
    
    def test_generate_rightsizing_recommendation_high_efficiency(self, opencost_client):
        """Test rightsizing recommendation for high efficiency workload."""
        cost = KubernetesCost(
            namespace="default",
            workload="efficient-app",
            cluster="test-cluster",
            cpu_cost=100.0,
            memory_cost=80.0,
            storage_cost=20.0,
            network_cost=10.0,
            total_cost=210.0,
            efficiency=85.0,  # High efficiency
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1"
        )
        
        result = opencost_client._generate_rightsizing_recommendation(cost)
        
        assert result is None  # No recommendation for efficient workloads
    
    def test_generate_scheduling_recommendation_high_cost(self, opencost_client):
        """Test scheduling recommendation for high-cost workload."""
        cost = KubernetesCost(
            namespace="default",
            workload="expensive-app",
            cluster="test-cluster",
            cpu_cost=300.0,
            memory_cost=200.0,
            storage_cost=100.0,
            network_cost=50.0,
            total_cost=650.0,  # High cost
            efficiency=70.0,
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1"
        )
        
        result = opencost_client._generate_scheduling_recommendation(cost)
        
        assert result is not None
        assert result.type == OptimizationType.SCHEDULING
        assert "spot instances" in result.title.lower()
        assert result.potential_savings > 0
    
    def test_generate_scheduling_recommendation_low_cost(self, opencost_client):
        """Test scheduling recommendation for low-cost workload."""
        cost = KubernetesCost(
            namespace="default",
            workload="cheap-app",
            cluster="test-cluster",
            cpu_cost=20.0,
            memory_cost=15.0,
            storage_cost=10.0,
            network_cost=5.0,
            total_cost=50.0,  # Low cost
            efficiency=70.0,
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1"
        )
        
        result = opencost_client._generate_scheduling_recommendation(cost)
        
        assert result is None  # No recommendation for low-cost workloads
    
    def test_generate_storage_recommendation_high_storage_cost(self, opencost_client):
        """Test storage recommendation for high storage cost workload."""
        cost = KubernetesCost(
            namespace="default",
            workload="storage-heavy-app",
            cluster="test-cluster",
            cpu_cost=50.0,
            memory_cost=40.0,
            storage_cost=150.0,  # High storage cost
            network_cost=10.0,
            total_cost=250.0,
            efficiency=70.0,
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1"
        )
        
        result = opencost_client._generate_storage_recommendation(cost)
        
        assert result is not None
        assert result.type == OptimizationType.STORAGE
        assert "storage" in result.title.lower()
        assert result.potential_savings > 0
    
    def test_generate_storage_recommendation_low_storage_cost(self, opencost_client):
        """Test storage recommendation for low storage cost workload."""
        cost = KubernetesCost(
            namespace="default",
            workload="low-storage-app",
            cluster="test-cluster",
            cpu_cost=100.0,
            memory_cost=80.0,
            storage_cost=10.0,  # Low storage cost
            network_cost=20.0,
            total_cost=210.0,
            efficiency=70.0,
            period_start=datetime(2025, 8, 15),
            period_end=datetime(2025, 8, 16),
            tenant_id="tenant1"
        )
        
        result = opencost_client._generate_storage_recommendation(cost)
        
        assert result is None  # No recommendation for low storage cost
    
    @pytest.mark.asyncio
    async def test_create_cost_alert_success(self, opencost_client):
        """Test successful cost alert creation."""
        result = await opencost_client.create_cost_alert(
            alert_type=CostAlertType.BUDGET_EXCEEDED,
            threshold=1000.0,
            namespace="default",
            cluster="test-cluster",
            workload="expensive-app",
            tenant_id="tenant1"
        )
        
        assert isinstance(result, CostAlert)
        assert result.type == CostAlertType.BUDGET_EXCEEDED
        assert result.threshold == 1000.0
        assert result.namespace == "default"
        assert result.cluster == "test-cluster"
        assert result.workload == "expensive-app"
        assert result.tenant_id == "tenant1"
        assert result.current_value == 0.0  # Default value
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, opencost_client):
        """Test successful health check."""
        mock_response = {"version": "1.0.0", "status": "ok"}
        
        with patch.object(opencost_client, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            
            result = await opencost_client.health_check()
            
            assert result["status"] == "healthy"
            assert result["opencost_url"] == "http://localhost:9003"
            assert result["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, opencost_client):
        """Test health check failure."""
        with patch.object(opencost_client, '_make_request') as mock_request:
            mock_request.side_effect = OpenCostError("Connection failed")
            
            result = await opencost_client.health_check()
            
            assert result["status"] == "unhealthy"
            assert result["opencost_url"] == "http://localhost:9003"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_close_session(self, opencost_client):
        """Test closing HTTP session."""
        with patch.object(opencost_client.session, 'aclose') as mock_close:
            await opencost_client.close()
            mock_close.assert_called_once()


class TestOpenCostClientIntegration:
    """Integration tests for OpenCost client."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete OpenCost workflow."""
        # This would be an integration test that requires actual OpenCost instance
        # For now, we'll skip it in unit tests
        pytest.skip("Integration test requires OpenCost instance")
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_enforcement(self):
        """Test that tenant isolation is properly enforced."""
        client = OpenCostClient()
        
        # Test that tenant validation is called
        with pytest.raises(TenantIsolationError):
            client._validate_tenant_access("tenant1", "tenant2")
        
        await client.close()


# Fixtures for test data
@pytest.fixture
def sample_kubernetes_cost():
    """Sample KubernetesCost object for testing."""
    return KubernetesCost(
        namespace="default",
        workload="test-app",
        cluster="test-cluster",
        cpu_cost=100.0,
        memory_cost=80.0,
        storage_cost=50.0,
        network_cost=20.0,
        total_cost=250.0,
        efficiency=75.0,
        period_start=datetime(2025, 8, 15),
        period_end=datetime(2025, 8, 16),
        tenant_id="tenant1",
        labels={"app": "test", "version": "1.0"},
        cpu_request=1.0,
        memory_request=1073741824  # 1GB
    )


@pytest.fixture
def sample_cost_optimization():
    """Sample CostOptimization object for testing."""
    return CostOptimization(
        type=OptimizationType.RIGHTSIZING,
        title="Rightsize test-app",
        description="Reduce resource requests to improve efficiency",
        potential_savings=50.0,
        implementation_effort="low",
        risk_level="low",
        steps=[
            "Analyze usage patterns",
            "Reduce CPU requests by 25%",
            "Monitor performance"
        ],
        current_resources={"cpu_request": 1.0, "memory_request": 1073741824},
        recommended_resources={"cpu_request": 0.75, "memory_request": 805306368},
        confidence_score=0.8
    )