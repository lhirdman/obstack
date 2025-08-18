"""Cost monitoring and optimization API endpoints with OpenCost integration."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
import json
import logging

from ...auth.dependencies import get_current_user
from ...auth.models import UserContext
from ...models.opencost import (
    CostQueryRequest, CostQueryResponse,
    CostAlertRequest, CostAlertResponse,
    CostOptimizationRequest, CostOptimizationResponse,
    CostReportRequest, CostReportResponse,
    KubernetesCost, CostAlert, CostOptimization,
    CostTrend, OpenCostMetrics, CostAlertType,
    OptimizationType
)
from ...services.opencost_client import OpenCostClient
from ...core.config import get_settings
from ...exceptions import OpenCostError, TenantIsolationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/costs", tags=["costs"])


def get_opencost_client() -> OpenCostClient:
    """Dependency to get OpenCost client."""
    settings = get_settings()
    return OpenCostClient(base_url=settings.opencost_url)


@router.post("/query", response_model=CostQueryResponse)
async def query_costs(
    request: CostQueryRequest,
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Query cost data with tenant filtering and time range.
    
    Retrieves Kubernetes cost data from OpenCost with proper tenant isolation
    and optional recommendations for cost optimization.
    """
    try:
        async with opencost_client:
            costs = []
            total_cost = 0.0
            cost_breakdown = {}
            trends = []
            recommendations = []
            
            # Query cluster-level costs if no specific filters
            if not request.namespace and not request.workload:
                if request.cluster:
                    metrics = await opencost_client.get_cluster_costs(
                        cluster=request.cluster,
                        start_time=request.start_time,
                        end_time=request.end_time,
                        tenant_id=current_user.tenant_id,
                        aggregation=request.aggregation
                    )
                    total_cost = metrics.total_cost
                    cost_breakdown = {
                        "cpu": metrics.cpu_cost_total,
                        "memory": metrics.memory_cost_total,
                        "storage": metrics.storage_cost_total,
                        "network": metrics.network_cost_total
                    }
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Cluster name is required for cluster-wide queries"
                    )
            
            # Query namespace-level costs
            elif request.namespace and not request.workload:
                if not request.cluster:
                    raise HTTPException(
                        status_code=400,
                        detail="Cluster name is required for namespace queries"
                    )
                
                costs = await opencost_client.get_namespace_costs(
                    cluster=request.cluster,
                    namespace=request.namespace,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    tenant_id=current_user.tenant_id,
                    aggregation=request.aggregation
                )
                total_cost = sum(cost.total_cost for cost in costs)
                
                # Build cost breakdown by workload
                cost_breakdown = {}
                for cost in costs:
                    cost_breakdown[cost.workload] = cost.total_cost
            
            # Query specific workload costs
            elif request.workload and request.namespace:
                if not request.cluster:
                    raise HTTPException(
                        status_code=400,
                        detail="Cluster name is required for workload queries"
                    )
                
                workload_cost = await opencost_client.get_workload_costs(
                    cluster=request.cluster,
                    namespace=request.namespace,
                    workload=request.workload,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    tenant_id=current_user.tenant_id,
                    aggregation=request.aggregation
                )
                
                if workload_cost:
                    costs = [workload_cost]
                    total_cost = workload_cost.total_cost
                    cost_breakdown = {
                        "cpu": workload_cost.cpu_cost,
                        "memory": workload_cost.memory_cost,
                        "storage": workload_cost.storage_cost,
                        "network": workload_cost.network_cost
                    }
            
            # Get cost trends if requested
            if request.cluster:
                trends = await opencost_client.get_cost_trends(
                    cluster=request.cluster,
                    namespace=request.namespace,
                    workload=request.workload,
                    days=7,  # Default to 7 days for trends
                    tenant_id=current_user.tenant_id
                )
            
            # Generate recommendations if requested
            if request.include_recommendations and request.cluster:
                recommendations = await opencost_client.generate_cost_optimizations(
                    cluster=request.cluster,
                    namespace=request.namespace,
                    workload=request.workload,
                    tenant_id=current_user.tenant_id,
                    min_savings=5.0  # Minimum $5 savings threshold
                )
            
            return CostQueryResponse(
                success=True,
                costs=costs,
                total_cost=total_cost,
                cost_breakdown=cost_breakdown,
                trends=trends,
                recommendations=recommendations,
                query_metadata={
                    "cluster": request.cluster,
                    "namespace": request.namespace,
                    "workload": request.workload,
                    "time_range": {
                        "start": request.start_time.isoformat(),
                        "end": request.end_time.isoformat()
                    },
                    "aggregation": request.aggregation,
                    "tenant_id": current_user.tenant_id
                }
            )
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Cost query failed: {e}")
        raise HTTPException(status_code=500, detail="Cost query failed")


