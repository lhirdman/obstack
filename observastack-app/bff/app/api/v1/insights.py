"""Insights and cost optimization API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import json

from ...auth.dependencies import get_current_user
from ...auth.models import UserContext
from ...models.insights import (
    InsightsDashboardRequest, InsightsDashboardResponse,
    CostOptimizationRequest, CostOptimizationResponse,
    TrendAnalysisRequest, TrendAnalysisResponse,
    BenchmarkingRequest, BenchmarkingResponse,
    CostInsight, ResourceUtilization, CapacityForecast
)
from ...services.cost_optimization_service import CostOptimizationService
from ...services.prometheus_client import PrometheusClient

router = APIRouter(prefix="/insights", tags=["insights"])


def get_cost_optimization_service() -> CostOptimizationService:
    """Dependency to get cost optimization service."""
    prometheus_client = PrometheusClient()
    return CostOptimizationService(prometheus_client)


@router.get("/dashboard", response_model=InsightsDashboardResponse)
async def get_insights_dashboard(
    categories: Optional[List[str]] = Query(None, description="Insight categories to include"),
    time_range_start: Optional[str] = Query(None, description="Start time (ISO format)"),
    time_range_end: Optional[str] = Query(None, description="End time (ISO format)"),
    services: Optional[List[str]] = Query(None, description="Services to analyze"),
    severity_filter: Optional[List[str]] = Query(None, description="Severity levels to include"),
    include_recommendations: bool = Query(True, description="Include recommendations"),
    current_user: UserContext = Depends(get_current_user),
    cost_service: CostOptimizationService = Depends(get_cost_optimization_service)
):
    """
    Get comprehensive insights dashboard data.
    
    Returns cost insights, performance metrics, capacity forecasts,
    and anomaly detection results for the user's tenant.
    """
    try:
        # Build time range
        time_range = {}
        if time_range_start and time_range_end:
            time_range = {"start": time_range_start, "end": time_range_end}
        else:
            # Default to last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            time_range = {
                "start": start_time.isoformat() + "Z",
                "end": end_time.isoformat() + "Z"
            }
        
        # Get resource utilization data
        utilization_data = await cost_service.get_resource_utilization(
            services, time_range, current_user.tenant_id
        )
        
        # Generate cost insights
        cost_insights = []
        if not categories or "cost" in categories:
            # Create cost optimization request
            cost_request = CostOptimizationRequest(
                services=services,
                time_range=time_range,
                optimization_goals=["reduce_costs", "improve_efficiency"]
            )
            
            cost_response = await cost_service.analyze_cost_optimization(
                cost_request, current_user.tenant_id
            )
            
            if cost_response.success:
                # Convert to cost insights format
                cost_insight = CostInsight(
                    category="infrastructure",
                    current_cost=cost_response.current_cost,
                    projected_cost=cost_response.optimized_cost,
                    savings_opportunity=cost_response.potential_savings,
                    period="monthly",
                    recommendations=cost_response.recommendations,
                    timestamp=datetime.utcnow(),
                    confidence_score=0.85,
                    data_sources=["prometheus", "cost_optimization_engine"]
                )
                cost_insights.append(cost_insight)
        
        # Generate capacity forecasts
        capacity_forecasts = []
        if not categories or "capacity" in categories:
            for util in utilization_data[:5]:  # Limit to top 5 resources
                # Simple forecast based on current trend
                forecast = CapacityForecast(
                    resource=util.resource,
                    current_usage=util.current,
                    projected_usage=util.current * 1.1,  # Simple 10% growth projection
                    capacity_limit=util.capacity,
                    forecast_period="monthly",
                    confidence_interval={"lower": 0.8, "upper": 1.2},
                    breach_probability=0.1 if util.utilization < 70 else 0.3,
                    recommended_actions=[],
                    model_accuracy=0.75,
                    created_at=datetime.utcnow()
                )
                capacity_forecasts.append(forecast)
        
        # Generate summary metrics
        summary_metrics = {
            "total_services": len(set(util.resource.split('_')[0] for util in utilization_data)),
            "avg_cpu_utilization": sum(util.utilization for util in utilization_data 
                                     if "cpu" in util.resource.lower()) / 
                                   max(1, len([u for u in utilization_data if "cpu" in u.resource.lower()])),
            "avg_memory_utilization": sum(util.utilization for util in utilization_data 
                                        if "memory" in util.resource.lower()) / 
                                     max(1, len([u for u in utilization_data if "memory" in u.resource.lower()])),
            "potential_monthly_savings": sum(rec.estimated_savings for insight in cost_insights 
                                           for rec in insight.recommendations),
            "high_utilization_resources": len([u for u in utilization_data if u.utilization > 80]),
            "underutilized_resources": len([u for u in utilization_data if u.utilization < 30])
        }
        
        return InsightsDashboardResponse(
            success=True,
            cost_insights=cost_insights,
            performance_insights=[],  # TODO: Implement performance insights
            capacity_forecasts=capacity_forecasts,
            anomalies=[],  # TODO: Implement anomaly detection
            resource_utilization=utilization_data,
            summary_metrics=summary_metrics,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights dashboard: {str(e)}")


@router.post("/cost-optimization", response_model=CostOptimizationResponse)
async def analyze_cost_optimization(
    request: CostOptimizationRequest,
    current_user: UserContext = Depends(get_current_user),
    cost_service: CostOptimizationService = Depends(get_cost_optimization_service)
):
    """
    Perform comprehensive cost optimization analysis.
    
    Analyzes resource utilization patterns and generates rightsizing
    recommendations with potential cost savings.
    """
    try:
        response = await cost_service.analyze_cost_optimization(request, current_user.tenant_id)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost optimization analysis failed: {str(e)}")


@router.post("/trend-analysis", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    current_user: UserContext = Depends(get_current_user),
    cost_service: CostOptimizationService = Depends(get_cost_optimization_service)
):
    """
    Analyze trends in resource utilization and performance metrics.
    
    Provides trend analysis, correlations, and forecasting for specified metrics.
    """
    try:
        response = await cost_service.analyze_trends(request, current_user.tenant_id)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/resource-utilization", response_model=List[ResourceUtilization])
async def get_resource_utilization(
    services: Optional[List[str]] = Query(None, description="Services to analyze"),
    time_range_start: Optional[str] = Query(None, description="Start time (ISO format)"),
    time_range_end: Optional[str] = Query(None, description="End time (ISO format)"),
    current_user: UserContext = Depends(get_current_user),
    cost_service: CostOptimizationService = Depends(get_cost_optimization_service)
):
    """
    Get detailed resource utilization metrics for services.
    
    Returns CPU, memory, and storage utilization data with trends.
    """
    try:
        # Build time range
        time_range = {}
        if time_range_start and time_range_end:
            time_range = {"start": time_range_start, "end": time_range_end}
        else:
            # Default to last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            time_range = {
                "start": start_time.isoformat() + "Z",
                "end": end_time.isoformat() + "Z"
            }
        
        utilization_data = await cost_service.get_resource_utilization(
            services, time_range, current_user.tenant_id
        )
        
        return utilization_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource utilization: {str(e)}")


@router.get("/cost-breakdown")
async def get_cost_breakdown(
    services: Optional[List[str]] = Query(None, description="Services to analyze"),
    time_range_start: Optional[str] = Query(None, description="Start time (ISO format)"),
    time_range_end: Optional[str] = Query(None, description="End time (ISO format)"),
    group_by: str = Query("service", description="Group costs by: service, resource_type, time"),
    current_user: UserContext = Depends(get_current_user),
    cost_service: CostOptimizationService = Depends(get_cost_optimization_service)
):
    """
    Get detailed cost breakdown by service, resource type, or time period.
    
    Provides granular cost analysis for better understanding of spending patterns.
    """
    try:
        # Build time range
        time_range = {}
        if time_range_start and time_range_end:
            time_range = {"start": time_range_start, "end": time_range_end}
        else:
            # Default to last 30 days
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            time_range = {
                "start": start_time.isoformat() + "Z",
                "end": end_time.isoformat() + "Z"
            }
        
        # Get utilization data
        utilization_data = await cost_service.get_resource_utilization(
            services, time_range, current_user.tenant_id
        )
        
        # Calculate costs and group by requested dimension
        cost_breakdown = {}
        
        for util in utilization_data:
            # Determine grouping key
            if group_by == "service":
                key = util.resource.split('_')[0]  # Extract service name
            elif group_by == "resource_type":
                key = util.resource.split('_')[-1]  # Extract resource type
            elif group_by == "time":
                key = util.last_updated.strftime("%Y-%m-%d")  # Group by day
            else:
                key = "total"
            
            # Calculate cost based on resource type
            resource_type = util.resource.lower()
            if "cpu" in resource_type:
                cost = util.capacity * cost_service.cost_per_cpu_hour * 24 * 30  # Monthly
            elif "memory" in resource_type:
                cost = util.capacity * cost_service.cost_per_gb_memory_hour * 24 * 30
            elif "storage" in resource_type:
                cost = util.capacity * cost_service.cost_per_gb_storage_hour * 24 * 30
            else:
                cost = 0
            
            if key not in cost_breakdown:
                cost_breakdown[key] = {
                    "total_cost": 0,
                    "cpu_cost": 0,
                    "memory_cost": 0,
                    "storage_cost": 0,
                    "resources": []
                }
            
            cost_breakdown[key]["total_cost"] += cost
            if "cpu" in resource_type:
                cost_breakdown[key]["cpu_cost"] += cost
            elif "memory" in resource_type:
                cost_breakdown[key]["memory_cost"] += cost
            elif "storage" in resource_type:
                cost_breakdown[key]["storage_cost"] += cost
            
            cost_breakdown[key]["resources"].append({
                "resource": util.resource,
                "utilization": util.utilization,
                "cost": cost
            })
        
        return {
            "breakdown": cost_breakdown,
            "total_cost": sum(item["total_cost"] for item in cost_breakdown.values()),
            "group_by": group_by,
            "time_range": time_range,
            "currency": "USD"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost breakdown: {str(e)}")


@router.get("/recommendations/stream")
async def stream_recommendations(
    services: Optional[List[str]] = Query(None, description="Services to analyze"),
    time_range_start: Optional[str] = Query(None, description="Start time (ISO format)"),
    time_range_end: Optional[str] = Query(None, description="End time (ISO format)"),
    current_user: UserContext = Depends(get_current_user),
    cost_service: CostOptimizationService = Depends(get_cost_optimization_service)
):
    """
    Stream cost optimization recommendations in real-time.
    
    Provides server-sent events with recommendations as they are generated.
    """
    async def generate_recommendations():
        try:
            # Build time range
            time_range = {}
            if time_range_start and time_range_end:
                time_range = {"start": time_range_start, "end": time_range_end}
            else:
                # Default to last 24 hours
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)
                time_range = {
                    "start": start_time.isoformat() + "Z",
                    "end": end_time.isoformat() + "Z"
                }
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting analysis...'})}\n\n"
            
            # Get utilization data
            yield f"data: {json.dumps({'type': 'status', 'message': 'Gathering resource utilization data...'})}\n\n"
            utilization_data = await cost_service.get_resource_utilization(
                services, time_range, current_user.tenant_id
            )
            
            # Generate recommendations
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing utilization patterns...'})}\n\n"
            recommendations = await cost_service.generate_rightsizing_recommendations(
                utilization_data, current_user.tenant_id
            )
            
            # Stream recommendations one by one
            for i, rec in enumerate(recommendations):
                yield f"data: {json.dumps({'type': 'recommendation', 'data': rec.dict(), 'index': i})}\n\n"
            
            # Send completion status
            yield f"data: {json.dumps({'type': 'complete', 'total': len(recommendations)})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_recommendations(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/benchmarking", response_model=BenchmarkingResponse)
async def perform_benchmarking(
    request: BenchmarkingRequest,
    current_user: UserContext = Depends(get_current_user)
):
    """
    Perform benchmarking analysis against historical or peer data.
    
    Compares current performance metrics against baselines to identify
    optimization opportunities.
    """
    try:
        # TODO: Implement benchmarking logic
        # This is a placeholder implementation
        
        benchmarks = {
            "cpu_utilization": {"current": 65.0, "baseline": 70.0, "peer_avg": 68.0},
            "memory_utilization": {"current": 75.0, "baseline": 80.0, "peer_avg": 72.0},
            "response_time": {"current": 150.0, "baseline": 200.0, "peer_avg": 180.0}
        }
        
        # Calculate performance score
        performance_score = 75.0  # Placeholder
        
        return BenchmarkingResponse(
            success=True,
            service=request.service,
            benchmarks=benchmarks,
            performance_score=performance_score,
            recommendations=[],
            comparison_data={"comparison_type": request.comparison_type}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmarking analysis failed: {str(e)}")