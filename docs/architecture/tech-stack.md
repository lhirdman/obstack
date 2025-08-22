# Tech Stack

This document outlines the official technology stack for the Obstack platform. All development must adhere to these choices to ensure consistency, maintainability, and performance.

## Frontend

| Category | Technology | Version | Purpose |
|---|---|---|---|
| Language | TypeScript | 5.9.2 | Primary language for the frontend application. |
| Framework | React | 19.1.0 | Core UI library for building the component-based interface. |
| Build Tool | Vite | 7.0.0 | Frontend development server and production bundler. |
| State Management | TanStack Query | 5.84.1 | Manages server state, caching, and data synchronization. |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS framework for rapid UI development. |
| Testing (Unit) | Vitest & RTL | latest | Vite-native unit and component testing framework. |
| Testing (E2E) | Playwright | latest | End-to-end testing across different browsers. |

## Backend

| Category | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.12+ | Primary language for the BFF and backend services. |
| Framework | FastAPI | 0.115+ | High-performance ASGI framework for building APIs. |
| Data Validation | Pydantic | 2.8+ | Core library for data validation and settings management. |
| Database | PostgreSQL | 15+ | Core relational database for users, tenants, and config. |
| Caching | Redis | 7.x | In-memory data store for caching and task queuing. |
| Task Queue | Celery | 5.3+ | Distributed task queue for background processing. |

## Infrastructure & Services

| Category | Technology | Version | Purpose |
|---|---|---|---|
| Identity | Keycloak | 22.x+ | Identity and Access Management for multi-tenancy. |
| API Gateway | Kong | 3.4+ | Manages, secures, and routes all API traffic. |
| Data Ingestion | OpenTelemetry Collector | latest | Primary endpoint for receiving customer telemetry data (OTLP). |
| Log Collection | Vector | latest | High-performance agent for collecting and forwarding log data. |
| Data Streaming | Redpanda | latest | Kafka-compatible streaming platform for the log ingestion pipeline. |
| Deployment | Ansible | latest | Configuration management and application deployment. |
| Metrics | Prometheus & Thanos | latest | Core engine for metrics collection and long-term storage. |
| Logs | Loki | latest | Core engine for log aggregation. |
| Traces | Tempo | latest | Core engine for distributed tracing. |
| Cost | OpenCost | latest | Engine for Kubernetes cost monitoring. |
| Storage | MinIO / S3 | latest | S3-compatible object storage for logs, metrics, etc. |

## Documentation

| Category | Technology | Version | Purpose |
|---|---|---|---|
| Site Generator | Docusaurus | 3.6+ | Static site generator for project documentation. |
| API Docs | Redocly | latest | Renders the OpenAPI spec for a user-friendly UI. |
