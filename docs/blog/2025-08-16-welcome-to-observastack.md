---
slug: welcome-to-observastack
title: Welcome to ObservaStack
authors: [observastack-team]
tags: [observability, monitoring, open-source, announcement]
---

# Welcome to ObservaStack

We're excited to introduce **ObservaStack** - a unified observability platform that brings together logs, metrics, traces, and alerts into a single, cohesive experience.

## The Problem We're Solving

Modern applications generate vast amounts of observability data across multiple tools and platforms. DevOps teams often find themselves juggling between different interfaces, struggling to correlate events across their stack, and paying premium prices for commercial APM solutions.

ObservaStack addresses these challenges by providing:

- **Unified Interface**: One dashboard for all your observability needs
- **Multi-Tenant Architecture**: Secure isolation for MSPs and enterprises  
- **Cost-Effective**: Open source alternative to expensive commercial platforms
- **Easy Deployment**: Get started in minutes with Docker Compose

<!--truncate-->

## Key Features

### 🔍 Unified Search
Search across logs, metrics, and traces from a single interface. No more switching between tools to understand what's happening in your system.

### 🏢 Multi-Tenant Ready
Built from the ground up with multi-tenancy in mind. Perfect for managed service providers and enterprises with multiple teams or customers.

### 📊 Embedded Dashboards
Leverage the power of Grafana dashboards within the ObservaStack interface, with consistent navigation and tenant-specific branding.

### 🚨 Intelligent Alerting
Aggregate and manage alerts from multiple sources with smart routing and escalation policies.

### 💡 Cost Insights
Get visibility into your observability costs and optimize resource usage with built-in insights and recommendations.

## Getting Started

Getting ObservaStack running is incredibly simple:

```bash
# Clone the repository
git clone https://github.com/observastack/observastack.git
cd observastack/docker

# Initialize storage
docker compose --profile init up mc && docker compose --profile init down

# Start ObservaStack
docker compose up -d

# Access at http://localhost:3000 (admin/admin)
```

That's it! You now have a complete observability stack running locally.

## Architecture Highlights

ObservaStack is built using modern technologies:

- **Frontend**: React 19 with TypeScript and Vite for fast development
- **Backend**: FastAPI with async/await for high performance
- **Observability**: Prometheus, Loki, Tempo, and Grafana
- **Authentication**: Keycloak for enterprise-grade security
- **Deployment**: Docker Compose for development, Ansible for production

## What's Next

We're just getting started! Here's what's coming in the next few months:

- **Enhanced Multi-Tenancy**: Advanced RBAC and tenant customization
- **AI-Powered Insights**: Machine learning for anomaly detection and root cause analysis
- **Extended Integrations**: Support for more data sources and notification channels
- **Performance Optimizations**: Improved query performance and resource efficiency
- **Kubernetes Operator**: Native Kubernetes deployment and management

## Join the Community

ObservaStack is an open source project, and we welcome contributions from the community:

- 🌟 **Star us on GitHub**: https://github.com/observastack/observastack
- 💬 **Join Discussions**: Share ideas and get help from the community
- 🐛 **Report Issues**: Help us improve by reporting bugs and feature requests
- 🤝 **Contribute**: Submit pull requests for features and fixes

## Commercial Support

While ObservaStack is open source, we also offer commercial support and services:

- **Professional Services**: Implementation, customization, and training
- **Enterprise Support**: SLA-backed support with priority response
- **Managed Hosting**: Fully managed ObservaStack in the cloud
- **Custom Development**: Tailored features for enterprise requirements

Contact us at [enterprise@observastack.io](mailto:enterprise@observastack.io) for more information.

## Conclusion

We believe that observability should be accessible, affordable, and powerful. ObservaStack represents our vision of what modern observability platforms should be - unified, multi-tenant, and cost-effective.

Try ObservaStack today and let us know what you think! We're excited to see what you build with it.

---

*The ObservaStack Team*