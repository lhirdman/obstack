-- Database initialization script for ObservaStack
-- This script creates the necessary databases and users for the application

-- Create keycloak database if it doesn't exist
SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec

-- Create keycloak user if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'keycloak') THEN

      CREATE ROLE keycloak LOGIN PASSWORD 'keycloak';
   END IF;
END
$do$;

-- Grant privileges to keycloak user on keycloak database
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;

-- Connect to keycloak database and grant schema privileges
\c keycloak;
GRANT ALL ON SCHEMA public TO keycloak;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO keycloak;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO keycloak;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO keycloak;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO keycloak;

-- Switch back to the default database
\c observastack;

-- Ensure observastack user has proper privileges on observastack database
GRANT ALL PRIVILEGES ON DATABASE observastack TO observastack;
GRANT ALL ON SCHEMA public TO observastack;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO observastack;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO observastack;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO observastack;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO observastack;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Switch to keycloak database and create extensions there too
\c keycloak;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Final message
\echo 'Database initialization completed successfully!'