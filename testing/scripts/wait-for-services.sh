#!/bin/bash
set -e

echo "Waiting for services to be ready..."

# Function to wait for a PostgreSQL service
wait_for_postgres() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose -f docker-compose.test.yml exec -T "$host" pg_isready -h localhost -p "$port" >/dev/null 2>&1; then
            echo "$service_name is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Function to wait for a generic service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        # Try both internal Docker network and localhost
        if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null || \
           timeout 5 bash -c "</dev/tcp/localhost/$port" 2>/dev/null || \
           curl -s --connect-timeout 5 "$host:$port" >/dev/null 2>&1 || \
           curl -s --connect-timeout 5 "localhost:$port" >/dev/null 2>&1; then
            echo "$service_name is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Wait for core services
wait_for_postgres "postgres" "5432" "PostgreSQL"
wait_for_postgres "test-results-db" "5432" "Test Results Database"
wait_for_service "backend" "8000" "Backend API"
wait_for_service "frontend" "3000" "Frontend"

# Additional health checks
echo "Performing health checks..."

# Check backend health endpoint - try both internal and external URLs
max_attempts=10
attempt=1
while [ $attempt -le $max_attempts ]; do
    # Try internal Docker network first, then localhost
    if curl -f http://backend:8000/api/v1/health >/dev/null 2>&1 || \
       curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        echo "Backend health check passed!"
        break
    fi
    echo "Backend health check attempt $attempt/$max_attempts failed..."
    sleep 3
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "ERROR: Backend health check failed"
    exit 1
fi

echo "All services are ready!"