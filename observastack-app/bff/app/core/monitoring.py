"""Monitoring and health check utilities for ObservaStack BFF."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import httpx
from contextlib import asynccontextmanager

from .logging import get_logger
from .config import get_settings

logger = get_logger("monitoring")


class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


class HealthChecker:
    """Health check manager for monitoring service dependencies."""
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], Awaitable[HealthCheck]]] = {}
        self.settings = get_settings()
    
    def register_check(self, name: str, check_func: Callable[[], Awaitable[HealthCheck]]) -> None:
        """Register a health check function."""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check '{name}' not found"
            )
        
        try:
            start_time = time.time()
            result = await self.checks[name]()
            result.response_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            logger.exception(f"Health check '{name}' failed")
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000 if 'start_time' in locals() else None
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        results = {}
        
        # Run checks concurrently
        tasks = {name: self.run_check(name) for name in self.checks}
        completed = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for name, result in zip(tasks.keys(), completed):
            if isinstance(result, Exception):
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check exception: {str(result)}"
                )
            else:
                results[name] = result
        
        return results
    
    async def get_overall_health(self) -> HealthCheck:
        """Get overall system health status."""
        checks = await self.run_all_checks()
        
        if not checks:
            return HealthCheck(
                name="overall",
                status=HealthStatus.HEALTHY,
                message="No health checks configured"
            )
        
        # Determine overall status
        statuses = [check.status for check in checks.values()]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
            message = "All services healthy"
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
            unhealthy_services = [
                name for name, check in checks.items() 
                if check.status == HealthStatus.UNHEALTHY
            ]
            message = f"Unhealthy services: {', '.join(unhealthy_services)}"
        else:
            overall_status = HealthStatus.DEGRADED
            degraded_services = [
                name for name, check in checks.items() 
                if check.status == HealthStatus.DEGRADED
            ]
            message = f"Degraded services: {', '.join(degraded_services)}"
        
        return HealthCheck(
            name="overall",
            status=overall_status,
            message=message,
            details={"checks": {name: check.status.value for name, check in checks.items()}}
        )


class MetricsCollector:
    """Metrics collection and reporting."""
    
    def __init__(self):
        self.metrics: List[MetricPoint] = []
        self.max_metrics = 10000  # Keep last 10k metrics in memory
        self.settings = get_settings()
    
    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ) -> None:
        """Record a metric point."""
        metric = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            unit=unit
        )
        
        self.metrics.append(metric)
        
        # Trim old metrics if we exceed the limit
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
        
        logger.debug(f"Recorded metric: {name}={value} {unit}", extra={
            "metric": {
                "name": name,
                "value": value,
                "labels": labels,
                "unit": unit
            }
        })
    
    def increment_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        value: float = 1.0
    ) -> None:
        """Increment a counter metric."""
        self.record_metric(f"{name}_total", value, labels, "count")
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ) -> None:
        """Record a histogram metric (duration, size, etc.)."""
        self.record_metric(name, value, labels, unit)
    
    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ) -> None:
        """Record a gauge metric (current value)."""
        self.record_metric(name, value, labels, unit)
    
    def get_metrics(
        self,
        name_filter: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """Get collected metrics with optional filtering."""
        filtered_metrics = self.metrics
        
        if name_filter:
            filtered_metrics = [m for m in filtered_metrics if name_filter in m.name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= since]
        
        return filtered_metrics
    
    def get_metric_summary(self, name: str, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        metrics = [m for m in self.get_metrics(name, since) if m.name == name]
        
        if not metrics:
            return {"count": 0}
        
        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "latest_timestamp": metrics[-1].timestamp.isoformat()
        }


# Global instances
health_checker = HealthChecker()
metrics_collector = MetricsCollector()


# Built-in health checks
async def check_redis_health() -> HealthCheck:
    """Check Redis connectivity."""
    try:
        from redis import Redis
        settings = get_settings()
        
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        start_time = time.time()
        redis_client.ping()
        response_time = (time.time() - start_time) * 1000
        
        return HealthCheck(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis connection successful",
            response_time_ms=response_time
        )
    except Exception as e:
        return HealthCheck(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis connection failed: {str(e)}"
        )


async def check_prometheus_health() -> HealthCheck:
    """Check Prometheus connectivity."""
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.prometheus_url}/-/healthy")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheck(
                    name="prometheus",
                    status=HealthStatus.HEALTHY,
                    message="Prometheus is healthy",
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    name="prometheus",
                    status=HealthStatus.DEGRADED,
                    message=f"Prometheus returned status {response.status_code}",
                    response_time_ms=response_time
                )
    except Exception as e:
        return HealthCheck(
            name="prometheus",
            status=HealthStatus.UNHEALTHY,
            message=f"Prometheus health check failed: {str(e)}"
        )


async def check_loki_health() -> HealthCheck:
    """Check Loki connectivity."""
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.loki_url}/ready")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheck(
                    name="loki",
                    status=HealthStatus.HEALTHY,
                    message="Loki is ready",
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    name="loki",
                    status=HealthStatus.DEGRADED,
                    message=f"Loki returned status {response.status_code}",
                    response_time_ms=response_time
                )
    except Exception as e:
        return HealthCheck(
            name="loki",
            status=HealthStatus.UNHEALTHY,
            message=f"Loki health check failed: {str(e)}"
        )


async def check_tempo_health() -> HealthCheck:
    """Check Tempo connectivity."""
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.tempo_url}/ready")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheck(
                    name="tempo",
                    status=HealthStatus.HEALTHY,
                    message="Tempo is ready",
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    name="tempo",
                    status=HealthStatus.DEGRADED,
                    message=f"Tempo returned status {response.status_code}",
                    response_time_ms=response_time
                )
    except Exception as e:
        return HealthCheck(
            name="tempo",
            status=HealthStatus.UNHEALTHY,
            message=f"Tempo health check failed: {str(e)}"
        )


async def check_grafana_health() -> HealthCheck:
    """Check Grafana connectivity."""
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.grafana_url}/api/health")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("database") == "ok":
                    return HealthCheck(
                        name="grafana",
                        status=HealthStatus.HEALTHY,
                        message="Grafana is healthy",
                        response_time_ms=response_time,
                        details=health_data
                    )
                else:
                    return HealthCheck(
                        name="grafana",
                        status=HealthStatus.DEGRADED,
                        message="Grafana database issues",
                        response_time_ms=response_time,
                        details=health_data
                    )
            else:
                return HealthCheck(
                    name="grafana",
                    status=HealthStatus.DEGRADED,
                    message=f"Grafana returned status {response.status_code}",
                    response_time_ms=response_time
                )
    except Exception as e:
        return HealthCheck(
            name="grafana",
            status=HealthStatus.UNHEALTHY,
            message=f"Grafana health check failed: {str(e)}"
        )


async def check_opencost_health() -> HealthCheck:
    """Check OpenCost connectivity."""
    settings = get_settings()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.opencost_url}/healthz")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheck(
                    name="opencost",
                    status=HealthStatus.HEALTHY,
                    message="OpenCost is healthy",
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    name="opencost",
                    status=HealthStatus.DEGRADED,
                    message=f"OpenCost returned status {response.status_code}",
                    response_time_ms=response_time
                )
    except Exception as e:
        return HealthCheck(
            name="opencost",
            status=HealthStatus.UNHEALTHY,
            message=f"OpenCost health check failed: {str(e)}"
        )


def register_default_health_checks() -> None:
    """Register all default health checks."""
    health_checker.register_check("redis", check_redis_health)
    health_checker.register_check("prometheus", check_prometheus_health)
    health_checker.register_check("loki", check_loki_health)
    health_checker.register_check("tempo", check_tempo_health)
    health_checker.register_check("grafana", check_grafana_health)
    health_checker.register_check("opencost", check_opencost_health)


@asynccontextmanager
async def monitor_performance(operation: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for monitoring operation performance."""
    start_time = time.time()
    labels = labels or {}
    
    try:
        yield
        # Record successful operation
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_histogram(
            f"{operation}_duration_ms",
            duration_ms,
            {**labels, "status": "success"},
            "milliseconds"
        )
        metrics_collector.increment_counter(
            f"{operation}_requests",
            {**labels, "status": "success"}
        )
    except Exception as e:
        # Record failed operation
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_histogram(
            f"{operation}_duration_ms",
            duration_ms,
            {**labels, "status": "error"},
            "milliseconds"
        )
        metrics_collector.increment_counter(
            f"{operation}_requests",
            {**labels, "status": "error"}
        )
        raise


