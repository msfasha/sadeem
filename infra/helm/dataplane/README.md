# Dataplane Helm Chart

This Helm chart deploys the core data plane components for the lakehouse platform:
- MinIO (S3-compatible object storage)
- Postgres (for Iceberg REST catalog metadata)
- Iceberg REST catalog
- Trino (SQL query engine)
- Spark Operator (for Spark job execution)

## Prerequisites

- Kubernetes cluster (1.24+)
- Helm 3.x
- kubectl configured

## Installation

```bash
# Install the chart
helm install dataplane ./infra/helm/dataplane

# Or with custom values
helm install dataplane ./infra/helm/dataplane -f my-values.yaml
```

## Configuration

See `values.yaml` for all configurable parameters. Key settings:

- `minio.accessKey` / `minio.secretKey`: MinIO credentials
- `postgres.password`: Postgres password
- `trino.worker.replicas`: Number of Trino worker nodes
- `global.storageClass`: Kubernetes storage class (if needed)

## Verification

After installation, verify components are running:

```bash
kubectl get pods
kubectl get services
```

## Uninstallation

```bash
helm uninstall dataplane
```

