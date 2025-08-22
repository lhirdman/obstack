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
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import schedule
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ObservaStack Health Monitor", version="1.0.0")

# Configuration
SERVICES_TO_MONITOR = os.getenv("SERVICES_TO_MONITOR", "").split(",")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
HEALTH_DB_URL = os.getenv("HEALTH_DB_URL")

# Health status storage
health_status: Dict[str, Dict] = {}


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


async def check_service_health(service_config: str) -> ServiceHealth:
    """Check health of a single service."""
    try:
        service_name, port = service_config.strip().split(":")
        url = f"http://{service_name}:{port}"
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try health endpoint first, fallback to root
            health_endpoints = ["/health", "/api/health", "/"]
            
            for endpoint in health_endpoints:
                try:
                    response = await client.get(f"{url}{endpoint}")
                    if response.status_code < 400:
                        response_time = (time.time() - start_time) * 1000
                        return ServiceHealth(
                            service=service_name,
                            status="healthy",
                            last_check=datetime.now(),
                            response_time_ms=response_time
                        )
                except httpx.RequestError:
                    continue
            
            # If all endpoints failed
            return ServiceHealth(
                service=service_name,
                status="unhealthy",
                last_check=datetime.now(),
                error_message="All health endpoints failed"
            )
            
    except Exception as e:
        logger.error(f"Error checking {service_config}: {str(e)}")
        return ServiceHealth(
            service=service_config,
            status="error",
            last_check=datetime.now(),
            error_message=str(e)
        )


async def check_database_health() -> ServiceHealth:
    """Check database connectivity."""
    try:
        if not HEALTH_DB_URL:
            return ServiceHealth(
                service="test-results-db",
                status="error",
                last_check=datetime.now(),
                error_message="Database URL not configured"
            )
        
        start_time = time.time()
        engine = create_engine(HEALTH_DB_URL)
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealth(
            service="test-results-db",
            status="healthy",
            last_check=datetime.now(),
            response_time_ms=response_time
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {str(e)}")
        return ServiceHealth(
            service="test-results-db",
            status="unhealthy",
            last_check=datetime.now(),
            error_message=str(e)
        )


async def perform_health_checks():
    """Perform health checks on all monitored services."""
    logger.info("Performing health checks...")
    
    # Check configured services
    tasks = []
    for service_config in SERVICES_TO_MONITOR:
        if service_config.strip():
            tasks.append(check_service_health(service_config))
    
    # Check database
    tasks.append(check_database_health())
    
    # Execute all checks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Update health status
    global health_status
    health_status.clear()
    
    for result in results:
        if isinstance(result, ServiceHealth):
            health_status[result.service] = result.dict()
        else:
            logger.error(f"Health check failed with exception: {result}")
    
    logger.info(f"Health checks completed. Status: {len([s for s in health_status.values() if s['status'] == 'healthy'])}/{len(health_status)} services healthy")


@app.get("/health", response_model=OverallHealth)
async def get_health():
    """Get overall health status of all monitored services."""
    if not health_status:
        await perform_health_checks()
    
    services = [ServiceHealth(**status) for status in health_status.values()]
    
    # Determine overall status
    if all(service.status == "healthy" for service in services):
        overall_status = "healthy"
    elif any(service.status == "healthy" for service in services):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return OverallHealth(
        status=overall_status,
        services=services,
        last_updated=datetime.now()
    )


@app.get("/health/{service_name}")
async def get_service_health(service_name: str):
    """Get health status of a specific service."""
    if service_name not in health_status:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    return health_status[service_name]


@app.on_event("startup")
async def startup_event():
    """Initialize health monitoring on startup."""
    logger.info("Starting Health Monitor Service")
    logger.info(f"Monitoring services: {SERVICES_TO_MONITOR}")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    
    # Perform initial health check
    await perform_health_checks()
    
    # Schedule periodic health checks
    schedule.every(CHECK_INTERVAL).seconds.do(lambda: asyncio.create_task(perform_health_checks()))


async def run_scheduler():
    """Run the scheduled health checks."""
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


if __name__ == "__main__":
    import uvicorn
    
    # Start the scheduler in the background
    asyncio.create_task(run_scheduler())
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8080)