def record_request_metrics(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    tenant_id: Optional[str] = None
) -> None:
    """Record HTTP request metrics."""
    labels = {
        "method": method,
        "path": path,
        "status_code": str(status_code),
        "status_class": f"{status_code // 100}xx"
    }
    
    if tenant_id:
        labels["tenant_id"] = tenant_id
    
    metrics_collector.record_histogram(
        "http_request_duration_ms",
        duration_ms,
        labels,
        "milliseconds"
    )
    
    metrics_collector.increment_counter(
        "http_requests",
        labels
    )


def record_search_metrics(
    search_type: str,
    result_count: int,
    duration_ms: float,
    tenant_id: str,
    success: bool = True
) -> None:
    """Record search operation metrics."""
    labels = {
        "search_type": search_type,
        "tenant_id": tenant_id,
        "status": "success" if success else "error"
    }
    
    metrics_collector.record_histogram(
        "search_duration_ms",
        duration_ms,
        labels,
        "milliseconds"
    )
    
    metrics_collector.record_gauge(
        "search_results_count",
        result_count,
        labels,
        "count"
    )
    
    metrics_collector.increment_counter(
        "search_requests",
        labels
    )


def record_alert_metrics(
    alert_source: str,
    severity: str,
    tenant_id: str,
    action: str = "received"
) -> None:
    """Record alert processing metrics."""
    labels = {
        "source": alert_source,
        "severity": severity,
        "tenant_id": tenant_id,
        "action": action
    }
    
    metrics_collector.increment_counter(
        "alerts_processed",
        labels
    )


def record_cost_metrics(
    operation: str,
    tenant_id: str,
    duration_ms: float,
    success: bool = True
) -> None:
    """Record cost monitoring metrics."""
    labels = {
        "operation": operation,
        "tenant_id": tenant_id,
        "status": "success" if success else "error"
    }
    
    metrics_collector.record_histogram(
        "cost_operation_duration_ms",
        duration_ms,
        labels,
        "milliseconds"
    )
    
    metrics_collector.increment_counter(
        "cost_operations",
        labels
    )