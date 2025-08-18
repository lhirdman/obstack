# Installation

Welcome to ObservaStack! This guide will help you get ObservaStack up and running in your environment.

## Prerequisites

Before installing ObservaStack, ensure you have the following prerequisites:

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- **Memory**: Minimum 8GB RAM (16GB+ recommended for production)
- **CPU**: 4+ cores recommended
- **Storage**: 50GB+ available disk space
- **Network**: Internet access for downloading dependencies

### Software Dependencies

- **Docker**: Version 20.10+ and Docker Compose v2
- **Node.js**: Version 18+ (for frontend development)
- **Python**: Version 3.12+ (for backend development)
- **Ansible**: Version 2.9+ (for production deployment)

## Installation Methods

ObservaStack supports multiple installation methods depending on your use case:

### 1. Docker Compose (Recommended for Development)

The fastest way to get started with ObservaStack is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/observastack/observastack.git
cd observastack

# Navigate to docker directory
cd docker

# Initialize storage buckets (first time only)
docker compose --profile init up mc && docker compose --profile init down

# Start the full observability stack
docker compose up -d

# Access Grafana at http://localhost:3000 (admin/admin)
```

### 2. Ansible Deployment (Production)

For production deployments, use the Ansible playbooks:

```bash
# Navigate to ansible directory
cd observastack/install/ansible

# Copy and customize inventory
cp inventories/example/hosts.ini inventories/production/hosts.ini
# Edit inventories/production/hosts.ini with your server details

# Run the installation playbook
ansible-playbook -i inventories/production/hosts.ini playbooks/install.yml
```

### 3. Kubernetes Deployment

Deploy using Helm charts for Kubernetes environments:

```bash
# Add ObservaStack Helm repository
helm repo add observastack https://observastack.github.io/helm-charts
helm repo update

# Install ObservaStack
helm install observastack observastack/observastack \
  --namespace observastack \
  --create-namespace \
  --values values.yaml
```

## Verification

After installation, verify that ObservaStack is running correctly:

### Check Services

```bash
# For Docker Compose
docker compose ps

# For Kubernetes
kubectl get pods -n observastack

# For Ansible deployment
systemctl status grafana-server
systemctl status prometheus
```

### Access Web Interface

1. Open your browser and navigate to `http://localhost:3000` (or your configured domain)
2. Log in with default credentials: `admin/admin`
3. You should see the ObservaStack dashboard

### Test Data Ingestion

Verify that data is being collected:

1. Navigate to the Search page
2. Try searching for logs or metrics
3. Check that alerts are being processed

## Next Steps

Once ObservaStack is installed:

1. [Configure authentication](../user-guide/authentication.md)
2. [Set up your first search](../user-guide/search.md)
3. [Configure alerts](../user-guide/alerts.md)
4. [Explore insights dashboard](../user-guide/insights.md)

## Troubleshooting

If you encounter issues during installation:

1. Check the [Common Issues](../troubleshooting/common-issues.md) guide
2. Review service logs for error messages
3. Ensure all prerequisites are met
4. Consult the [Debugging](../troubleshooting/debugging.md) guide

## Support

Need help? Here are your options:

- 📖 [Documentation](https://observastack.github.io/docs)
- 💬 [GitHub Discussions](https://github.com/observastack/observastack/discussions)
- 🐛 [Report Issues](https://github.com/observastack/observastack/issues)
- 📧 [Community Support](mailto:community@observastack.io)