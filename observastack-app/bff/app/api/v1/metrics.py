"""Prometheus metrics endpoint for application monitoring."""

from datetime import datetime, timedelta
from typing import Dict, List
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from ...core.monitoring import metrics_collector, health_checker, HealthStatus
from ...core.logging import get_logger

logger = get_logger("api.metrics")

router = APIRouter(tags=["metrics"])


def format_prometheus_metric(
    name: str,
    value: float,
    labels: Dict[str, str] = None,
    metric_type: str = "gauge",
    help_text: str = ""
) -> str:
    """Format a metric in Prometheus exposition format."""
    lines = []
    
    # Add help text
    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    
    # Add type
    lines.append(f"# TYPE {name} {metric_type}")
    
    # Format labels
    if labels:
        label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
        lines.append(f"{name}{{{label_str}}} {value}")
    else:
        lines.append(f"{name} {value}")
    
    return "\n".join(lines)


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns application metrics in Prometheus exposition format for scraping.
    Includes:
    - HTTP request metrics
    - Search operation metrics
    - Alert processing metrics
    - Cost monitoring metrics
    - Health check status metrics
    """
    try:
        lines = []
        
        # Get metrics from the last hour
        since = datetime.utcnow() - timedelta(hours=1)
        all_metrics = metrics_collector.get_metrics(since=since)
        
        # Group metrics by name for aggregation
        metric_groups: Dict[str, List] = {}
        for metric in all_metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
        
        # Process each metric group
        for metric_name, metric_list in metric_groups.items():
            if not metric_list:
                continue
            
            # Determine metric type based on name
            if "_total" in metric_name or "_count" in metric_name:
                metric_type = "counter"
                help_text = f"Total count of {metric_name.replace('_total', '').replace('_count', '')}"
            elif "_duration_ms" in metric_name or "_size_bytes" in metric_name:
                metric_type = "histogram"
                help_text = f"Histogram of {metric_name}"
            else:
                metric_type = "gauge"
                help_text = f"Current value of {metric_name}"
            
            # For counters, sum all values
            if metric_type == "counter":
                # Group by labels and sum values
                label_groups: Dict[str, float] = {}
                for metric in metric_list:
                    label_key = ",".join([f'{k}="{v}"' for k, v in sorted(metric.labels.items())])
                    if label_key not in label_groups:
                        label_groups[label_key] = 0
                    label_groups[label_key] += metric.value
                
                # Output aggregated counters
                for label_key, total_value in label_groups.items():
                    if label_key:
                        # Parse labels back
                        labels = {}
                        for pair in label_key.split(","):
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                labels[k] = v.strip('"')
                        lines.append(format_prometheus_metric(
                            metric_name, total_value, labels, metric_type, help_text
                        ))
                    else:
                        lines.append(format_prometheus_metric(
                            metric_name, total_value, {}, metric_type, help_text
                        ))
            
            # For histograms, create buckets and summary stats
            elif metric_type == "histogram":
                # Group by labels
                label_groups: Dict[str, List[float]] = {}
                for metric in metric_list:
                    label_key = ",".join([f'{k}="{v}"' for k, v in sorted(metric.labels.items())])
                    if label_key not in label_groups:
                        label_groups[label_key] = []
                    label_groups[label_key].append(metric.value)
                
                # Create histogram buckets
                buckets = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, float("inf")]
                
                for label_key, values in label_groups.items():
                    if not values:
                        continue
                    
                    # Parse labels
                    labels = {}
                    if label_key:
                        for pair in label_key.split(","):
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                labels[k] = v.strip('"')
                    
                    # Create histogram buckets
                    base_name = metric_name.replace("_duration_ms", "").replace("_size_bytes", "")
                    
                    # Bucket counts
                    for bucket in buckets:
                        count = sum(1 for v in values if v <= bucket)
                        bucket_labels = {**labels, "le": str(bucket) if bucket != float("inf") else "+Inf"}
                        lines.append(format_prometheus_metric(
                            f"{base_name}_bucket", count, bucket_labels, "counter"
                        ))
                    
                    # Total count
                    lines.append(format_prometheus_metric(
                        f"{base_name}_count", len(values), labels, "counter"
                    ))
                    
                    # Sum
                    lines.append(format_prometheus_metric(
                        f"{base_name}_sum", sum(values), labels, "counter"
                    ))
            
            # For gauges, use the latest value for each label combination
            else:
                # Group by labels and use latest value
                label_groups: Dict[str, float] = {}
                for metric in metric_list:
                    label_key = ",".join([f'{k}="{v}"' for k, v in sorted(metric.labels.items())])
                    label_groups[label_key] = metric.value  # Latest value wins
                
                # Output gauges
                for label_key, value in label_groups.items():
                    if label_key:
                        # Parse labels back
                        labels = {}
                        for pair in label_key.split(","):
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                labels[k] = v.strip('"')
                        lines.append(format_prometheus_metric(
                            metric_name, value, labels, metric_type, help_text
                        ))
                    else:
                        lines.append(format_prometheus_metric(
                            metric_name, value, {}, metric_type, help_text
                        ))
        
        # Add health check metrics
        try:
            health_checks = await health_checker.run_all_checks()
            
            lines.append(format_prometheus_metric(
                "observastack_health_check_status",
                0,  # Placeholder, will be overwritten
                {},
                "gauge",
                "Health check status (1=healthy, 0.5=degraded, 0=unhealthy)"
            ))
            
            for service_name, health_check in health_checks.items():
                status_value = {
                    HealthStatus.HEALTHY: 1.0,
                    HealthStatus.DEGRADED: 0.5,
                    HealthStatus.UNHEALTHY: 0.0
                }[health_check.status]
                
                lines.append(format_prometheus_metric(
                    "observastack_health_check_status",
                    status_value,
                    {"service": service_name}
                ))
                
                # Add response time metric if available
                if health_check.response_time_ms is not None:
                    lines.append(format_prometheus_metric(
                        "observastack_health_check_duration_ms",
                        health_check.response_time_ms,
                        {"service": service_name},
                        "gauge",
                        "Health check response time in milliseconds"
                    ))
        
        except Exception as e:
            logger.warning(f"Failed to include health check metrics: {e}")
        
        # Add application info metric
        lines.append(format_prometheus_metric(
            "observastack_info",
            1,
            {
                "version": "1.0.0",
                "environment": "development"
            },
            "gauge",
            "ObservaStack application information"
        ))
        
        # Add timestamp
        lines.append(format_prometheus_metric(
            "observastack_metrics_timestamp",
            datetime.utcnow().timestamp(),
            {},
            "gauge",
            "Timestamp when metrics were generated"
        ))
        
        metrics_content = "\n".join(lines) + "\n"
        
        return PlainTextResponse(
            content=metrics_content,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        logger.error("Failed to generate Prometheus metrics", exc_info=True)
        return PlainTextResponse(
            content="# Error generating metrics\n",
            status_code=500,
            media_type="text/plain"
        )