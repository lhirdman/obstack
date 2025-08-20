import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up ObservaStack API...")
    try:
        await init_db()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ObservaStack API...")


app = FastAPI(
    title="ObservaStack API",
    description="A unified observability platform API for metrics, logs, and traces",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url=None,  # Disable default Swagger UI
    redoc_url=None,  # We'll create custom Redocly endpoint
    lifespan=lifespan,
)

# Include API routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/api/docs", response_class=HTMLResponse, include_in_schema=False)
async def redocly_html():
    """Serve API documentation using Redocly."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
    )

@app.get("/")
def read_root():
    """Root endpoint returning basic service information."""
    return {"message": "Observastack Backend is running."}
