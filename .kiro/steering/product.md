# ObservaStack Product Overview

ObservaStack is a unified observability platform that consolidates logs, metrics, traces, and alerts into a single multi-tenant web application. The project aims to provide a cost-effective alternative to commercial APM solutions like Datadog and New Relic.

## Core Value Proposition
- **Unified View**: "All Your Signals. One View" - consolidates fragmented observability workflows
- **Multi-tenant**: RBAC and tenant isolation for MSPs and enterprise environments  
- **Cost-effective**: Open source alternative to expensive commercial APM platforms
- **Embedded Dashboards**: Extends Grafana panels with consistent navigation and styling

## Target Users
- DevOps teams and Site Reliability Engineers (SREs)
- Managed Service Providers (MSPs)
- SaaS platform operators
- Enterprises replacing expensive APM platforms

## Key Features
- Custom UI shell with embedded Grafana dashboards
- Cross-signal linking (trace → logs → metrics)
- Alert aggregation and management
- Insights dashboard for cost optimization
- Ansible-based deployment automation
- Docker Compose development environment

## Architecture Philosophy
- Backend-for-Frontend (BFF) pattern with FastAPI
- React/TypeScript frontend with embedded observability tools
- Multi-tenant security at both UI and datasource levels
- Microservices-ready with OpenTelemetry integration