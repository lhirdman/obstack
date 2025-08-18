# Project Structure & Organization

## Repository Layout
This is a multi-repository project with distinct concerns:

### `/docker/` - Development Environment
Full-stack Docker Compose setup for local development and testing:
- `docker-compose.yml` - Complete observability stack
- `prometheus/` - Prometheus configs and alerting rules
- `grafana-provisioning/` - Grafana datasources and dashboards
- `dashboards/` - Pre-built Grafana dashboard JSON files
- Service configs: `loki-config.yaml`, `tempo-config.yaml`, `vector-aggregator.toml`

### `/observastack/` - Production Deployment
Infrastructure-as-code for production deployments:
- `install/ansible/` - Ansible playbooks and roles for deployment
- `install/compose/` - Production Docker Compose variant
- `install/helm/` - Kubernetes Helm charts
- `config/` - Configuration templates and rule packs

### `/observastack-app/` - Application Monorepo
Main application code organized as a monorepo:
- `frontend/` - React/TypeScript UI shell
- `bff/` - FastAPI backend-for-frontend
- `contracts/` - OpenAPI specifications
- `e2e/` - End-to-end test suites

## Key Architectural Patterns

### Monorepo Structure
The `observastack-app/` follows monorepo conventions:
- Shared contracts via OpenAPI specs
- Independent build/deploy cycles per service
- Common development tooling and standards

### Configuration Management
- Environment-specific configs in respective deployment folders
- Template-based configuration with variable substitution
- Separation of secrets from configuration files

### Multi-tenant Architecture
- Tenant isolation at multiple layers (UI, API, datasource)
- RBAC enforcement through Keycloak integration
- Tenant-specific branding and customization support

## File Naming Conventions
- Ansible: `main.yml` for role tasks, kebab-case for playbooks
- Docker: `docker-compose.yml` (not .yaml), service-specific config files
- Frontend: PascalCase for React components, camelCase for utilities
- Backend: snake_case for Python modules, kebab-case for config files
- Configs: `.yml` for Ansible/Kubernetes, `.yaml` for application configs

## Development Workflow
1. Use `/docker/` for full-stack local development
2. Develop application code in `/observastack-app/`
3. Test deployment with `/observastack/install/compose/`
4. Production deployment via `/observastack/install/ansible/`

## Port Conventions
- Frontend dev: 3000 (Vite)
- BFF API: 8000 (uvicorn)
- Grafana: 3000 (production), 3001 (embedded proxy)
- Prometheus: 9090 (A), 9091 (B)
- Thanos Query: 10902
- OpenSearch: 9200
- Loki: 3100
- Tempo: 3200