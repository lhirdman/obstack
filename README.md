# Observastack Platform

A full-stack observability platform built with React, FastAPI, and modern DevOps practices.

## Architecture

This is an Nx-managed monorepo containing:
- **Frontend**: React + TypeScript + Vite application (`apps/frontend`)
- **Backend**: FastAPI + Python application (`apps/backend`)

## Prerequisites

- **Node.js**: v22.12.0 or higher
- **Python**: v3.12 or higher
- **Docker**: For containerized development
- **npm**: v10.0.0 or higher

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/lhirdman/obstack.git
   cd obstack
   ```

2. **Install root dependencies**
   ```bash
   npm install
   ```

3. **Setup Frontend**
   ```bash
   cd apps/frontend
   npm install
   npm run dev
   ```
   Frontend will be available at http://localhost:5173

4. **Setup Backend** (in a new terminal)
   ```bash
   cd apps/backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
   Backend API will be available at http://localhost:8000

### Docker Development

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Development Commands

### Frontend (`apps/frontend`)
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run unit tests
npm run test:e2e     # Run end-to-end tests
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

### Backend (`apps/backend`)
```bash
uvicorn app.main:app --reload  # Start development server
pytest                         # Run tests
ruff check .                   # Run linting
ruff format .                  # Format code
```

### Nx Commands (from root)
```bash
npx nx build frontend    # Build frontend
npx nx test frontend     # Test frontend
npx nx lint frontend     # Lint frontend
```

## Project Structure

```
observastack/
├── apps/
│   ├── frontend/           # React + Vite frontend
│   └── backend/            # FastAPI backend
├── packages/               # Shared packages
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Docker development setup
└── nx.json                 # Nx configuration
```

## Technology Stack

- **Frontend**: React 19.1.0, TypeScript 5.9.2, Vite 7.0.0, Tailwind CSS
- **Backend**: Python 3.12+, FastAPI 0.115+, Pydantic 2.8+
- **Testing**: Vitest, Playwright, Pytest
- **Build**: Nx, Vite
- **Deployment**: Docker, Ansible

## Contributing

1. Follow the coding standards defined in `docs/architecture/coding-standards.md`
2. Ensure all tests pass before submitting PRs
3. Use conventional commit messages
4. All PRs must pass CI checks (linting, testing, type checking)

## License

ISC License
