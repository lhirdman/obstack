# Multi-stage Dockerfile for ObservaStack Backend (BFF)
# Supports development, testing, and production environments

# Base stage with common system dependencies
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Development stage with debugging and test tools
FROM base AS development

# Install development and test dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    pytest-cov==6.0.0 \
    pytest-xdist==3.6.0 \
    pytest-mock==3.14.0 \
    black==24.10.0 \
    ruff==0.8.4 \
    mypy==1.13.0 \
    debugpy==1.8.9 \
    ipdb==0.13.13 \
    rich==13.9.4

# Copy source code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app
USER appuser

# Expose ports (8000 for app, 5678 for debugger)
EXPOSE 8000 5678

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with auto-reload and debugging
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# Test stage for running comprehensive tests
FROM development AS test

# Set test environment variables
ENV TESTING=1 \
    PYTEST_CURRENT_TEST=1

# Run code quality checks
RUN python -m ruff check . --output-format=github
RUN python -m black --check --diff .
RUN python -m mypy app/ --ignore-missing-imports

# Run tests with coverage
RUN python -m pytest \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=80 \
    --maxfail=1 \
    -v \
    tests/

# Production build stage
FROM base AS build

# Install only production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app ./app

# Production stage
FROM python:3.12-slim AS production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=build /app .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with optimized settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log", "--log-level", "info"]
