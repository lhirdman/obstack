from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json, asyncio
import os
from redis import Redis

from .models import *
from .models.search import CorrelationRequest, CorrelationResponse
from .exceptions import *
from .exceptions import SearchException
from .error_handlers import setup_error_handlers
from .auth import JWTAuthMiddleware, get_current_user, get_current_tenant, JWTHandler
from .auth.service import AuthService
from .auth.models import UserContext
from .services import SearchService, LokiClient, PrometheusClient, TempoClient, AlertService
from .api.v1.alerts import router as alerts_router
from .api.v1.insights import router as insights_router
from .api.v1.costs import router as costs_router
from .api.v1.grafana import router as grafana_router
from .api.v1.tenants import router as tenants_router
from .api.v1.health import router as health_router
from .api.v1.metrics import router as metrics_router
from .middleware.monitoring import MonitoringMiddleware, MetricsMiddleware
from .core.logging import setup_logging, get_logger
from .core.monitoring import register_default_health_checks

# Setup logging first
setup_logging()
logger = get_logger("main")

app = FastAPI(
    title="ObservaStack BFF",
    version="0.1.0",
    description="Backend-for-Frontend API for ObservaStack unified observability platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Register health checks
register_default_health_checks()
logger.info("ObservaStack BFF starting up")

# Setup monitoring middleware
app.add_middleware(MonitoringMiddleware)
app.add_middleware(MetricsMiddleware)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client (optional)
redis_client = None
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()  # Test connection
except Exception as e:
    print(f"Redis connection failed: {e}. Session management will be disabled.")
    redis_client = None

# Initialize JWT handler and auth service
jwt_handler = JWTHandler()
auth_service = AuthService(jwt_handler=jwt_handler, redis_client=redis_client)

# Initialize search service with data source clients
loki_client = LokiClient(base_url=os.getenv("LOKI_URL", "http://localhost:3100"))
prometheus_client = PrometheusClient(base_url=os.getenv("PROMETHEUS_URL", "http://localhost:9090"))
tempo_client = TempoClient(base_url=os.getenv("TEMPO_URL", "http://localhost:3200"))
search_service = SearchService(
    loki_client=loki_client,
    prometheus_client=prometheus_client,
    tempo_client=tempo_client
)

# Add JWT authentication middleware with webhook exclusions
webhook_exclude_paths = [
    "/api/docs",
    "/api/redoc", 
    "/api/openapi.json",
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/jwks",
    "/api/meta/flags",
    "/health",
    "/metrics",
    "/api/v1/alerts/webhook/alertmanager",
    "/api/v1/alerts/webhook/generic"
]
app.add_middleware(JWTAuthMiddleware, jwt_handler=jwt_handler, exclude_paths=webhook_exclude_paths)

# Setup error handlers
setup_error_handlers(app)

# Include API routers
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(costs_router, prefix="/api/v1")
app.include_router(grafana_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(metrics_router)

# Startup handler
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("ObservaStack BFF startup complete")

# Cleanup handler
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    logger.info("ObservaStack BFF shutting down")
    await search_service.close()
    logger.info("ObservaStack BFF shutdown complete")

@app.get("/health")
async def health_check():
    """
    Health check endpoint for container health monitoring.
    
    Returns:
        Health status of the application and its dependencies
    """
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    # Check Redis connection if available
    if redis_client:
        try:
            redis_client.ping()
            health_status["redis"] = "connected"
        except Exception:
            health_status["redis"] = "disconnected"
            health_status["status"] = "degraded"
    else:
        health_status["redis"] = "not_configured"
    
    # Check search service health
    try:
        search_health = await search_service.health_check()
        health_status["search_services"] = search_health
        
        # If no search services are healthy, mark as unhealthy
        if not any(search_health.values()):
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["search_services"] = {"error": str(e)}
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/api/meta/flags")
def flags():
    return {"edition":"community","features":{"sso":False,"opensearch":False,"cost_insights":False}}

@app.post("/api/auth/login", response_model=AuthTokens)
async def login(req: LoginRequest) -> AuthTokens:
    """Authenticate user and return JWT tokens."""
    return await auth_service.authenticate_user(req)

@app.post("/api/auth/refresh", response_model=AuthTokens)
async def refresh(req: RefreshTokenRequest) -> AuthTokens:
    """Refresh access token using refresh token."""
    return await auth_service.refresh_tokens(req)

@app.post("/api/auth/logout")
async def logout(
    req: LogoutRequest,
    current_user: UserContext = Depends(get_current_user)
) -> dict:
    """Logout user and invalidate tokens."""
    await auth_service.logout(current_user, req.refresh_token)
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserContext = Depends(get_current_user)
) -> UserProfile:
    """Get current user profile information."""
    from datetime import datetime
    
    # TODO: Replace with actual user data from identity provider
    return UserProfile(
        id=current_user.user_id,
        username="demo-user",  # Would come from identity provider
        email="demo@example.com",  # Would come from identity provider
        tenant_id=current_user.tenant_id,
        roles=current_user.roles,
        created_at=datetime.now(),
        is_active=True
    )

@app.get("/api/auth/jwks", response_model=JWKSResponse)
def jwks() -> JWKSResponse:
    # Demo implementation - replace with actual JWKS
    return JWKSResponse(keys=[{"kty":"oct","kid":"demo","k":"not-a-real-key"}])

@app.post("/api/search", response_model=SearchResult)
async def search(
    query: SearchQuery,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> SearchResult:
    """
    Perform unified search across logs, metrics, and traces.
    
    Args:
        query: Search parameters including text, filters, and time range
        current_user: Authenticated user context for tenant isolation
        tenant_id: Tenant ID for data isolation
        
    Returns:
        SearchResult with items, stats, and facets
        
    Raises:
        HTTPException: 400 for invalid query, 403 for permissions, 500 for search errors
    """
    try:
        # Ensure query uses the correct tenant ID
        query.tenant_id = tenant_id
        
        # Perform unified search
        result = await search_service.search(query, tenant_id)
        
        return result
        
    except SearchException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal search error"
        )

@app.post("/api/search/stream")
async def search_stream(
    query: SearchQuery,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Perform streaming search with Server-Sent Events (SSE) for real-time results.
    
    Args:
        query: Search parameters including text, filters, and time range
        current_user: Authenticated user context for tenant isolation
        tenant_id: Tenant ID for data isolation
        
    Returns:
        StreamingResponse with SSE format for real-time search results
    """
    async def generate_search_stream():
        try:
            # Ensure query uses the correct tenant ID
            query.tenant_id = tenant_id
            
            # Send initial event
            yield f"event: search_started\n"
            yield f"data: {json.dumps({'status': 'started', 'query_id': query.tenant_id})}\n\n"
            
            # Stream search results from the service
            async for chunk in search_service.search_stream(query, tenant_id):
                yield f"event: search_chunk\n"
                yield f"data: {chunk.model_dump_json()}\n\n"
            
            # Send completion event
            yield f"event: search_completed\n"
            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
            
        except SearchException as e:
            # Send error event
            yield f"event: search_error\n"
            yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"
        except Exception as e:
            # Send unexpected error event
            yield f"event: search_error\n"
            yield f"data: {json.dumps({'error': 'Internal search error', 'status': 'error'})}\n\n"
    
    return StreamingResponse(
        generate_search_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.post("/api/search/correlate", response_model=CorrelationResponse)
async def correlate_signals(
    request: CorrelationRequest,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> CorrelationResponse:
    """
    Find correlated signals based on trace ID, correlation ID, or service.
    
    Args:
        request: Correlation request parameters
        current_user: Authenticated user context
        tenant_id: Tenant ID for data isolation
        
    Returns:
        CorrelationResponse with related items and correlation graph
    """
    try:
        response = await search_service.correlate_signals(request, tenant_id)
        return response
        
    except SearchException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Correlation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal correlation error"
        )

@app.get("/api/search/health")
async def search_health(current_user: UserContext = Depends(get_current_user)):
    """
    Check health status of all search data sources.
    
    Returns:
        Health status for each data source
    """
    try:
        health_status = await search_service.health_check()
        
        # Determine overall health
        overall_healthy = any(health_status.values())
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "sources": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@app.get("/api/search/stats")
async def search_statistics(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get search performance statistics and metrics.
    
    Returns:
        Search performance statistics for the tenant
    """
    try:
        stats = await search_service.get_search_statistics(tenant_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search statistics"
        )

@app.get("/api/search/metrics")
async def search_metrics(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get real-time search performance metrics.
    
    Returns:
        Real-time search performance metrics
    """
    try:
        metrics = await search_service.get_performance_metrics(tenant_id)
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search metrics"
        )

@app.post("/api/search/aggregate")
async def search_aggregate(
    query: SearchQuery,
    aggregation_type: str,
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Perform aggregated search with result grouping and statistics.
    
    Args:
        query: Search parameters
        aggregation_type: Type of aggregation (time, service, source, etc.)
        current_user: Authenticated user context
        tenant_id: Tenant ID for data isolation
        
    Returns:
        Aggregated search results with statistics
    """
    try:
        # Ensure query uses the correct tenant ID
        query.tenant_id = tenant_id
        
        # Perform aggregated search
        result = await search_service.search_aggregate(query, aggregation_type, tenant_id)
        
        return result
        
    except SearchException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Aggregated search failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal aggregation error"
        )

@app.get("/api/alerts", response_model=AlertsResponse)
def alerts(
    current_user: UserContext = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> AlertsResponse:
    # Demo implementation - replace with actual alerts logic
    from datetime import datetime
    
    demo_alerts = [
        Alert(
            id="a1",
            severity=SeverityLevel.HIGH,
            title="CPU saturation",
            description="CPU usage is above 90% for more than 5 minutes",
            source=AlertSource.PROMETHEUS,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            fingerprint="cpu-saturation-fingerprint",
            starts_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        Alert(
            id="a2",
            severity=SeverityLevel.MEDIUM,
            title="Error rate spike",
            description="Error rate increased to 5% in the last 10 minutes",
            source=AlertSource.LOKI,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            fingerprint="error-rate-spike-fingerprint",
            starts_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    return AlertsResponse(alerts=demo_alerts, total=len(demo_alerts))
