"""Integration tests for cost monitoring API endpoints."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.opencost import (
    CostQueryRequest, KubernetesCost, CostAlert, CostOptimization,
    CostTrend, OpenCostMetrics, CostAlertType, OptimizationType,
    ResourceType, ImplementationEffort, RiskLevel
)
from app.auth.models import UserContext


class TestCostAPI:
    """Test suite for cost monitoring API endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return UserContext(
            user_id="test-user-id",
            tenant_id="test-tenant",
            roles=["user"],
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    
    @pytest.fixture
    def mock_opencost_client(self):
        """Mock OpenCost client."""
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def sample_kubernetes_cost(self):
        """Sample Kubernetes cost data."""
        return KubernetesCost(
            namespace="default",
            workload="test-deployment",
            cluster="test-cluster",
            cpu_cost=50.0,
            memory_cost=30.0,
            storage_cost=20.0,
            network_cost=10.0,
            total_cost=110.0,
            efficiency=75.0,
            period_start=datetime.utcnow() - timedelta(hours=24),
            period_end=datetime.utcnow(),
            tenant_id="test-tenant",
            labels={"app": "test-app"},
            cpu_request=2.0,
            memory_request=4096000000,  # 4GB in bytes
            cpu_limit=4.0,
            memory_limit=8192000000   # 8GB in bytes
        )
    
    @pytest.fixture
    def sample_cost_optimization(self):
        """Sample cost optimization recommendation."""
        return CostOptimization(
            type=OptimizationType.RIGHTSIZING,
            title="Rightsize test-deployment",
            description="Reduce CPU and memory requests to improve efficiency",
            potential_savings=25.0,
            implementation_effort=ImplementationEffort.LOW,
            risk_level=RiskLevel.LOW,
            steps=[
                "Analyze current usage patterns",
                "Reduce CPU request from 2 to 1.5 cores",
                "Reduce memory request from 4GB to 3GB",
                "Monitor performance after changes"
            ],
            current_resources={"cpu_request": 2.0, "memory_request": 4.0},
            recommended_resources={"cpu_request": 1.5, "memory_request": 3.0},
            confidence_score=0.85
        )
    
    @pytest.fixture
    def sample_cluster_metrics(self):
        """Sample cluster cost metrics."""
        return OpenCostMetrics(
            cluster="test-cluster",
            total_cost=500.0,
            cost_by_namespace={"default": 200.0, "kube-system": 150.0, "monitoring": 150.0},
            cost_by_workload={"deployment/app1": 100.0, "deployment/app2": 100.0},
            cost_by_service={"service1": 80.0, "service2": 70.0},
            cpu_cost_total=250.0,
            memory_cost_total=150.0,
            storage_cost_total=75.0,
            network_cost_total=25.0,
            overall_efficiency=68.0,
            wasted_cost=160.0,
            optimization_potential=120.0,
            period_start=datetime.utcnow() - timedelta(hours=24),
            period_end=datetime.utcnow(),
            tenant_id="test-tenant"
        )
    
    @pytest.mark.asyncio
    async def test_query_costs_cluster_level(self, mock_user, mock_opencost_client, sample_cluster_metrics):
        """Test querying cluster-level costs."""
        # Setup mock
        mock_opencost_client.get_cluster_costs.return_value = sample_cluster_metrics
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "1h",
                        "include_recommendations": True
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_cost"] == 500.0
        assert "cpu" in data["cost_breakdown"]
        assert data["cost_breakdown"]["cpu"] == 250.0
        assert data["query_metadata"]["cluster"] == "test-cluster"
        assert data["query_metadata"]["tenant_id"] == "test-tenant"
        
        # Verify OpenCost client was called correctly
        mock_opencost_client.get_cluster_costs.assert_called_once()
        call_args = mock_opencost_client.get_cluster_costs.call_args
        assert call_args[1]["cluster"] == "test-cluster"
        assert call_args[1]["tenant_id"] == "test-tenant"
    
    @pytest.mark.asyncio
    async def test_query_costs_namespace_level(self, mock_user, mock_opencost_client, sample_kubernetes_cost):
        """Test querying namespace-level costs."""
        # Setup mock
        mock_opencost_client.get_namespace_costs.return_value = [sample_kubernetes_cost]
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "namespace": "default",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "1h",
                        "include_recommendations": False
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_cost"] == 110.0
        assert len(data["costs"]) == 1
        assert data["costs"][0]["workload"] == "test-deployment"
        assert "test-deployment" in data["cost_breakdown"]
        
        # Verify OpenCost client was called correctly
        mock_opencost_client.get_namespace_costs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_costs_workload_level(self, mock_user, mock_opencost_client, sample_kubernetes_cost):
        """Test querying workload-level costs."""
        # Setup mock
        mock_opencost_client.get_workload_costs.return_value = sample_kubernetes_cost
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "namespace": "default",
                        "workload": "test-deployment",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "1h",
                        "include_recommendations": True
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_cost"] == 110.0
        assert len(data["costs"]) == 1
        assert data["costs"][0]["namespace"] == "default"
        assert data["costs"][0]["workload"] == "test-deployment"
        
        # Verify OpenCost client was called correctly
        mock_opencost_client.get_workload_costs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_costs_missing_cluster(self, mock_user, mock_opencost_client):
        """Test querying costs without cluster name fails."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "1h"
                    }
                )
        
        assert response.status_code == 400
        assert "Cluster name is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_namespace_costs(self, mock_user, mock_opencost_client, sample_kubernetes_cost):
        """Test getting namespace costs endpoint."""
        # Setup mock
        mock_opencost_client.get_namespace_costs.return_value = [sample_kubernetes_cost]
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/costs/clusters/test-cluster/namespaces/default/costs",
                    params={
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "1h"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["namespace"] == "default"
        assert data[0]["workload"] == "test-deployment"
        assert data[0]["total_cost"] == 110.0
    
    @pytest.mark.asyncio
    async def test_get_cluster_metrics(self, mock_user, mock_opencost_client, sample_cluster_metrics):
        """Test getting cluster metrics endpoint."""
        # Setup mock
        mock_opencost_client.get_cluster_costs.return_value = sample_cluster_metrics
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/costs/clusters/test-cluster/metrics",
                    params={
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "1h"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cluster"] == "test-cluster"
        assert data["total_cost"] == 500.0
        assert data["overall_efficiency"] == 68.0
        assert "default" in data["cost_by_namespace"]
        assert data["cost_by_namespace"]["default"] == 200.0
    
    @pytest.mark.asyncio
    async def test_get_cost_trends(self, mock_user, mock_opencost_client):
        """Test getting cost trends endpoint."""
        # Setup mock trend data
        sample_trend = CostTrend(
            resource_type=ResourceType.CPU,
            namespace="default",
            workload="test-deployment",
            data_points=[
                {"timestamp": "2025-08-14T00:00:00Z", "cost": 45.0},
                {"timestamp": "2025-08-14T12:00:00Z", "cost": 50.0},
                {"timestamp": "2025-08-15T00:00:00Z", "cost": 55.0}
            ],
            trend_direction="increasing",
            trend_percentage=22.2,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            tenant_id="test-tenant"
        )
        mock_opencost_client.get_cost_trends.return_value = [sample_trend]
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/costs/trends",
                    params={
                        "cluster": "test-cluster",
                        "namespace": "default",
                        "workload": "test-deployment",
                        "days": 7
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["resource_type"] == "cpu"
        assert data[0]["trend_direction"] == "increasing"
        assert data[0]["trend_percentage"] == 22.2
        assert len(data[0]["data_points"]) == 3
    
    @pytest.mark.asyncio
    async def test_analyze_cost_optimization(self, mock_user, mock_opencost_client, sample_cost_optimization):
        """Test cost optimization analysis endpoint."""
        # Setup mock
        mock_opencost_client.generate_cost_optimizations.return_value = [sample_cost_optimization]
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/optimization",
                    json={
                        "cluster": "test-cluster",
                        "namespace": "default",
                        "workload": "test-deployment",
                        "optimization_types": ["rightsizing"],
                        "time_range_days": 7,
                        "min_savings_threshold": 10.0
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_potential_savings"] == 25.0
        assert len(data["optimizations"]) == 1
        assert data["optimizations"][0]["type"] == "rightsizing"
        assert data["optimizations"][0]["potential_savings"] == 25.0
        assert len(data["implementation_priority"]) == 1
        assert "rightsizing: $25.00 savings" in data["implementation_priority"][0]
    
    @pytest.mark.asyncio
    async def test_create_cost_alert(self, mock_user, mock_opencost_client):
        """Test creating cost alert endpoint."""
        # Setup mock alert
        sample_alert = CostAlert(
            id="test-alert-id",
            type=CostAlertType.BUDGET_EXCEEDED,
            severity="medium",
            title="Budget Exceeded Alert",
            description="Namespace budget exceeded threshold",
            threshold=100.0,
            current_value=0.0,
            namespace="default",
            cluster="test-cluster",
            tenant_id="test-tenant",
            recommendations=["Review resource usage", "Consider optimization"]
        )
        mock_opencost_client.create_cost_alert.return_value = sample_alert
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/alerts",
                    json={
                        "type": "budget_exceeded",
                        "threshold": 100.0,
                        "namespace": "default",
                        "cluster": "test-cluster",
                        "notification_channels": ["email", "slack"]
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["created"] is True
        assert data["alert"]["type"] == "budget_exceeded"
        assert data["alert"]["threshold"] == 100.0
        assert data["alert"]["namespace"] == "default"
    
    @pytest.mark.asyncio
    async def test_get_cost_alerts(self, mock_user):
        """Test getting cost alerts endpoint."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/costs/alerts",
                    params={
                        "cluster": "test-cluster",
                        "namespace": "default",
                        "alert_type": "budget_exceeded",
                        "active_only": True
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Currently returns empty list as alerts would be stored in database
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_resolve_cost_alert(self, mock_user):
        """Test resolving cost alert endpoint."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put("/api/v1/costs/alerts/test-alert-id/resolve")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Alert test-alert-id resolved" in data["message"]
    
    @pytest.mark.asyncio
    async def test_generate_cost_report_chargeback(self, mock_user, mock_opencost_client, sample_cluster_metrics):
        """Test generating chargeback cost report."""
        # Setup mock
        mock_opencost_client.get_cluster_costs.return_value = sample_cluster_metrics
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/reports",
                    json={
                        "report_type": "chargeback",
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "group_by": ["namespace"],
                        "include_forecasts": False
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_data"]["type"] == "chargeback"
        assert data["report_data"]["total_cost"] == 500.0
        assert "default" in data["report_data"]["cost_by_namespace"]
        assert data["summary"]["total_cost"] == 500.0
        assert len(data["charts"]) == 2
        assert "pdf" in data["export_urls"]
        assert "csv" in data["export_urls"]
    
    @pytest.mark.asyncio
    async def test_generate_cost_report_showback(self, mock_user, mock_opencost_client, sample_cluster_metrics):
        """Test generating showback cost report."""
        # Setup mock
        mock_opencost_client.get_cluster_costs.return_value = sample_cluster_metrics
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/reports",
                    json={
                        "report_type": "showback",
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "group_by": ["namespace"]
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_data"]["type"] == "showback"
        assert "usage_metrics" in data["report_data"]
        assert "efficiency_metrics" in data["report_data"]
        assert data["summary"]["efficiency_score"] == 68.0
    
    @pytest.mark.asyncio
    async def test_generate_cost_report_allocation(self, mock_user, mock_opencost_client, sample_cluster_metrics):
        """Test generating allocation cost report."""
        # Setup mock
        mock_opencost_client.get_cluster_costs.return_value = sample_cluster_metrics
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/reports",
                    json={
                        "report_type": "allocation",
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_data"]["type"] == "allocation"
        assert "allocations" in data["report_data"]
        assert data["summary"]["allocated_cost"] == 500.0  # Sum of namespace costs
        assert data["summary"]["allocation_percentage"] == 100.0
    
    @pytest.mark.asyncio
    async def test_cost_service_health(self, mock_opencost_client):
        """Test cost service health endpoint."""
        # Setup mock health response
        mock_opencost_client.health_check.return_value = {
            "status": "healthy",
            "opencost_url": "http://localhost:9003",
            "response_time_ms": 50,
            "version": "1.0.0"
        }
        
        with patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/costs/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["opencost_url"] == "http://localhost:9003"
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_cost_service_health_unhealthy(self, mock_opencost_client):
        """Test cost service health endpoint when service is unhealthy."""
        # Setup mock to raise exception
        mock_opencost_client.health_check.side_effect = Exception("Connection failed")
        
        with patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/costs/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
        assert "Connection failed" in data["error"]
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_error(self, mock_user, mock_opencost_client):
        """Test that tenant isolation errors are handled properly."""
        from app.exceptions import TenantIsolationError
        
        # Setup mock to raise tenant isolation error
        mock_opencost_client.get_cluster_costs.side_effect = TenantIsolationError(
            "Tenant test-tenant cannot access resources for tenant other-tenant"
        )
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z"
                    }
                )
        
        assert response.status_code == 403
        assert "cannot access resources" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_opencost_error_handling(self, mock_user, mock_opencost_client):
        """Test that OpenCost errors are handled properly."""
        from app.exceptions import OpenCostError
        
        # Setup mock to raise OpenCost error
        mock_opencost_client.get_cluster_costs.side_effect = OpenCostError("OpenCost API unavailable")
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z"
                    }
                )
        
        assert response.status_code == 500
        assert "OpenCost error" in response.json()["detail"]
        assert "OpenCost API unavailable" in response.json()["detail"]


class TestCostAPIStreaming:
    """Test suite for cost API streaming endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return UserContext(
            user_id="test-user-id",
            tenant_id="test-tenant",
            roles=["user"],
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    
    @pytest.fixture
    def mock_opencost_client(self):
        """Mock OpenCost client."""
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def sample_cluster_metrics(self):
        """Sample cluster cost metrics."""
        return OpenCostMetrics(
            cluster="test-cluster",
            total_cost=500.0,
            cost_by_namespace={"default": 200.0, "kube-system": 150.0},
            cost_by_workload={"deployment/app1": 100.0, "deployment/app2": 100.0},
            cost_by_service={"service1": 80.0, "service2": 70.0},
            cpu_cost_total=250.0,
            memory_cost_total=150.0,
            storage_cost_total=75.0,
            network_cost_total=25.0,
            overall_efficiency=68.0,
            wasted_cost=160.0,
            optimization_potential=120.0,
            period_start=datetime.utcnow() - timedelta(hours=24),
            period_end=datetime.utcnow(),
            tenant_id="test-tenant"
        )
    
    @pytest.mark.asyncio
    async def test_stream_cost_allocation(self, mock_user, mock_opencost_client, sample_cluster_metrics):
        """Test streaming cost allocation endpoint."""
        # Setup mock
        mock_opencost_client.get_cluster_costs.return_value = sample_cluster_metrics
        
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user), \
             patch('app.api.v1.costs.get_opencost_client', return_value=mock_opencost_client):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/costs/allocation/stream",
                    params={
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z"
                    }
                )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Read the streaming response
        content = response.content.decode()
        lines = content.strip().split('\n')
        
        # Check for expected SSE events
        status_events = [line for line in lines if 'status' in line]
        allocation_events = [line for line in lines if 'allocation' in line]
        complete_events = [line for line in lines if 'complete' in line]
        
        assert len(status_events) > 0
        assert len(allocation_events) > 0
        assert len(complete_events) > 0
        
        # Verify OpenCost client was called
        mock_opencost_client.get_cluster_costs.assert_called_once()


class TestCostAPIValidation:
    """Test suite for cost API input validation."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return UserContext(
            user_id="test-user-id",
            tenant_id="test-tenant",
            roles=["user"],
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    
    @pytest.mark.asyncio
    async def test_invalid_date_range(self, mock_user):
        """Test validation of invalid date ranges."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "start_time": "2025-08-15T00:00:00Z",  # End before start
                        "end_time": "2025-08-14T00:00:00Z",
                        "aggregation": "1h"
                    }
                )
        
        # FastAPI/Pydantic should handle this validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_invalid_aggregation(self, mock_user):
        """Test validation of invalid aggregation values."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/query",
                    json={
                        "cluster": "test-cluster",
                        "start_time": "2025-08-14T00:00:00Z",
                        "end_time": "2025-08-15T00:00:00Z",
                        "aggregation": "invalid"  # Invalid aggregation format
                    }
                )
        
        # Should fail validation due to regex pattern
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_negative_threshold_alert(self, mock_user):
        """Test validation of negative threshold values."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/alerts",
                    json={
                        "type": "budget_exceeded",
                        "threshold": -100.0,  # Negative threshold
                        "namespace": "default",
                        "cluster": "test-cluster"
                    }
                )
        
        # Should fail validation due to gt=0 constraint
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_optimization_request(self, mock_user):
        """Test validation of invalid optimization request."""
        with patch('app.api.v1.costs.get_current_user', return_value=mock_user):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/costs/optimization",
                    json={
                        "cluster": "test-cluster",
                        "time_range_days": 0,  # Invalid: should be >= 1
                        "min_savings_threshold": -10.0  # Invalid: should be >= 0
                    }
                )
        
        # Should fail validation
        assert response.status_code == 422