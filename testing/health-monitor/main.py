#!/usr/bin/env python3
"""
Health Monitor Service for ObservaStack Test Environment

Monitors the health of all services in the test stack and provides
a centralized health status endpoint.
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import contextlib
import httpx
import schedule
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SERVICES_TO_MONITOR = os.getenv("SERVICES_TO_MONITOR", "").split(",")
DATABASE_URLS_TO_MONITOR = os.getenv("DATABASE_URLS_TO_MONITOR", "").split(",")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

# global registry + metrics
REGISTRY = CollectorRegistry()

# Health status storage
health_status: Dict[str, Dict] = {}
scheduler_task: Optional[asyncio.Task] = None

# --- Specific Health Endpoints for Services ---
SERVICE_HEALTH_ENDPOINTS = {
    "frontend": ["/health", "/"],
    "backend": ["/health", "/api/v1/health", "/"],
    "prometheus": ["/-/healthy"],
    "loki": ["/ready"],
    "tempo": ["/ready"],
    "grafana": ["/api/health"],
    "keycloak": ["/health/ready"],
    "alertmanager": ["/-/ready"],
    "thanos-query": ["/-/healthy"],
    "otel-collector": ["/health"],
    "opensearch": ["/_cluster/health"],
    "redpanda": ["/v1/status/ready", "/v1/cluster/health_overview"],
    "default": ["/health", "/api/health", "/"],
}


class ServiceHealth(BaseModel):
    service: str
    status: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class OverallHealth(BaseModel):
    status: str
    services: List[ServiceHealth]
    last_updated: datetime


def build_metrics():
    """Return (registry, gauges, update_fn) without using module globals."""
    registry = CollectorRegistry()
    g_up = Gauge("health_service_up", "Service health (1=healthy,0=down)", ["service"], registry=registry)
    g_rt = Gauge("health_service_response_ms", "Service health check response time (ms)", ["service"], registry=registry)

    def update_metrics(snapshot: Dict[str, Dict[str, Any]]) -> None:
        # snapshot has shape {service: {"status": "...", "response_time_ms": float, ...}}
        for svc, s in snapshot.items():
            g_up.labels(service=svc).set(1.0 if s.get("status") == "healthy" else 0.0)
            rt = s.get("response_time_ms")
            g_rt.labels(service=svc).set(float(rt) if rt is not None else 0.0)

    return registry, {"up": g_up, "rt": g_rt}, update_metrics


# add alongside other specialized checks
async def check_opensearch_health(service_name: str, port: int) -> ServiceHealth:
    """
    OpenSearch health: GET /_cluster/health and consider green/yellow healthy.
    Supports optional basic auth via OPENSEARCH_USER / OPENSEARCH_PASSWORD env vars.
    """
    url = f"http://{service_name}:{port}/_cluster/health"
    auth = None
    user = os.getenv("OPENSEARCH_USER")
    pwd = os.getenv("OPENSEARCH_PASSWORD")
    if user and pwd:
        auth = (user, pwd)

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=10.0, verify=True, auth=auth) as client:
            resp = await client.get(url)
        rt_ms = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            status = (data.get("status") or "").lower()
            if status in ("green", "yellow"):
                return ServiceHealth(service=service_name, status="healthy",
                                     last_check=datetime.now(), response_time_ms=rt_ms)
            else:
                return ServiceHealth(service=service_name, status="unhealthy",
                                     last_check=datetime.now(),
                                     error_message=f"cluster status={status!r}",
                                     response_time_ms=rt_ms)
        elif resp.status_code in (401, 403):
            return ServiceHealth(service=service_name, status="unhealthy",
                                 last_check=datetime.now(),
                                 error_message=f"{resp.status_code} auth required for {url}")
        else:
            return ServiceHealth(service=service_name, status="unhealthy",
                                 last_check=datetime.now(),
                                 error_message=f"HTTP {resp.status_code} from {url}")
    except Exception as e:
        return ServiceHealth(service=service_name, status="error",
                             last_check=datetime.now(), error_message=str(e))


async def check_redis_health(service_name: str, port: int) -> ServiceHealth:
    """
    Minimal Redis health: open TCP, send RESP PING, accept +PONG or -NOAUTH as 'alive'.
    Avoids HTTP entirely so Redis won't log SECURITY ATTACK warnings.
    """
    try:
        start_time = time.time()
        reader, writer = await asyncio.open_connection(service_name, port)
        try:
            # RESP for: *1\r\n$4\r\nPING\r\n
            writer.write(b"*1\r\n$4\r\nPING\r\n")
            await writer.drain()
            data = await asyncio.wait_for(reader.readline(), timeout=2.0)
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

        # Accept either +PONG or -NOAUTH ... both prove Redis responded
        if data.startswith(b"+PONG") or data.startswith(b"-NOAUTH"):
            rt = (time.time() - start_time) * 1000
            return ServiceHealth(service=service_name, status="healthy", last_check=datetime.now(), response_time_ms=rt)

        return ServiceHealth(
            service=service_name,
            status="unhealthy",
            last_check=datetime.now(),
            error_message=f"Unexpected Redis reply: {data[:64]!r}",
        )
    except Exception as e:
        return ServiceHealth(service=service_name, status="error", last_check=datetime.now(), error_message=str(e))


async def check_service_health(service_config: str) -> ServiceHealth:
    """Check health of a single service via HTTP using specific endpoints."""
    service_name, port_str = service_config.strip().split(":")
    port = int(port_str)

    # Special-case: OpenSearch
    if service_name.lower() in {"opensearch", "elasticsearch"} or port == 9200:
        return await check_opensearch_health(service_name, port)

    # Special-case: Redis
    if service_name.lower() in {"redis", "keydb", "dragonfly"} or port == 6379:
        return await check_redis_health(service_name, port)

    url = f"http://{service_name}:{port}"
    endpoints = SERVICE_HEALTH_ENDPOINTS.get(service_name, SERVICE_HEALTH_ENDPOINTS["default"])
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{url}{endpoint}")
                    if response.status_code < 400:
                        response_time = (time.time() - start_time) * 1000
                        return ServiceHealth(
                            service=service_name,
                            status="healthy",
                            last_check=datetime.now(),
                            response_time_ms=response_time,
                        )
                except httpx.RequestError as e:
                    logger.warning(f"Request to {url}{endpoint} failed: {e}")
                    continue
        
        error_message = f"All configured health endpoints failed: {endpoints}"
        logger.error(f"Health check for {service_name} failed. {error_message}")
        return ServiceHealth(
            service=service_name,
            status="unhealthy",
            last_check=datetime.now(),
            error_message=error_message,
        )
    except Exception as e:
        logger.error(f"Unexpected error checking {service_config}: {str(e)}")
        return ServiceHealth(
            service=service_config,
            status="error",
            last_check=datetime.now(),
            error_message=str(e),
        )


async def check_database_health(db_config: str) -> ServiceHealth:
    """Check a single database connectivity."""
    service_name, db_url = db_config.strip().split("|")
    try:
        start_time = time.time()
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            service=service_name,
            status="healthy",
            last_check=datetime.now(),
            response_time_ms=response_time,
        )
    except SQLAlchemyError as e:
        logger.error(f"Database health check for {service_name} failed: {str(e)}")
        return ServiceHealth(
            service=service_name,
            status="unhealthy",
            last_check=datetime.now(),
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error checking database {service_name}: {str(e)}")
        return ServiceHealth(
            service=service_name,
            status="error",
            last_check=datetime.now(),
            error_message=str(e),
        )


async def perform_health_checks(update_fn: Optional[Callable[[Dict[str, Dict[str, Any]]], None]] = None):
    """Perform health checks on all monitored services."""
    logger.info("Performing health checks...")
    tasks = []
    for service_config in SERVICES_TO_MONITOR:
        if service_config.strip():
            tasks.append(check_service_health(service_config))
    for db_config in DATABASE_URLS_TO_MONITOR:
        if db_config.strip():
            tasks.append(check_database_health(db_config))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    global health_status
    health_status.clear()
    for result in results:
        if isinstance(result, ServiceHealth):
            health_status[result.service] = result.dict()
        else:
            logger.error(f"Health check failed with exception: {result}")
    healthy_count = len([s for s in health_status.values() if s['status'] == 'healthy'])
    logger.info(f"Health checks completed. Status: {healthy_count}/{len(health_status)} services healthy")
    # push into metrics if a callback was provided
    if update_fn is not None:
        try:
            update_fn(health_status)
        except Exception as e:
            logger.warning(f"Failed to update metrics: {e}")

async def run_scheduler(app: FastAPI):
    """Run the scheduled health checks."""
    schedule.every(CHECK_INTERVAL).seconds.do(
        lambda: asyncio.create_task(perform_health_checks(update_fn=getattr(app.state, 'update_metrics', None)))
    )
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting Health Monitor Service")

    # NEW: build registry+gauges and keep them on app.state
    registry, gauges, update_fn = build_metrics()
    app.state.metrics_registry = registry
    app.state.update_metrics = update_fn
    app.state.metrics_gauges = gauges

    # first run updates JSON and metrics
    await perform_health_checks(update_fn=app.state.update_metrics)

    global scheduler_task
    scheduler_task = asyncio.create_task(run_scheduler(app))
    yield

    logger.info("Shutting down Health Monitor Service")
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled successfully.")

app = FastAPI(title="ObservaStack Health Monitor", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=OverallHealth)
async def get_health():
    """Get overall health status of all monitored services."""
    if not health_status:
        # also update metrics on first on-demand run
        await perform_health_checks(update_fn=getattr(app.state, "update_metrics", None))
    services = [ServiceHealth(**status) for status in health_status.values()]
    if all(service.status == "healthy" for service in services):
        overall_status = "healthy"
    elif any(service.status == "healthy" for service in services):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    return OverallHealth(
        status=overall_status, services=services, last_updated=datetime.now()
    )


@app.get("/health/{service_name}")
async def get_service_health(service_name: str):
    """Get health status of a specific service."""
    if service_name not in health_status:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    return health_status[service_name]


@app.get("/metrics")
async def metrics():
    reg = getattr(app.state, "metrics_registry", None)
    if reg is None:
        # Build on-demand if not present (shouldn’t happen in normal flow)
        reg, _, _ = build_metrics()
        app.state.metrics_registry = reg
    return Response(generate_latest(reg), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
