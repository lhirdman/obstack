# Technology Stack & Build System

## Frontend Stack
- **Framework**: React 19.1.0 with TypeScript 5.9.2
- **Build Tool**: Vite 7.0.0 with React plugin (modern replacement for Create React App)
- **Routing**: React Router DOM v7.6.2 (latest with data APIs)
- **State Management**: TanStack Query v5.84.1 (React Query) for server state
- **UI Components**: Headless UI or Radix UI for accessible components
- **Styling**: Tailwind CSS 3.4+ or CSS Modules with PostCSS
- **Package Manager**: npm (with pnpm compatibility for faster installs)
- **Dev Server**: Vite dev server on port 3000
- **Testing**: Vitest (Vite-native) + React Testing Library + Playwright for E2E

## Backend Stack
- **API Framework**: FastAPI 0.115+ (latest stable)
- **Runtime**: Python 3.12+ with uvicorn ASGI server
- **Authentication**: python-jose[cryptography] 3.3+ or PyJWT 2.8+
- **HTTP Client**: httpx 0.27+ for async HTTP calls
- **Data Validation**: Pydantic v2.8+ with strict typing
- **Database**: SQLAlchemy 2.0+ with async support (if needed)
- **Caching**: Redis with redis-py 5.0+ or aiocache
- **Task Queue**: Celery 5.3+ with Redis broker (for background tasks)

## Infrastructure & Observability
- **Metrics**: Prometheus + Thanos for long-term storage
- **Logs**: Loki + OpenSearch cluster (3-node)
- **Traces**: Tempo with OpenTelemetry Collector
- **Dashboards**: Grafana with embedded panels
- **Message Queue**: RedPanda (Kafka-compatible, 3-node cluster)
- **Storage**: MinIO S3-compatible object storage
- **API Gateway**: Kong for routing and auth
- **Identity**: Keycloak for multi-tenant RBAC

## Deployment & Orchestration
- **Development**: Docker Compose with profiles
- **Production**: Ansible playbooks with role-based deployment
- **Container Registry**: Standard Docker images
- **Helm Charts**: Available for Kubernetes deployment

## Modern Development Practices
- **Frontend**: No Create React App - using Vite for faster builds and HMR
- **Backend**: Modern async Python with type hints and Pydantic v2
- **Testing**: Vitest instead of Jest for better Vite integration
- **Linting**: ESLint 9+ with flat config, Prettier 3+, Ruff for Python
- **Type Safety**: Strict TypeScript config, Pydantic for runtime validation
- **Package Management**: Lock files (package-lock.json, requirements.txt with hashes)

## Common Commands

### Frontend Development
```bash
cd observastack-app/frontend
npm install
npm run dev          # Start dev server on :3000 with HMR
npm run build        # Production build with tree-shaking
npm run preview      # Preview production build
npm run test         # Run Vitest unit tests
npm run test:e2e     # Run Playwright E2E tests
npm run lint         # ESLint + Prettier
npm run type-check   # TypeScript type checking
```

### Backend Development  
```bash
cd observastack-app/bff
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000  # Development server
python -m pytest                          # Run tests
ruff check .                              # Fast Python linting
mypy .                                    # Type checking
```

### Docker Compose (Full Stack)
```bash
cd docker
# Initialize storage buckets
docker compose --profile init up mc && docker compose --profile init down
# Start full observability stack
docker compose up -d
# Access Grafana at http://localhost:3000 (admin/admin)
```

### Ansible Deployment
```bash
cd observastack/install/ansible
ansible-playbook -i inventories/example/hosts.ini playbooks/install.yml
```

## Documentation & API Tools
- **Documentation Site**: Docusaurus 3.6+ (React-based, matches frontend stack)
- **API Documentation**: FastAPI auto-generated + Redocly for enhanced UI
- **Component Docs**: Storybook 8+ for React component documentation
- **Diagrams**: Mermaid.js for architecture diagrams (built into Docusaurus)
- **Code Examples**: Live code blocks with syntax highlighting
- **Search**: Algolia DocSearch for documentation search

## Additional Modern Tooling
- **Code Quality**: Husky for git hooks, lint-staged for pre-commit
- **Bundle Analysis**: Vite Bundle Analyzer, webpack-bundle-analyzer alternative
- **Performance**: Lighthouse CI for performance monitoring
- **Security**: npm audit, Snyk, or Socket.dev for dependency scanning
- **Containerization**: Multi-stage Docker builds with distroless images
- **Monitoring**: OpenTelemetry SDK for application observability

## Version Pinning Strategy
- **Frontend**: Use exact versions for build tools, caret ranges for React ecosystem
- **Backend**: Pin exact versions in requirements.txt, use pip-tools for management
- **Infrastructure**: Pin Docker image tags, avoid 'latest' in production
- **Node.js**: Use .nvmrc file to specify Node version (22.12+ LTS recommended, 24.x available but not LTS until Oct 2025)

## Development Proxy Configuration
Vite dev server proxies:
- `/api` → `http://localhost:8000` (BFF)
- `/grafana` → `http://localhost:3001` (Grafana embeds)

## Deprecated Technologies to Avoid
- ❌ Create React App (use Vite instead)
- ❌ Webpack directly (Vite handles this)
- ❌ Jest for Vite projects (use Vitest)
- ❌ Class components (use function components with hooks)
- ❌ PropTypes (use TypeScript interfaces)
- ❌ Moment.js (use date-fns or Temporal API when available)
- ❌ Lodash (use native ES methods or es-toolkit)
- ❌ Axios (httpx for backend, fetch API for frontend)