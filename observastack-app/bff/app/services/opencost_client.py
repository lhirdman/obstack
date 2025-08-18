"""OpenCost client service for Kubernetes cost monitoring integration."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from ..models.opencost import (
    CostAllocation,
    CostAlert,
    CostAlertType,
    CostOptimization,
    CostTrend,
    KubernetesCost,
    OpenCostMetrics,
    OptimizationType,
    ResourceType,
    ImplementationEffort,
    RiskLevel
)
from ..core.config import get_settings
from ..exceptions import OpenCostError, TenantIsolationError

logger = logging.getLogger(__name__)

class OpenCostClient:
    """Client for interacting with OpenCost API for Kubernetes cost monitoring."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """Initialize OpenCost client.
        
        Args:
            base_url: OpenCost API base URL (defaults to settings)
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        self.base_url = base_url or settings.opencost_url
        self.timeout = timeout
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"Content-Type": "application/json"}
        )
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.session.aclose()
        
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to OpenCost API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            OpenCostError: If request fails or returns error
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = await self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenCost API error: {e.response.status_code} - {e.response.text}")
            raise OpenCostError(f"OpenCost API request failed: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"OpenCost request error: {e}")
            raise OpenCostError(f"Failed to connect to OpenCost: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenCost request: {e}")
            raise OpenCostError(f"Unexpected error: {e}")
            
    def _validate_tenant_access(self, tenant_id: str, resource_tenant_id: str):
        """Validate tenant has access to resource.
        
        Args:
            tenant_id: Requesting tenant ID
            resource_tenant_id: Resource tenant ID
            
        Raises:
            TenantIsolationError: If tenant doesn't have access
        """
        if tenant_id != resource_tenant_id:
            raise TenantIsolationError(
                f"Tenant {tenant_id} cannot access resources for tenant {resource_tenant_id}"
            )
            
    async def get_cluster_costs(
        self, 
        cluster: str,
        start_time: datetime,
        end_time: datetime,
        tenant_id: str,
        aggregation: str = "1h"
    ) -> OpenCostMetrics:
        """Get cost metrics for a Kubernetes cluster.
        
        Args:
            cluster: Cluster name
            start_time: Start of time range
            end_time: End of time range
            tenant_id: Tenant ID for isolation
            aggregation: Time aggregation (1h, 1d, etc.)
            
        Returns:
            OpenCost metrics for the cluster
        """
        params = {
            "window": f"{start_time.isoformat()},{end_time.isoformat()}",
            "aggregate": "cluster",
            "step": aggregation
        }
        
        try:
            data = await self._make_request("GET", "/allocation", params=params)
            
            # Parse OpenCost response and create metrics
            cluster_data = data.get("data", {}).get(cluster, {})
            
            return OpenCostMetrics(
                cluster=cluster,
                total_cost=cluster_data.get("totalCost", 0.0),
                cost_by_namespace=cluster_data.get("namespaces", {}),
                cost_by_workload=cluster_data.get("workloads", {}),
                cost_by_service=cluster_data.get("services", {}),
                cpu_cost_total=cluster_data.get("cpuCost", 0.0),
                memory_cost_total=cluster_data.get("memoryCost", 0.0),
                storage_cost_total=cluster_data.get("storageCost", 0.0),
                network_cost_total=cluster_data.get("networkCost", 0.0),
                overall_efficiency=cluster_data.get("efficiency", 0.0) * 100,
                wasted_cost=cluster_data.get("wastedCost", 0.0),
                optimization_potential=cluster_data.get("optimizationPotential", 0.0),
                period_start=start_time,
                period_end=end_time,
                tenant_id=tenant_id
            )
            
        except ValidationError as e:
            logger.error(f"Failed to validate OpenCost metrics: {e}")
            raise OpenCostError(f"Invalid OpenCost data format: {e}")
            
    async def get_namespace_costs(
        self,
        cluster: str,
        namespace: str,
        start_time: datetime,
        end_time: datetime,
        tenant_id: str,
        aggregation: str = "1h"
    ) -> List[KubernetesCost]:
        """Get cost data for a specific namespace.
        
        Args:
            cluster: Cluster name
            namespace: Namespace name
            start_time: Start of time range
            end_time: End of time range
            tenant_id: Tenant ID for isolation
            aggregation: Time aggregation
            
        Returns:
            List of Kubernetes cost objects for workloads in namespace
        """
        params = {
            "window": f"{start_time.isoformat()},{end_time.isoformat()}",
            "aggregate": "namespace,workload",
            "filter": f"namespace:{namespace}",
            "step": aggregation
        }
        
        try:
            data = await self._make_request("GET", "/allocation", params=params)
            costs = []
            
            for workload_key, workload_data in data.get("data", {}).items():
                # Parse workload key (format: cluster/namespace/workload)
                parts = workload_key.split("/")
                if len(parts) >= 3:
                    workload_cluster, workload_namespace, workload_name = parts[0], parts[1], parts[2]
                    
                    # Skip if not matching our cluster/namespace
                    if workload_cluster != cluster or workload_namespace != namespace:
                        continue
                        
                    cost = KubernetesCost(
                        namespace=workload_namespace,
                        workload=workload_name,
                        cluster=workload_cluster,
                        cpu_cost=workload_data.get("cpuCost", 0.0),
                        memory_cost=workload_data.get("memoryCost", 0.0),
                        storage_cost=workload_data.get("storageCost", 0.0),
                        network_cost=workload_data.get("networkCost", 0.0),
                        gpu_cost=workload_data.get("gpuCost", 0.0),
                        total_cost=workload_data.get("totalCost", 0.0),
                        efficiency=workload_data.get("efficiency", 0.0) * 100,
                        period_start=start_time,
                        period_end=end_time,
                        tenant_id=tenant_id,
                        labels=workload_data.get("labels", {}),
                        cpu_request=workload_data.get("cpuCoreRequest"),
                        memory_request=workload_data.get("ramByteRequest"),
                        cpu_limit=workload_data.get("cpuCoreLimit"),
                        memory_limit=workload_data.get("ramByteLimit")
                    )
                    costs.append(cost)
                    
            return costs
            
        except ValidationError as e:
            logger.error(f"Failed to validate Kubernetes costs: {e}")
            raise OpenCostError(f"Invalid cost data format: {e}")
            
    async def get_workload_costs(
        self,
        cluster: str,
        namespace: str,
        workload: str,
        start_time: datetime,
        end_time: datetime,
        tenant_id: str,
        aggregation: str = "1h"
    ) -> Optional[KubernetesCost]:
        """Get cost data for a specific workload.
        
        Args:
            cluster: Cluster name
            namespace: Namespace name
            workload: Workload name
            start_time: Start of time range
            end_time: End of time range
            tenant_id: Tenant ID for isolation
            aggregation: Time aggregation
            
        Returns:
            Kubernetes cost object for the workload or None if not found
        """
        costs = await self.get_namespace_costs(
            cluster, namespace, start_time, end_time, tenant_id, aggregation
        )
        
        for cost in costs:
            if cost.workload == workload:
                return cost
                
        return None
        
    async def get_cost_trends(
        self,
        cluster: str,
        namespace: Optional[str] = None,
        workload: Optional[str] = None,
        days: int = 7,
        tenant_id: str = ""
    ) -> List[CostTrend]:
        """Get cost trend analysis for resources.
        
        Args:
            cluster: Cluster name
            namespace: Optional namespace filter
            workload: Optional workload filter
            days: Number of days for trend analysis
            tenant_id: Tenant ID for isolation
            
        Returns:
            List of cost trends for different resource types
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        params = {
            "window": f"{start_time.isoformat()},{end_time.isoformat()}",
            "aggregate": "namespace" if not workload else "workload",
            "step": "1d"  # Daily aggregation for trends
        }
        
        if namespace:
            params["filter"] = f"namespace:{namespace}"
            if workload:
                params["filter"] += f",workload:{workload}"
                
        try:
            data = await self._make_request("GET", "/allocation", params=params)
            trends = []
            
            # Analyze trends for each resource type
            for resource_type in ResourceType:
                trend_data = self._analyze_cost_trend(
                    data.get("data", {}), 
                    resource_type,
                    start_time,
                    end_time
                )
                
                if trend_data:
                    trend = CostTrend(
                        resource_type=resource_type,
                        namespace=namespace or "all",
                        workload=workload,
                        data_points=trend_data["points"],
                        trend_direction=trend_data["direction"],
                        trend_percentage=trend_data["percentage"],
                        period_start=start_time,
                        period_end=end_time,
                        tenant_id=tenant_id
                    )
                    trends.append(trend)
                    
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get cost trends: {e}")
            raise OpenCostError(f"Cost trend analysis failed: {e}")
            
    def _analyze_cost_trend(
        self, 
        data: Dict[str, Any], 
        resource_type: ResourceType,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """Analyze cost trend for a specific resource type.
        
        Args:
            data: OpenCost allocation data
            resource_type: Type of resource to analyze
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Trend analysis data or None if insufficient data
        """
        # Extract cost data points for the resource type
        points = []
        cost_field = f"{resource_type.value}Cost"
        
        for key, allocation in data.items():
            if cost_field in allocation:
                points.append({
                    "timestamp": allocation.get("start", start_time.isoformat()),
                    "cost": allocation[cost_field],
                    "resource": key
                })
                
        if len(points) < 2:
            return None
            
        # Calculate trend direction and percentage
        first_cost = points[0]["cost"]
        last_cost = points[-1]["cost"]
        
        if first_cost == 0:
            percentage = 100.0 if last_cost > 0 else 0.0
            direction = "increasing" if last_cost > 0 else "stable"
        else:
            percentage = ((last_cost - first_cost) / first_cost) * 100
            if abs(percentage) < 5:  # Less than 5% change is considered stable
                direction = "stable"
            elif percentage > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
                
        return {
            "points": points,
            "direction": direction,
            "percentage": percentage
        }
        
    async def generate_cost_optimizations(
        self,
        cluster: str,
        namespace: Optional[str] = None,
        workload: Optional[str] = None,
        tenant_id: str = "",
        min_savings: float = 10.0
    ) -> List[CostOptimization]:
        """Generate cost optimization recommendations.
        
        Args:
            cluster: Cluster name
            namespace: Optional namespace filter
            workload: Optional workload filter
            tenant_id: Tenant ID for isolation
            min_savings: Minimum savings threshold in currency units
            
        Returns:
            List of cost optimization recommendations
        """
        # Get recent cost data for analysis
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        try:
            if workload and namespace:
                cost_data = await self.get_workload_costs(
                    cluster, namespace, workload, start_time, end_time, tenant_id
                )
                cost_list = [cost_data] if cost_data else []
            elif namespace:
                cost_list = await self.get_namespace_costs(
                    cluster, namespace, start_time, end_time, tenant_id
                )
            else:
                # Get cluster-wide data
                metrics = await self.get_cluster_costs(
                    cluster, start_time, end_time, tenant_id
                )
                cost_list = []  # Would need to fetch detailed workload data
                
            optimizations = []
            
            for cost in cost_list:
                # Generate rightsizing recommendations
                rightsizing = self._generate_rightsizing_recommendation(cost)
                if rightsizing and rightsizing.potential_savings >= min_savings:
                    optimizations.append(rightsizing)
                    
                # Generate scheduling optimizations
                scheduling = self._generate_scheduling_recommendation(cost)
                if scheduling and scheduling.potential_savings >= min_savings:
                    optimizations.append(scheduling)
                    
                # Generate storage optimizations
                storage = self._generate_storage_recommendation(cost)
                if storage and storage.potential_savings >= min_savings:
                    optimizations.append(storage)
                    
            return optimizations
            
        except Exception as e:
            logger.error(f"Failed to generate cost optimizations: {e}")
            raise OpenCostError(f"Cost optimization generation failed: {e}")
            
    def _generate_rightsizing_recommendation(self, cost: KubernetesCost) -> Optional[CostOptimization]:
        """Generate rightsizing recommendation for a workload.
        
        Args:
            cost: Kubernetes cost data
            
        Returns:
            Rightsizing optimization or None if not applicable
        """
        # Check if workload has low efficiency (< 50%)
        if cost.efficiency >= 50:
            return None
            
        # Calculate potential savings based on efficiency
        wasted_percentage = (100 - cost.efficiency) / 100
        potential_savings = (cost.cpu_cost + cost.memory_cost) * wasted_percentage * 0.7  # Conservative estimate
        
        if potential_savings < 5.0:  # Minimum threshold
            return None
            
        return CostOptimization(
            type=OptimizationType.RIGHTSIZING,
            title=f"Rightsize {cost.workload} in {cost.namespace}",
            description=f"Workload efficiency is {cost.efficiency:.1f}%. Reducing resource requests could save costs.",
            potential_savings=potential_savings,
            implementation_effort=ImplementationEffort.LOW,
            risk_level=RiskLevel.LOW,
            steps=[
                "Analyze workload resource usage patterns",
                "Reduce CPU and memory requests by 20-30%",
                "Monitor performance after changes",
                "Adjust limits if needed"
            ],
            current_resources={
                "cpu_request": cost.cpu_request or 0,
                "memory_request": cost.memory_request or 0
            },
            recommended_resources={
                "cpu_request": (cost.cpu_request or 0) * 0.7,
                "memory_request": (cost.memory_request or 0) * 0.7
            },
            confidence_score=0.8,
            impact_analysis={
                "performance_impact": "Low - based on current utilization",
                "availability_impact": "None - requests only",
                "monitoring_required": True
            }
        )
        
    def _generate_scheduling_recommendation(self, cost: KubernetesCost) -> Optional[CostOptimization]:
        """Generate scheduling optimization recommendation.
        
        Args:
            cost: Kubernetes cost data
            
        Returns:
            Scheduling optimization or None if not applicable
        """
        # Simple heuristic: if workload has high cost but could use spot instances
        if cost.total_cost < 100:  # Only for higher-cost workloads
            return None
            
        # Check if workload might be suitable for spot instances (no specific indicators in basic cost data)
        potential_savings = cost.total_cost * 0.6  # Spot instances typically 60% cheaper
        
        return CostOptimization(
            type=OptimizationType.SCHEDULING,
            title=f"Use spot instances for {cost.workload}",
            description="Consider migrating to spot instances for significant cost savings.",
            potential_savings=potential_savings,
            implementation_effort=ImplementationEffort.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            steps=[
                "Evaluate workload fault tolerance",
                "Implement graceful shutdown handling",
                "Configure spot instance node pools",
                "Add node affinity for spot instances",
                "Monitor for interruptions"
            ],
            confidence_score=0.6,
            impact_analysis={
                "performance_impact": "None",
                "availability_impact": "Medium - potential interruptions",
                "cost_savings": "High - up to 60% reduction"
            }
        )
        
    def _generate_storage_recommendation(self, cost: KubernetesCost) -> Optional[CostOptimization]:
        """Generate storage optimization recommendation.
        
        Args:
            cost: Kubernetes cost data
            
        Returns:
            Storage optimization or None if not applicable
        """
        # Only generate if storage cost is significant
        if cost.storage_cost < 20:
            return None
            
        # Suggest storage class optimization
        potential_savings = cost.storage_cost * 0.3  # 30% savings from storage class optimization
        
        return CostOptimization(
            type=OptimizationType.STORAGE,
            title=f"Optimize storage for {cost.workload}",
            description="Consider using more cost-effective storage classes or implementing data lifecycle policies.",
            potential_savings=potential_savings,
            implementation_effort=ImplementationEffort.LOW,
            risk_level=RiskLevel.LOW,
            steps=[
                "Audit current storage usage patterns",
                "Identify infrequently accessed data",
                "Migrate to cheaper storage classes",
                "Implement data lifecycle policies",
                "Set up automated cleanup"
            ],
            confidence_score=0.7,
            impact_analysis={
                "performance_impact": "Low - for infrequent access",
                "availability_impact": "None",
                "implementation_time": "1-2 days"
            }
        )
        
    async def create_cost_alert(
        self,
        alert_type: CostAlertType,
        threshold: float,
        namespace: str,
        cluster: str,
        workload: Optional[str] = None,
        tenant_id: str = ""
    ) -> CostAlert:
        """Create a cost alert for monitoring thresholds.
        
        Args:
            alert_type: Type of cost alert
            threshold: Alert threshold value
            namespace: Kubernetes namespace
            cluster: Cluster name
            workload: Optional workload name
            tenant_id: Tenant ID for isolation
            
        Returns:
            Created cost alert
        """
        alert_id = f"{cluster}-{namespace}-{workload or 'all'}-{alert_type.value}-{int(datetime.utcnow().timestamp())}"
        
        alert = CostAlert(
            id=alert_id,
            type=alert_type,
            severity="medium",  # Default severity
            title=f"Cost {alert_type.value.replace('_', ' ').title()}",
            description=f"Cost alert for {namespace}/{workload or 'all workloads'} in {cluster}",
            threshold=threshold,
            current_value=0.0,  # Will be updated when alert triggers
            namespace=namespace,
            workload=workload,
            cluster=cluster,
            tenant_id=tenant_id,
            recommendations=[
                "Review resource usage patterns",
                "Consider optimization recommendations",
                "Check for cost anomalies"
            ]
        )
        
        # In a real implementation, this would be stored in a database
        # For now, we just return the created alert
        logger.info(f"Created cost alert: {alert_id}")
        return alert
        
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenCost service health.
        
        Returns:
            Health status information
        """
        try:
            # Try to make a simple request to check connectivity
            response = await self._make_request("GET", "/healthz")
            return {
                "status": "healthy",
                "opencost_url": self.base_url,
                "response_time_ms": 0,  # Would measure actual response time
                "version": response.get("version", "unknown")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "opencost_url": self.base_url,
                "error": str(e)
            }