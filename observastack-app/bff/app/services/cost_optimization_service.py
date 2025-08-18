"""Cost optimization service for resource utilization analysis and recommendations."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from statistics import mean, median, stdev
import math

from ..models.insights import (
    CostInsight, ResourceUtilization, Recommendation, CapacityForecast,
    RecommendationType, ImpactLevel, EffortLevel, TimePeriod, TrendDirection,
    CostOptimizationRequest, CostOptimizationResponse, TrendAnalysisRequest,
    TrendAnalysisResponse
)
from ..models.common import SeverityLevel
from ..exceptions import SearchException
from .prometheus_client import PrometheusClient

logger = logging.getLogger(__name__)


class CostOptimizationService:
    """Service for cost optimization analysis and recommendations."""
    
    def __init__(self, prometheus_client: PrometheusClient):
        """
        Initialize cost optimization service.
        
        Args:
            prometheus_client: Prometheus client for metrics queries
        """
        self.prometheus = prometheus_client
        
        # Cost configuration (can be moved to config)
        self.cost_per_cpu_hour = 0.05  # USD per CPU core per hour
        self.cost_per_gb_memory_hour = 0.01  # USD per GB memory per hour
        self.cost_per_gb_storage_hour = 0.0001  # USD per GB storage per hour
        
        # Utilization thresholds
        self.cpu_underutilized_threshold = 20.0  # %
        self.cpu_overutilized_threshold = 80.0   # %
        self.memory_underutilized_threshold = 30.0  # %
        self.memory_overutilized_threshold = 85.0   # %
        
        # Rightsizing parameters
        self.rightsizing_buffer = 0.2  # 20% buffer for recommendations
        self.min_observation_hours = 24  # Minimum hours of data for recommendations

    async def analyze_cost_optimization(
        self, 
        request: CostOptimizationRequest, 
        tenant_id: str
    ) -> CostOptimizationResponse:
        """
        Perform comprehensive cost optimization analysis.
        
        Args:
            request: Cost optimization request parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Cost optimization response with recommendations
        """
        try:
            # Get resource utilization data
            utilization_data = await self.get_resource_utilization(
                request.services, request.time_range, tenant_id
            )
            
            # Calculate current costs
            current_cost = await self.calculate_current_costs(
                utilization_data, request.time_range
            )
            
            # Generate rightsizing recommendations
            recommendations = await self.generate_rightsizing_recommendations(
                utilization_data, tenant_id
            )
            
            # Calculate potential savings
            potential_savings = sum(rec.estimated_savings for rec in recommendations)
            optimized_cost = current_cost - potential_savings
            savings_percentage = (potential_savings / current_cost * 100) if current_cost > 0 else 0
            
            # Create implementation plan
            implementation_plan = self._create_implementation_plan(recommendations)
            
            # Assess risks
            risk_assessment = self._assess_optimization_risks(recommendations, utilization_data)
            
            return CostOptimizationResponse(
                success=True,
                current_cost=current_cost,
                optimized_cost=optimized_cost,
                potential_savings=potential_savings,
                savings_percentage=savings_percentage,
                recommendations=recommendations,
                implementation_plan=implementation_plan,
                risk_assessment=risk_assessment
            )
            
        except Exception as e:
            logger.error(f"Cost optimization analysis failed: {e}")
            return CostOptimizationResponse(
                success=False,
                message=f"Cost optimization analysis failed: {str(e)}",
                current_cost=0,
                optimized_cost=0,
                potential_savings=0,
                savings_percentage=0,
                recommendations=[],
                implementation_plan=[],
                risk_assessment={}
            )

    async def get_resource_utilization(
        self, 
        services: Optional[List[str]], 
        time_range: Dict[str, str], 
        tenant_id: str
    ) -> List[ResourceUtilization]:
        """
        Get resource utilization metrics for services.
        
        Args:
            services: List of services to analyze (None for all)
            time_range: Time range for analysis
            tenant_id: Tenant ID for isolation
            
        Returns:
            List of resource utilization data
        """
        utilization_data = []
        
        try:
            # Define resource metrics to query
            resource_metrics = {
                "cpu": {
                    "usage_query": 'rate(container_cpu_usage_seconds_total{tenant_id="' + tenant_id + '"}[5m]) * 100',
                    "capacity_query": 'container_spec_cpu_quota{tenant_id="' + tenant_id + '"} / container_spec_cpu_period{tenant_id="' + tenant_id + '"} * 100'
                },
                "memory": {
                    "usage_query": 'container_memory_usage_bytes{tenant_id="' + tenant_id + '"} / 1024 / 1024 / 1024',
                    "capacity_query": 'container_spec_memory_limit_bytes{tenant_id="' + tenant_id + '"} / 1024 / 1024 / 1024'
                },
                "storage": {
                    "usage_query": 'container_fs_usage_bytes{tenant_id="' + tenant_id + '"} / 1024 / 1024 / 1024',
                    "capacity_query": 'container_fs_limit_bytes{tenant_id="' + tenant_id + '"} / 1024 / 1024 / 1024'
                }
            }
            
            # Query each resource type
            for resource_name, queries in resource_metrics.items():
                usage_data = await self._query_prometheus_range(
                    queries["usage_query"], time_range
                )
                capacity_data = await self._query_prometheus_range(
                    queries["capacity_query"], time_range
                )
                
                # Process data for each service
                service_data = self._process_utilization_data(
                    usage_data, capacity_data, resource_name, services
                )
                utilization_data.extend(service_data)
                
        except Exception as e:
            logger.error(f"Failed to get resource utilization: {e}")
            
        return utilization_data

    async def generate_rightsizing_recommendations(
        self, 
        utilization_data: List[ResourceUtilization], 
        tenant_id: str
    ) -> List[Recommendation]:
        """
        Generate rightsizing recommendations based on utilization data.
        
        Args:
            utilization_data: Resource utilization data
            tenant_id: Tenant ID
            
        Returns:
            List of rightsizing recommendations
        """
        recommendations = []
        
        for util in utilization_data:
            # Skip if insufficient data
            if len(util.trend) < self.min_observation_hours:
                continue
                
            # Analyze utilization patterns
            utilization_values = [point["value"] for point in util.trend]
            avg_utilization = mean(utilization_values)
            max_utilization = max(utilization_values)
            p95_utilization = self._calculate_percentile(utilization_values, 95)
            
            # Generate recommendations based on resource type and utilization
            if "cpu" in util.resource.lower():
                rec = self._generate_cpu_recommendation(
                    util, avg_utilization, max_utilization, p95_utilization, tenant_id
                )
            elif "memory" in util.resource.lower():
                rec = self._generate_memory_recommendation(
                    util, avg_utilization, max_utilization, p95_utilization, tenant_id
                )
            elif "storage" in util.resource.lower():
                rec = self._generate_storage_recommendation(
                    util, avg_utilization, max_utilization, p95_utilization, tenant_id
                )
            else:
                continue
                
            if rec:
                recommendations.append(rec)
                
        return recommendations

    def _generate_cpu_recommendation(
        self, 
        util: ResourceUtilization, 
        avg_util: float, 
        max_util: float, 
        p95_util: float, 
        tenant_id: str
    ) -> Optional[Recommendation]:
        """Generate CPU rightsizing recommendation."""
        
        if avg_util < self.cpu_underutilized_threshold:
            # Downsize recommendation
            recommended_capacity = p95_util * (1 + self.rightsizing_buffer)
            current_cost_per_hour = util.capacity * self.cost_per_cpu_hour
            new_cost_per_hour = recommended_capacity * self.cost_per_cpu_hour
            hourly_savings = current_cost_per_hour - new_cost_per_hour
            monthly_savings = hourly_savings * 24 * 30
            
            return Recommendation(
                id=f"cpu_downsize_{util.resource}_{tenant_id}",
                type=RecommendationType.RIGHTSIZING,
                title=f"Downsize CPU allocation for {util.resource}",
                description=f"Current CPU utilization averages {avg_util:.1f}% with P95 at {p95_util:.1f}%. "
                           f"Consider reducing from {util.capacity:.2f} to {recommended_capacity:.2f} cores.",
                impact=ImpactLevel.MEDIUM if monthly_savings > 50 else ImpactLevel.LOW,
                effort=EffortLevel.LOW,
                estimated_savings=monthly_savings,
                metadata={
                    "current_capacity": util.capacity,
                    "recommended_capacity": recommended_capacity,
                    "avg_utilization": avg_util,
                    "p95_utilization": p95_util,
                    "resource_type": "cpu"
                },
                created_at=datetime.utcnow()
            )
            
        elif max_util > self.cpu_overutilized_threshold:
            # Upsize recommendation
            recommended_capacity = max_util * (1 + self.rightsizing_buffer)
            
            return Recommendation(
                id=f"cpu_upsize_{util.resource}_{tenant_id}",
                type=RecommendationType.RIGHTSIZING,
                title=f"Increase CPU allocation for {util.resource}",
                description=f"CPU utilization peaks at {max_util:.1f}% which may cause performance issues. "
                           f"Consider increasing from {util.capacity:.2f} to {recommended_capacity:.2f} cores.",
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.MEDIUM,
                estimated_savings=0,  # This is a performance improvement, not cost savings
                metadata={
                    "current_capacity": util.capacity,
                    "recommended_capacity": recommended_capacity,
                    "max_utilization": max_util,
                    "resource_type": "cpu",
                    "reason": "performance"
                },
                created_at=datetime.utcnow()
            )
            
        return None

    def _generate_memory_recommendation(
        self, 
        util: ResourceUtilization, 
        avg_util: float, 
        max_util: float, 
        p95_util: float, 
        tenant_id: str
    ) -> Optional[Recommendation]:
        """Generate memory rightsizing recommendation."""
        
        if avg_util < self.memory_underutilized_threshold:
            # Downsize recommendation
            recommended_capacity = p95_util * (1 + self.rightsizing_buffer)
            current_cost_per_hour = util.capacity * self.cost_per_gb_memory_hour
            new_cost_per_hour = recommended_capacity * self.cost_per_gb_memory_hour
            hourly_savings = current_cost_per_hour - new_cost_per_hour
            monthly_savings = hourly_savings * 24 * 30
            
            return Recommendation(
                id=f"memory_downsize_{util.resource}_{tenant_id}",
                type=RecommendationType.RIGHTSIZING,
                title=f"Reduce memory allocation for {util.resource}",
                description=f"Memory utilization averages {avg_util:.1f}% with P95 at {p95_util:.1f}%. "
                           f"Consider reducing from {util.capacity:.2f}GB to {recommended_capacity:.2f}GB.",
                impact=ImpactLevel.MEDIUM if monthly_savings > 20 else ImpactLevel.LOW,
                effort=EffortLevel.LOW,
                estimated_savings=monthly_savings,
                metadata={
                    "current_capacity": util.capacity,
                    "recommended_capacity": recommended_capacity,
                    "avg_utilization": avg_util,
                    "p95_utilization": p95_util,
                    "resource_type": "memory"
                },
                created_at=datetime.utcnow()
            )
            
        elif max_util > self.memory_overutilized_threshold:
            # Upsize recommendation
            recommended_capacity = max_util * (1 + self.rightsizing_buffer)
            
            return Recommendation(
                id=f"memory_upsize_{util.resource}_{tenant_id}",
                type=RecommendationType.RIGHTSIZING,
                title=f"Increase memory allocation for {util.resource}",
                description=f"Memory utilization peaks at {max_util:.1f}% which may cause OOM issues. "
                           f"Consider increasing from {util.capacity:.2f}GB to {recommended_capacity:.2f}GB.",
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.MEDIUM,
                estimated_savings=0,
                metadata={
                    "current_capacity": util.capacity,
                    "recommended_capacity": recommended_capacity,
                    "max_utilization": max_util,
                    "resource_type": "memory",
                    "reason": "reliability"
                },
                created_at=datetime.utcnow()
            )
            
        return None

    def _generate_storage_recommendation(
        self, 
        util: ResourceUtilization, 
        avg_util: float, 
        max_util: float, 
        p95_util: float, 
        tenant_id: str
    ) -> Optional[Recommendation]:
        """Generate storage rightsizing recommendation."""
        
        if avg_util < 50:  # Storage threshold is different
            # Storage optimization recommendation
            recommended_capacity = p95_util * 1.3  # 30% buffer for storage
            current_cost_per_hour = util.capacity * self.cost_per_gb_storage_hour
            new_cost_per_hour = recommended_capacity * self.cost_per_gb_storage_hour
            hourly_savings = current_cost_per_hour - new_cost_per_hour
            monthly_savings = hourly_savings * 24 * 30
            
            return Recommendation(
                id=f"storage_optimize_{util.resource}_{tenant_id}",
                type=RecommendationType.STORAGE,
                title=f"Optimize storage allocation for {util.resource}",
                description=f"Storage utilization averages {avg_util:.1f}%. "
                           f"Consider reducing from {util.capacity:.2f}GB to {recommended_capacity:.2f}GB.",
                impact=ImpactLevel.LOW,
                effort=EffortLevel.MEDIUM,  # Storage changes can be more complex
                estimated_savings=monthly_savings,
                metadata={
                    "current_capacity": util.capacity,
                    "recommended_capacity": recommended_capacity,
                    "avg_utilization": avg_util,
                    "resource_type": "storage"
                },
                created_at=datetime.utcnow()
            )
            
        return None

    async def analyze_trends(
        self, 
        request: TrendAnalysisRequest, 
        tenant_id: str
    ) -> TrendAnalysisResponse:
        """
        Analyze trends in resource utilization and costs.
        
        Args:
            request: Trend analysis request
            tenant_id: Tenant ID for isolation
            
        Returns:
            Trend analysis response with insights
        """
        try:
            trends = {}
            correlations = {}
            forecasts = {}
            insights = []
            
            # Analyze each requested metric
            for metric in request.metrics:
                # Build Prometheus query
                query = f'{metric}{{tenant_id="{tenant_id}"}}'
                if request.services:
                    service_filter = '|'.join(request.services)
                    query = f'{metric}{{tenant_id="{tenant_id}",service=~"{service_filter}"}}'
                
                # Get time series data
                data = await self._query_prometheus_range(query, request.time_range)
                
                if data:
                    # Process trend data
                    trend_data = self._process_trend_data(data, request.granularity)
                    trends[metric] = trend_data
                    
                    # Generate forecast
                    forecast_data = self._generate_forecast(trend_data)
                    forecasts[metric] = forecast_data
                    
                    # Generate insights
                    metric_insights = self._analyze_metric_trends(metric, trend_data)
                    insights.extend(metric_insights)
            
            # Calculate correlations between metrics
            if len(trends) > 1:
                correlations = self._calculate_correlations(trends)
            
            return TrendAnalysisResponse(
                success=True,
                trends=trends,
                correlations=correlations,
                forecasts=forecasts,
                insights=insights
            )
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return TrendAnalysisResponse(
                success=False,
                message=f"Trend analysis failed: {str(e)}",
                trends={},
                correlations={},
                forecasts={},
                insights=[]
            )

    async def calculate_current_costs(
        self, 
        utilization_data: List[ResourceUtilization], 
        time_range: Dict[str, str]
    ) -> float:
        """
        Calculate current costs based on resource utilization.
        
        Args:
            utilization_data: Resource utilization data
            time_range: Time range for cost calculation
            
        Returns:
            Total current cost
        """
        total_cost = 0.0
        
        # Calculate time period in hours
        start_time = datetime.fromisoformat(time_range["start"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(time_range["end"].replace('Z', '+00:00'))
        hours = (end_time - start_time).total_seconds() / 3600
        
        for util in utilization_data:
            resource_type = util.resource.lower()
            
            if "cpu" in resource_type:
                cost = util.capacity * self.cost_per_cpu_hour * hours
            elif "memory" in resource_type:
                cost = util.capacity * self.cost_per_gb_memory_hour * hours
            elif "storage" in resource_type:
                cost = util.capacity * self.cost_per_gb_storage_hour * hours
            else:
                continue
                
            total_cost += cost
            
        return total_cost

    async def _query_prometheus_range(
        self, 
        query: str, 
        time_range: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Query Prometheus for range data."""
        try:
            # Use the existing Prometheus client
            params = {
                "query": query,
                "start": time_range["start"],
                "end": time_range["end"],
                "step": "5m"  # 5-minute resolution
            }
            
            url = f"{self.prometheus.base_url}/api/v1/query_range"
            response = await self.prometheus._client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", {}).get("result", [])
            return []
            
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return []

    def _process_utilization_data(
        self, 
        usage_data: List[Dict], 
        capacity_data: List[Dict], 
        resource_name: str, 
        services: Optional[List[str]]
    ) -> List[ResourceUtilization]:
        """Process raw Prometheus data into utilization objects."""
        utilization_list = []
        
        # Group data by service
        service_usage = {}
        service_capacity = {}
        
        # Process usage data
        for series in usage_data:
            metric = series.get("metric", {})
            service = metric.get("service", metric.get("job", "unknown"))
            
            if services and service not in services:
                continue
                
            values = series.get("values", [])
            service_usage[service] = values
        
        # Process capacity data
        for series in capacity_data:
            metric = series.get("metric", {})
            service = metric.get("service", metric.get("job", "unknown"))
            
            if services and service not in services:
                continue
                
            values = series.get("values", [])
            service_capacity[service] = values
        
        # Create utilization objects
        for service in service_usage.keys():
            if service not in service_capacity:
                continue
                
            usage_values = service_usage[service]
            capacity_values = service_capacity[service]
            
            if not usage_values or not capacity_values:
                continue
            
            # Calculate current utilization
            latest_usage = float(usage_values[-1][1]) if usage_values else 0
            latest_capacity = float(capacity_values[-1][1]) if capacity_values else 1
            current_utilization = (latest_usage / latest_capacity * 100) if latest_capacity > 0 else 0
            
            # Build trend data
            trend_data = []
            for timestamp, value in usage_values:
                trend_data.append({
                    "timestamp": datetime.fromtimestamp(float(timestamp)),
                    "value": float(value)
                })
            
            # Count threshold breaches (simplified)
            threshold_breaches = sum(1 for point in trend_data 
                                   if point["value"] > latest_capacity * 0.9)
            
            utilization = ResourceUtilization(
                resource=f"{service}_{resource_name}",
                current=latest_usage,
                capacity=latest_capacity,
                utilization=current_utilization,
                trend=trend_data,
                recommendations=[],
                threshold_breaches=threshold_breaches,
                last_updated=datetime.utcnow()
            )
            
            utilization_list.append(utilization)
        
        return utilization_list

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def _create_implementation_plan(
        self, 
        recommendations: List[Recommendation]
    ) -> List[Dict[str, Any]]:
        """Create implementation plan for recommendations."""
        plan = []
        
        # Group recommendations by effort level
        low_effort = [r for r in recommendations if r.effort == EffortLevel.LOW]
        medium_effort = [r for r in recommendations if r.effort == EffortLevel.MEDIUM]
        high_effort = [r for r in recommendations if r.effort == EffortLevel.HIGH]
        
        # Phase 1: Low effort, high impact
        if low_effort:
            plan.append({
                "phase": 1,
                "title": "Quick Wins",
                "description": "Low effort recommendations with immediate impact",
                "recommendations": [r.id for r in low_effort],
                "estimated_duration": "1-2 weeks",
                "risk_level": "low"
            })
        
        # Phase 2: Medium effort
        if medium_effort:
            plan.append({
                "phase": 2,
                "title": "Optimization Phase",
                "description": "Medium effort recommendations requiring planning",
                "recommendations": [r.id for r in medium_effort],
                "estimated_duration": "2-4 weeks",
                "risk_level": "medium"
            })
        
        # Phase 3: High effort
        if high_effort:
            plan.append({
                "phase": 3,
                "title": "Strategic Changes",
                "description": "High effort recommendations requiring significant changes",
                "recommendations": [r.id for r in high_effort],
                "estimated_duration": "1-3 months",
                "risk_level": "high"
            })
        
        return plan

    def _assess_optimization_risks(
        self, 
        recommendations: List[Recommendation], 
        utilization_data: List[ResourceUtilization]
    ) -> Dict[str, Any]:
        """Assess risks of implementing optimization recommendations."""
        
        # Calculate risk factors
        downsize_count = sum(1 for r in recommendations 
                           if "downsize" in r.title.lower() or "reduce" in r.title.lower())
        upsize_count = sum(1 for r in recommendations 
                         if "upsize" in r.title.lower() or "increase" in r.title.lower())
        
        high_utilization_services = sum(1 for util in utilization_data 
                                      if util.utilization > 80)
        
        # Assess overall risk level
        risk_score = 0
        if downsize_count > len(recommendations) * 0.7:  # More than 70% downsizing
            risk_score += 3
        if high_utilization_services > len(utilization_data) * 0.3:  # 30% high utilization
            risk_score += 2
        if upsize_count > 0:  # Any upsizing indicates current issues
            risk_score += 1
        
        risk_level = "low"
        if risk_score >= 4:
            risk_level = "high"
        elif risk_score >= 2:
            risk_level = "medium"
        
        return {
            "overall_risk": risk_level,
            "risk_score": risk_score,
            "factors": {
                "downsize_recommendations": downsize_count,
                "upsize_recommendations": upsize_count,
                "high_utilization_services": high_utilization_services
            },
            "mitigation_strategies": [
                "Implement changes gradually",
                "Monitor performance closely after changes",
                "Have rollback plan ready",
                "Test in staging environment first"
            ]
        }

    def _process_trend_data(
        self, 
        data: List[Dict], 
        granularity: str
    ) -> List[Dict[str, Any]]:
        """Process Prometheus data into trend format."""
        trend_points = []
        
        for series in data:
            values = series.get("values", [])
            for timestamp, value in values:
                trend_points.append({
                    "timestamp": datetime.fromtimestamp(float(timestamp)).isoformat(),
                    "value": float(value)
                })
        
        return sorted(trend_points, key=lambda x: x["timestamp"])

    def _generate_forecast(
        self, 
        trend_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate simple linear forecast from trend data."""
        if len(trend_data) < 2:
            return []
        
        # Simple linear regression for forecasting
        values = [point["value"] for point in trend_data]
        n = len(values)
        
        # Calculate trend
        x_values = list(range(n))
        x_mean = mean(x_values)
        y_mean = mean(values)
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return []
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Generate forecast points (next 24 hours)
        forecast_points = []
        last_timestamp = datetime.fromisoformat(trend_data[-1]["timestamp"])
        
        for i in range(1, 25):  # Next 24 hours
            forecast_time = last_timestamp + timedelta(hours=i)
            forecast_value = intercept + slope * (n + i)
            
            forecast_points.append({
                "timestamp": forecast_time.isoformat(),
                "value": max(0, forecast_value),  # Ensure non-negative
                "confidence": max(0.1, 1.0 - (i * 0.03))  # Decreasing confidence
            })
        
        return forecast_points

    def _analyze_metric_trends(
        self, 
        metric: str, 
        trend_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Analyze trends and generate insights."""
        insights = []
        
        if len(trend_data) < 10:
            return insights
        
        values = [point["value"] for point in trend_data]
        
        # Calculate trend direction
        recent_values = values[-10:]  # Last 10 points
        older_values = values[-20:-10] if len(values) >= 20 else values[:-10]
        
        if older_values:
            recent_avg = mean(recent_values)
            older_avg = mean(older_values)
            
            change_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
            
            if abs(change_percent) > 20:
                direction = "increased" if change_percent > 0 else "decreased"
                insights.append(
                    f"{metric} has {direction} by {abs(change_percent):.1f}% in recent period"
                )
        
        # Check for volatility
        if len(values) > 5:
            try:
                std_dev = stdev(values)
                mean_val = mean(values)
                cv = (std_dev / mean_val) if mean_val > 0 else 0
                
                if cv > 0.5:
                    insights.append(f"{metric} shows high volatility (CV: {cv:.2f})")
            except:
                pass  # Skip if calculation fails
        
        return insights

    def _calculate_correlations(
        self, 
        trends: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, float]:
        """Calculate correlations between metrics."""
        correlations = {}
        metric_names = list(trends.keys())
        
        for i, metric1 in enumerate(metric_names):
            for metric2 in metric_names[i+1:]:
                try:
                    values1 = [point["value"] for point in trends[metric1]]
                    values2 = [point["value"] for point in trends[metric2]]
                    
                    # Ensure same length
                    min_len = min(len(values1), len(values2))
                    values1 = values1[:min_len]
                    values2 = values2[:min_len]
                    
                    if min_len > 1:
                        correlation = self._pearson_correlation(values1, values2)
                        correlations[f"{metric1}_vs_{metric2}"] = correlation
                except:
                    continue
        
        return correlations

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator