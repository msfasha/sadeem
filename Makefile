.PHONY: dev-k8s-up dev-k8s-down dev-cp-up dev-cp-down demo help

help:
	@echo "Available targets:"
	@echo "  dev-k8s-up    - Create local k8s cluster and deploy data plane"
	@echo "  dev-k8s-down  - Delete local k8s cluster"
	@echo "  dev-cp-up     - Start control plane services (Postgres + API + Worker)"
	@echo "  dev-cp-down   - Stop control plane services"
	@echo "  demo          - Run Spark -> Iceberg -> Trino demo"

dev-k8s-up:
	@echo "Creating local Kubernetes cluster..."
	@k3d cluster create sadeem-platform || echo "Cluster may already exist"
	@echo "Deploying data plane..."
	@cd infra/helm && helm upgrade --install dataplane ./dataplane
	@echo "Waiting for pods to be ready..."
	@kubectl wait --for=condition=ready pod -l app=minio --timeout=300s || true
	@kubectl wait --for=condition=ready pod -l app=trino --timeout=300s || true

dev-k8s-down:
	@echo "Deleting local Kubernetes cluster..."
	@k3d cluster delete sadeem-platform || echo "Cluster may not exist"

dev-cp-up:
	@echo "Starting Postgres..."
	@docker run -d --name sadeem-postgres -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15 || echo "Postgres may already be running"
	@sleep 3
	@echo "Running database migrations..."
	@cd control_plane && alembic upgrade head
	@echo "Starting API server..."
	@cd control_plane && uvicorn api.main:app --reload &
	@echo "Starting worker..."
	@cd control_plane && python -m worker.worker &
	@echo "Control plane started. API at http://localhost:8000"

dev-cp-down:
	@echo "Stopping control plane services..."
	@pkill -f "uvicorn api.main:app" || true
	@pkill -f "python -m worker.worker" || true
	@docker stop sadeem-postgres || true
	@docker rm sadeem-postgres || true

demo:
	@echo "Running Spark -> Iceberg -> Trino demo..."
	@cd infra/examples && ./demo-spark-to-trino.sh




