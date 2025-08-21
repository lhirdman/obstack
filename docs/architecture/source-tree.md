# Source Tree

This document defines the official source code structure for the `obstack/platform` monorepo. The structure is managed by Nx to facilitate code sharing and maintain a clean, organized codebase.

## High-Level Directory Structure

```
obstack/platform/
├── apps/
│   ├── frontend/                 # React (Vite) Frontend Application
│   └── backend/                  # FastAPI Backend Application (BFF)
│
├── packages/
│   ├── shared-types/             # Shared TypeScript interfaces
│   └── ui-components/            # Shared React component library
│
├── docs/                         # Docusaurus documentation site
│
├── installer/                    # Community "one-click" installer
│
├── ansible/                      # Ansible playbooks for deployment
│
├── .github/
│   └── workflows/                # CI/CD pipelines (GitHub Actions)
│
├── .env.example
├── nx.json
├── package.json
└── README.md
```

## `apps` Directory

This directory contains the main, deployable applications.

### `apps/frontend`

Contains the React single-page application (SPA) that users interact with.

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Top-level page components (views)
│   ├── services/           # API client services
│   ├── lib/                # Utility functions, configs
│   ├── contexts/           # React contexts
│   ├── types/              # Frontend-specific types
│   └── main.tsx            # Application entry point
└── package.json
```

### `apps/backend`

Contains the FastAPI Backend-for-Frontend (BFF) application.

```
backend/
├── app/
│   ├── api/                # API router definitions (v1, v2, etc.)
│   ├── core/               # App configuration, security settings
│   ├── models/             # Pydantic data models
│   ├── services/           # Business logic services
│   ├── db/                 # Database connection, repository pattern
│   └── main.py             # Application entry point
└── requirements.txt
```

## `packages` Directory

This directory contains shared code intended to be used across different applications in the monorepo.

-   **`packages/shared-types`**: Contains TypeScript interfaces for data models (e.g., `User`, `Tenant`, `Alert`) that are used by both the frontend and backend to ensure type safety.
-   **`packages/ui-components`**: A shared library of reusable React components that can be used across different frontend applications if needed in the future.
