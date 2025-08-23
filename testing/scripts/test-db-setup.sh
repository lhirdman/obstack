#!/bin/bash

# Test script to verify database setup
echo "Testing database setup..."

# Wait for postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker compose -f testing/docker-compose.test.yml exec postgres pg_isready -U observastack -d observastack; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Test observastack database
echo "Testing observastack database..."
docker compose -f testing/docker-compose.test.yml exec postgres psql -U observastack -d observastack -c "SELECT current_database(), current_user;"

# Test keycloak database
echo "Testing keycloak database..."
docker compose -f testing/docker-compose.test.yml exec postgres psql -U keycloak -d keycloak -c "SELECT current_database(), current_user;"

# List all databases
echo "Listing all databases..."
docker compose -f testing/docker-compose.test.yml exec postgres psql -U observastack -c "\l"

# List all users
echo "Listing all users..."
docker compose -f testing/docker-compose.test.yml exec postgres psql -U observastack -c "\du"

echo "Database setup test completed!"