@router.get("/clusters/{cluster}/namespaces/{namespace}/costs", response_model=List[KubernetesCost])
async def get_namespace_costs(
    cluster: str = Path(..., description="Kubernetes cluster name"),
    namespace: str = Path(..., description="Kubernetes namespace"),
    start_time: datetime = Query(..., description="Start time for cost data"),
    end_time: datetime = Query(..., description="End time for cost data"),
    aggregation: str = Query("1h", description="Time aggregation (1h, 1d, etc.)"),
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Get cost data for all workloads in a specific namespace.
    
    Returns detailed cost breakdown by workload with resource-level costs
    and efficiency metrics.
    """
    try:
        async with opencost_client:
            costs = await opencost_client.get_namespace_costs(
                cluster=cluster,
                namespace=namespace,
                start_time=start_time,
                end_time=end_time,
                tenant_id=current_user.tenant_id,
                aggregation=aggregation
            )
            
            return costs
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Namespace cost query failed: {e}")
        raise HTTPException(status_code=500, detail="Namespace cost query failed")


@router.get("/clusters/{cluster}/metrics", response_model=OpenCostMetrics)
async def get_cluster_metrics(
    cluster: str = Path(..., description="Kubernetes cluster name"),
    start_time: datetime = Query(..., description="Start time for metrics"),
    end_time: datetime = Query(..., description="End time for metrics"),
    aggregation: str = Query("1h", description="Time aggregation"),
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Get comprehensive cost metrics for a Kubernetes cluster.
    
    Returns cluster-wide cost metrics including breakdowns by namespace,
    workload, and resource type with efficiency analysis.
    """
    try:
        async with opencost_client:
            metrics = await opencost_client.get_cluster_costs(
                cluster=cluster,
                start_time=start_time,
                end_time=end_time,
                tenant_id=current_user.tenant_id,
                aggregation=aggregation
            )
            
            return metrics
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Cluster metrics query failed: {e}")
        raise HTTPException(status_code=500, detail="Cluster metrics query failed")


@router.get("/trends", response_model=List[CostTrend])
async def get_cost_trends(
    cluster: str = Query(..., description="Kubernetes cluster name"),
    namespace: Optional[str] = Query(None, description="Optional namespace filter"),
    workload: Optional[str] = Query(None, description="Optional workload filter"),
    days: int = Query(7, ge=1, le=90, description="Number of days for trend analysis"),
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Get cost trend analysis for resources over time.
    
    Analyzes cost trends for different resource types and provides
    forecasting data for capacity planning.
    """
    try:
        async with opencost_client:
            trends = await opencost_client.get_cost_trends(
                cluster=cluster,
                namespace=namespace,
                workload=workload,
                days=days,
                tenant_id=current_user.tenant_id
            )
            
            return trends
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Cost trends query failed: {e}")
        raise HTTPException(status_code=500, detail="Cost trends query failed")


@router.post("/optimization", response_model=CostOptimizationResponse)
async def analyze_cost_optimization(
    request: CostOptimizationRequest,
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Generate cost optimization recommendations.
    
    Analyzes resource utilization patterns and generates actionable
    recommendations for cost reduction and efficiency improvements.
    """
    try:
        async with opencost_client:
            optimizations = await opencost_client.generate_cost_optimizations(
                cluster=request.cluster,
                namespace=request.namespace,
                workload=request.workload,
                tenant_id=current_user.tenant_id,
                min_savings=request.min_savings_threshold
            )
            
            # Filter by optimization types if specified
            if request.optimization_types:
                optimizations = [
                    opt for opt in optimizations 
                    if opt.type in request.optimization_types
                ]
            
            # Calculate total potential savings
            total_potential_savings = sum(opt.potential_savings for opt in optimizations)
            
            # Create implementation priority based on savings and effort
            implementation_priority = []
            for opt in sorted(optimizations, key=lambda x: (x.potential_savings, -x.implementation_effort.value), reverse=True):
                implementation_priority.append(f"{opt.type.value}: ${opt.potential_savings:.2f} savings")
            
            return CostOptimizationResponse(
                success=True,
                optimizations=optimizations,
                total_potential_savings=total_potential_savings,
                implementation_priority=implementation_priority,
                analysis_metadata={
                    "cluster": request.cluster,
                    "namespace": request.namespace,
                    "workload": request.workload,
                    "time_range_days": request.time_range_days,
                    "min_savings_threshold": request.min_savings_threshold,
                    "optimization_types": [t.value for t in request.optimization_types] if request.optimization_types else "all",
                    "tenant_id": current_user.tenant_id,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Cost optimization analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Cost optimization analysis failed")


@router.post("/alerts", response_model=CostAlertResponse)
async def create_cost_alert(
    request: CostAlertRequest,
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Create a cost alert for monitoring thresholds.
    
    Sets up cost monitoring alerts that trigger when spending exceeds
    thresholds or when cost anomalies are detected.
    """
    try:
        async with opencost_client:
            alert = await opencost_client.create_cost_alert(
                alert_type=request.type,
                threshold=request.threshold,
                namespace=request.namespace,
                cluster=request.cluster,
                workload=request.workload,
                tenant_id=current_user.tenant_id
            )
            
            return CostAlertResponse(
                success=True,
                alert=alert,
                created=True
            )
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Cost alert creation failed: {e}")
        raise HTTPException(status_code=500, detail="Cost alert creation failed")


@router.get("/alerts", response_model=List[CostAlert])
async def get_cost_alerts(
    cluster: Optional[str] = Query(None, description="Filter by cluster"),
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    alert_type: Optional[CostAlertType] = Query(None, description="Filter by alert type"),
    active_only: bool = Query(True, description="Only return active alerts"),
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get cost alerts for the current tenant.
    
    Returns cost alerts with optional filtering by cluster, namespace,
    or alert type. Supports both active and resolved alerts.
    """
    try:
        # TODO: Implement alert storage and retrieval
        # For now, return empty list as alerts would be stored in database
        alerts = []
        
        # In a real implementation, this would query the database:
        # alerts = await cost_alert_service.get_alerts(
        #     tenant_id=current_user.tenant_id,
        #     cluster=cluster,
        #     namespace=namespace,
        #     alert_type=alert_type,
        #     active_only=active_only
        # )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Cost alerts query failed: {e}")
        raise HTTPException(status_code=500, detail="Cost alerts query failed")


@router.put("/alerts/{alert_id}/resolve")
async def resolve_cost_alert(
    alert_id: str = Path(..., description="Cost alert ID"),
    current_user: UserContext = Depends(get_current_user)
):
    """
    Resolve a cost alert.
    
    Marks a cost alert as resolved and updates its status.
    """
    try:
        # TODO: Implement alert resolution
        # In a real implementation:
        # await cost_alert_service.resolve_alert(alert_id, current_user.tenant_id)
        
        return {"success": True, "message": f"Alert {alert_id} resolved"}
        
    except Exception as e:
        logger.error(f"Cost alert resolution failed: {e}")
        raise HTTPException(status_code=500, detail="Cost alert resolution failed")


@router.post("/reports", response_model=CostReportResponse)
async def generate_cost_report(
    request: CostReportRequest,
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Generate cost reports for chargeback and showback.
    
    Creates detailed cost reports with various grouping options
    for chargeback, showback, and cost allocation purposes.
    """
    try:
        async with opencost_client:
            # Get cost data for the report period
            if request.cluster:
                metrics = await opencost_client.get_cluster_costs(
                    cluster=request.cluster,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    tenant_id=current_user.tenant_id,
                    aggregation="1d"  # Daily aggregation for reports
                )
                
                # Build report data based on report type
                report_data = {}
                summary = {}
                charts = []
                
                if request.report_type == "chargeback":
                    # Chargeback report with actual costs
                    report_data = {
                        "type": "chargeback",
                        "total_cost": metrics.total_cost,
                        "cost_by_namespace": metrics.cost_by_namespace,
                        "cost_by_workload": metrics.cost_by_workload,
                        "resource_breakdown": {
                            "cpu": metrics.cpu_cost_total,
                            "memory": metrics.memory_cost_total,
                            "storage": metrics.storage_cost_total,
                            "network": metrics.network_cost_total
                        }
                    }
                    summary = {
                        "total_cost": metrics.total_cost,
                        "efficiency": metrics.overall_efficiency,
                        "wasted_cost": metrics.wasted_cost
                    }
                
                elif request.report_type == "showback":
                    # Showback report for visibility without billing
                    report_data = {
                        "type": "showback",
                        "usage_metrics": {
                            "cpu_hours": metrics.cpu_cost_total / 0.05,  # Assuming $0.05/hour
                            "memory_gb_hours": metrics.memory_cost_total / 0.01,  # Assuming $0.01/GB-hour
                            "storage_gb_hours": metrics.storage_cost_total / 0.001  # Assuming $0.001/GB-hour
                        },
                        "efficiency_metrics": {
                            "overall_efficiency": metrics.overall_efficiency,
                            "optimization_potential": metrics.optimization_potential
                        }
                    }
                    summary = {
                        "efficiency_score": metrics.overall_efficiency,
                        "optimization_potential": metrics.optimization_potential
                    }
                
                elif request.report_type == "allocation":
                    # Cost allocation report
                    report_data = {
                        "type": "allocation",
                        "allocations": metrics.cost_by_namespace,
                        "unallocated": max(0, metrics.total_cost - sum(metrics.cost_by_namespace.values()))
                    }
                    summary = {
                        "allocated_cost": sum(metrics.cost_by_namespace.values()),
                        "allocation_percentage": (sum(metrics.cost_by_namespace.values()) / metrics.total_cost * 100) if metrics.total_cost > 0 else 0
                    }
                
                # Generate charts data
                charts = [
                    {
                        "type": "pie",
                        "title": "Cost by Namespace",
                        "data": metrics.cost_by_namespace
                    },
                    {
                        "type": "bar",
                        "title": "Resource Cost Breakdown",
                        "data": {
                            "CPU": metrics.cpu_cost_total,
                            "Memory": metrics.memory_cost_total,
                            "Storage": metrics.storage_cost_total,
                            "Network": metrics.network_cost_total
                        }
                    }
                ]
                
                return CostReportResponse(
                    success=True,
                    report_data=report_data,
                    summary=summary,
                    charts=charts,
                    export_urls={
                        "pdf": f"/api/v1/costs/reports/export/{request.report_type}.pdf",
                        "csv": f"/api/v1/costs/reports/export/{request.report_type}.csv",
                        "excel": f"/api/v1/costs/reports/export/{request.report_type}.xlsx"
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Cluster name is required for cost reports"
                )
            
    except TenantIsolationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OpenCostError as e:
        raise HTTPException(status_code=500, detail=f"OpenCost error: {str(e)}")
    except Exception as e:
        logger.error(f"Cost report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Cost report generation failed")


@router.get("/allocation/stream")
async def stream_cost_allocation(
    cluster: str = Query(..., description="Kubernetes cluster name"),
    start_time: datetime = Query(..., description="Start time for allocation data"),
    end_time: datetime = Query(..., description="End time for allocation data"),
    current_user: UserContext = Depends(get_current_user),
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Stream real-time cost allocation data.
    
    Provides server-sent events with cost allocation updates
    for real-time cost monitoring dashboards.
    """
    async def generate_allocation_stream():
        try:
            async with opencost_client:
                # Send initial status
                yield f"data: {json.dumps({'type': 'status', 'message': 'Starting cost allocation stream...'})}\n\n"
                
                # Get initial allocation data
                metrics = await opencost_client.get_cluster_costs(
                    cluster=cluster,
                    start_time=start_time,
                    end_time=end_time,
                    tenant_id=current_user.tenant_id,
                    aggregation="1h"
                )
                
                # Stream allocation data
                allocation_data = {
                    "type": "allocation",
                    "cluster": cluster,
                    "total_cost": metrics.total_cost,
                    "namespaces": metrics.cost_by_namespace,
                    "workloads": metrics.cost_by_workload,
                    "efficiency": metrics.overall_efficiency,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(allocation_data)}\n\n"
                
                # Send completion status
                yield f"data: {json.dumps({'type': 'complete', 'message': 'Cost allocation data sent'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_allocation_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.get("/health")
async def cost_service_health(
    opencost_client: OpenCostClient = Depends(get_opencost_client)
):
    """
    Check health status of OpenCost service.
    
    Returns health information for the OpenCost integration
    and connectivity status.
    """
    try:
        async with opencost_client:
            health_status = await opencost_client.health_check()
            return health_status
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }