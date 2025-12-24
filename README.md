# Lakehouse Platform

A simple, portable, Kubernetes-first lakehouse platform with a control plane for managing workspaces, connections, jobs, and runs.

## Overview

This platform provides:
- **Data plane**: MinIO (object storage), Apache Iceberg (table format), Trino (SQL engine), Spark (batch compute)
- **Control plane**: FastAPI-based API for managing workspaces, connections, jobs, and runs

See [docs/overview.md](docs/overview.md) for the complete specification.

## Quick Start

### Prerequisites

- Kubernetes cluster (local: `kind`, `minikube`, or `k3d`)
- `kubectl` configured
- `helm` v3.x installed
- Python 3.10+ (for control plane)
- PostgreSQL (for control plane metadata)

### Deploy Data Plane

```bash
# Deploy data plane components
cd infra/helm
helm install dataplane ./dataplane

# Wait for components to be ready
kubectl wait --for=condition=available --timeout=300s deployment/minio
kubectl wait --for=condition=available --timeout=300s deployment/trino-coordinator
```

### Setup Control Plane

```bash
# Install dependencies
cd control_plane
pip install -r requirements.txt

# Set database URL
export DB_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/lakehouse_platform"

# Run migrations
alembic upgrade head

# Start API server
uvicorn api.main:app --reload
```

### Run Demo

```bash
# Run smoke demo (end-to-end test)
cd infra/examples
./smoke-demo.sh

# Or run Spark -> Iceberg -> Trino demo
./demo-spark-to-trino.sh
```

## Project Structure

```
.
├── control_plane/          # FastAPI control plane
│   ├── api/               # API endpoints
│   ├── db/                # Database models and migrations
│   └── worker/            # Job execution workers
├── infra/
│   ├── helm/             # Helm charts for data plane
│   └── examples/         # Demo scripts
└── docs/                  # Documentation
    └── overview.md       # Single source of truth
```

## Development

See individual component READMEs:
- [Control Plane README](control_plane/README.md)
- [Helm Chart README](infra/helm/dataplane/README.md)

## License

[To be determined]

