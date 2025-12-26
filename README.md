# Big Data Platform

A simple, on-prem/hybrid "junior Databricks" platform for managing workspaces, connections, catalogs, jobs, and runs.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Kubernetes cluster (k3d, kind, or minikube)
- kubectl configured
- Helm 3.x
- Python 3.10+

### Local Development

1. **Start local Kubernetes cluster** (example with k3d):
   ```bash
   k3d cluster create sadeem-platform
   ```

2. **Deploy data plane**:
   ```bash
   make dev-k8s-up
   # Or manually:
   cd infra/helm
   helm install dataplane ./dataplane
   ```

3. **Start control plane**:
   ```bash
   make dev-cp-up
   # Or manually:
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15
   cd control_plane
   alembic upgrade head
   uvicorn api.main:app --reload
   ```

4. **Run demo**:
   ```bash
   make demo
   # Or manually:
   cd infra/examples
   ./demo-spark-to-trino.sh
   ```

## Project Structure

```
control_plane/          # Control plane services
  api/                  # FastAPI application
  worker/               # Async execution workers
  db/                   # Database models and migrations
infra/
  helm/                 # Helm charts for data plane
  k8s/                  # Plain Kubernetes manifests
  examples/             # Demo scripts and configs
docs/
  overview.md           # Single Source of Truth (SSOT)
```

## Documentation

See [docs/overview.md](docs/overview.md) for the complete architecture, design decisions, and operational notes.

**Important**: This project follows a strict documentation contract. All code changes must update `docs/overview.md` in the same change set.

## License

[To be determined]

