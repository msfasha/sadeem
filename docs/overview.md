<!--
Single Source of Truth (SSOT)
If anything conflicts with other docs under docs/ (especially docs/archived/), this file wins.
-->

# Big Data Platform — Single Source of Truth

**Status:** Active  
**Last updated:** 2025-12-24  
**Audience:** engineering + delivery (on‑prem / hybrid)

## Documentation Contract (Mandatory Rule)

**`docs/overview.md` is a living Single Source of Truth (SSOT).** This document MUST be updated whenever we add, modify, or remove any module, interface, API endpoint, Helm chart, configuration, or runtime behavior.

### The Rule
Every code change that affects system behavior MUST include a corresponding update to this document in the same change set (PR/commit). The update must document:
- **What changed**: component/module names, endpoints, configs, file paths
- **Why it changed**: intent, decision rationale, requirements addressed
- **How it works now**: data flow, sequence diagrams, key runtime behavior, interactions
- **How to run/verify**: commands, ports, expected outputs, health checks

### PR Checklist
Before merging any PR that touches code:
- [ ] Updated `docs/overview.md` with the change
- [ ] Added entry to **Change Log** section (date + brief description)
- [ ] Updated relevant sections: **Current Components**, **Runtime Architecture**, **Configuration Map**, or **Operational Notes**
- [ ] Verified all code examples/commands still work

### Document Structure
This SSOT is organized into:
- **Documentation Contract** (this section): the rule and checklist
- **Current Components**: inventory of all services/modules and their responsibilities
- **Runtime Architecture**: request flows, job submission flows, data paths
- **Configuration Map**: where to configure each component (env vars, Helm values, config files)
- **Operational Notes**: local dev setup, installation, troubleshooting, health checks
- **Change Log**: chronological record of significant changes

## Product Goal

Build a **simple, on‑prem / hybrid “junior Databricks”**:
- **Control plane**: manage workspaces, connections, catalogs, jobs, runs, users (simple in dev), basic audit, and a unified admin UI/API.
- **Data plane**: run open-source engines on Kubernetes to ingest, store, transform, and serve analytics/ML data.

Target domains include utilities (water/electric), banks, and government. We remain **domain‑agnostic**: domain specifics live in connectors and data models, not the core platform.

## Core Principles

- **Keep it simple**: fewer components, “boring” tech, clear boundaries.
- **Kubernetes-first**: one deployment story; local dev uses lightweight equivalents.
- **Open lakehouse**: separate storage/compute; open table format; avoid vendor lock‑in.
- **Two compute modes**:
  - **Batch/ML**: Spark
  - **Interactive BI SQL**: Trino
- **Batch-first** (v1): streaming comes after the foundation is stable.

## Requirements (Condensed)

### Functional (v1)
- **Workspaces**: create/manage logical tenants for teams/projects.
- **Connections**: store/validate configs for MinIO/S3, Trino, Spark, Postgres, etc.
- **Catalog explorer**: browse Iceberg namespaces/tables/schemas.
- **Jobs + runs**:
  - Job types: **Trino SQL** and **Spark batch**
  - Submit, monitor, stop, retry
  - Persist run state + links to logs/results
- **Admin UI**: manage workspaces/connections/jobs/runs + basic “health” view.
- **Audit baseline**: “who did what and when” for key control-plane actions.

### Non-functional (v1)
- **On‑prem capable**: minimal assumptions (k8s + storage + DNS/TLS).
- **Replaceable components** behind interfaces (object store, catalog, auth provider).
- **Safe secrets handling**: k8s secrets in v1; external secret manager later.
- **Operational clarity**: reproducible installs (Helm), backups, and reasonable defaults.

## Default Architecture (v1)

### Canonical stack choice (default)

**Iceberg-first** is the platform default because we explicitly want **multi‑engine interoperability (Spark + Trino)**.

- **Object storage**: MinIO (S3-compatible)
- **Table format**: Apache Iceberg
- **Catalog**: Iceberg REST catalog
- **SQL engine**: Trino (queries Iceberg tables)
- **Batch compute**: Spark on Kubernetes (ETL/ML feature jobs)
- **Execution/orchestration**: start with a simple control-plane worker submitting jobs; integrate a mature workflow engine later

### Note on Delta Lake (when it’s acceptable)

Some delivery contexts (e.g., Spark-heavy utility proposals) strongly prefer **Spark + Delta Lake**. That can be supported as a **workspace-level table-format choice** later, but the **platform default remains Iceberg** to keep Trino + Spark interoperability straightforward.

## Control Plane (v1) — What It Does

### Responsibilities
- **Workspace provisioning** (eventually automated):
  - Create MinIO bucket/prefix
  - Create Iceberg namespace
  - Create IdP group/roles (when OIDC enabled)
- **Connection manager**:
  - CRUD + validation (connectivity checks)
  - Credential storage (k8s secrets in v1)
- **Catalog explorer**:
  - Read metadata from Iceberg REST catalog
- **SQL proxy (optional v1, recommended v2)**:
  - Unified endpoint for UI “SQL Worksheet” via Trino
- **Job manager**:
  - Submit Spark jobs (Spark Operator) and Trino SQL jobs
  - Track runs: status, timings, parameters, log/result links

### Implementation (v1)
- **Backend**: Python + FastAPI
- **DB**: Postgres (platform metadata: users, workspaces, connections, jobs, runs, audit)
- **Worker**: a simple async worker/executor (later can delegate to Airflow/Temporal/Argo)
- **Frontend**: Admin GUI (small React/Next.js app or minimal UI early)
- **Auth**:
  - **Dev**: local users + hashed passwords + roles
  - **Prod target**: OIDC (Keycloak/AzureAD/Okta)

## Data Plane (v1) — What It Does

- **Durable ACID tables**: Iceberg on MinIO
- **Batch ingest/transforms**: Spark jobs writing/reading Iceberg tables
- **Interactive SQL**: Trino querying Iceberg tables for BI/dashboards

## System Diagram (Conceptual)

```mermaid
graph TD
    User[User / Analyst] --> UI[Platform Console (Admin UI)]
    UI --> API[Control Plane API (FastAPI)]

    subgraph "Control Plane"
        API --> DB[(Platform DB - Postgres)]
        API --> Auth[IdP (Keycloak/OIDC) - Phase 3+]
        API --> Worker[Worker/Executor]
    end

    subgraph "Data Plane (Engines)"
        Worker -->|Submit Spark jobs| SparkOp[Spark Operator]
        API -->|Query metadata| Iceberg[Iceberg REST Catalog]
        API -->|Run SQL / proxy| Trino[Trino Coordinator]
        Worker -->|Manage buckets/prefixes| MinIO[MinIO (S3)]
    end
```

## Data & Resource Model (Canonical Terms)

- **Workspace**: logical tenant (team/project) containing connections, jobs, datasets.
- **Connection**: a validated configuration to reach a service (MinIO/Trino/Spark/Postgres/etc).
- **Dataset/Table**: registered logical name + ownership + location + tags (backed by Iceberg).
- **Job**: versioned definition of work (Trino SQL job or Spark batch job), possibly parameterized.
- **Run**: single execution instance of a job; tracks state and artifacts/links.

## Non-Goals (v1)

- No custom compute engine (we orchestrate existing engines).
- No full governance suite (fine-grained masking/lineage) in Phase 1.
- No mandatory streaming in Phase 1 (batch first).
- No “perfect” multi-tenancy from day one; we add quotas/isolation in hardening.

## Deployment Model

### Local development (Phase 0/1)

- Control plane can run locally with a local Postgres.
- Data plane can run on a local k8s (kind/minikube/k3d) using Helm.

### Kubernetes install (data plane)

```bash
cd infra/helm
helm install dataplane ./dataplane
kubectl get pods
cd ../../infra/examples
./demo-spark-to-trino.sh
```

### Control plane dev

```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15
cd control_plane
alembic upgrade head
uvicorn api.main:app --reload
curl http://localhost:8000/health
```

## Phased Build Plan (Exit-Criteria Driven)

### Phase 0 — Repo + Local Dev Skeleton
- FastAPI scaffold + Postgres migrations
- Minimal Admin UI scaffold
- “Hello run”: submit a trivial Trino query and record a run

### Phase 1 — Kubernetes Data Plane Baseline
- Helm-based deployment for MinIO + Iceberg REST catalog + Trino + Spark operator
- Demo path: Spark writes Iceberg → Trino reads Iceberg

**Exit criteria**: ingest sample batch data → write Iceberg → query in Trino → show results in UI.

### Phase 2 — Control Plane MVP
- Workspaces + connections + jobs + runs (persisted)
- Admin UI: manage connections/jobs/runs
- Simple auth module (dev practical) + RBAC checks

**Exit criteria**: from UI/API create connection → create job → run → see status/logs → rerun.

### Phase 3 — Hardening
- OIDC integration (Keycloak or customer IdP)
- Backups + retention (MinIO + Postgres)
- Resource isolation/quotas (prevent BI from starving batch)
- Operational runbooks (install/upgrade)

### Phase 4 — Streaming (Only When Justified)
- Introduce Kafka (or equivalent) when requirements justify it
- Streaming ingestion to Iceberg with late-data + dedupe strategy

## Minimal BOM (Production-Capable Guidance)

This is a **reference sizing** for “small but real production,” optimized for tens of TB initially, moderate concurrency, batch ETL + BI SQL + ML experimentation.

### Option A — Smallest “real production” footprint (8 servers)
- **K8s control plane (3 nodes)**: 16 cores / 64 GB RAM / 2×1.92TB NVMe (RAID1) / 10GbE
- **Compute/services workers (3 nodes)**: 32 cores / 256 GB RAM / 2×1.92TB NVMe / 2×10GbE
- **MinIO storage (2 nodes)**: 16 cores / 128 GB RAM / 8×16TB HDD + 1×NVMe / 25GbE preferred (10GbE min)

### Option B — Better storage resilience (10 servers, preferred)
Same as Option A, but **4 MinIO nodes** instead of 2.

### Operational guardrails (strongly recommended)
- **Separate scheduling domains** (namespaces / node pools): `interactive` (Trino) vs `batch` (Spark) to avoid noisy neighbors.
- **Resource groups in Trino** to prevent runaway BI queries.
- **Backups**: Postgres backups; MinIO replication or periodic snapshots.
- **Observability baseline**: Prometheus + Grafana (MinIO metrics, Trino JMX exporter, Spark metrics).

## Open Decisions (Tracked Here)

- ✅ **Iceberg catalog**: REST catalog (decided)
- ✅ **Deployment**: Helm charts for data plane (decided)
- ⏳ **Workflow engine (Phase 3+)**: Temporal vs Airflow vs Argo
- ⏳ **UI framework**: React/Next.js vs minimal admin UI early
- ⏳ **Table-format extensibility**: support workspace-level Delta/Iceberg choice (later)

## Repo Structure (Current/Target)

```
control_plane/
  api/          # FastAPI application
  worker/       # Async execution/submission workers
  db/           # Database migrations and models
admin_ui/       # Admin GUI (to be added)
infra/
  helm/         # Helm charts for data plane components
  k8s/          # Plain manifests if needed
  examples/     # Sample configs and demos
docs/
  overview.md   # This file (SSOT)
```

## Current Components

*This section documents all implemented services, modules, and components. Update when adding/removing components.*

### Control Plane Components

- **API Service** (`control_plane/api/main.py`): FastAPI application providing REST endpoints
  - Endpoints: `/health`, `/workspaces`, `/connections`, `/jobs`, `/runs`
  - Uses SQLAlchemy ORM with Postgres backend
  - CORS enabled for local development
  - Pydantic schemas for request/response validation (`api/schemas.py`)

- **Worker Service** (`control_plane/worker/worker.py`): Async executor that processes queued runs
  - Polls database every 5 seconds for runs with status=`queued`
  - Supports Trino SQL runs and Spark batch runs
  - Updates run status (`running`, `succeeded`, `failed`) and stores artifacts
  - Currently simulates execution (Trino/Spark client integration TODO)

- **Database** (`control_plane/db/models.py`): SQLAlchemy models and Alembic migrations for Postgres
  - Tables: `workspaces`, `connections`, `jobs`, `runs`, `audit_events`
  - Initial migration: `db/migrations/versions/001_initial_schema.py`
  - Database URL configurable via `DATABASE_URL` env var

### Data Plane Components

- **MinIO** (`infra/helm/dataplane/templates/minio.yaml`): S3-compatible object storage
  - Single-node deployment for dev
  - Creates bucket `sadeem-data` on startup
  - Exposed via Service (ClusterIP or NodePort for dev)
  - Credentials: `minioadmin`/`minioadmin` (dev only)

- **Iceberg REST Catalog** (`infra/helm/dataplane/templates/iceberg-catalog.yaml`): Metadata catalog for Iceberg tables
  - Uses Postgres backend for catalog metadata
  - Configured to use MinIO as S3 backend
  - Exposed via Service on port 8181

- **Trino** (`infra/helm/dataplane/templates/trino.yaml`): SQL query engine
  - Coordinator + Worker deployment
  - Iceberg connector configured to use REST catalog
  - Exposed via Service on port 8080
  - Resource limits configurable via Helm values

- **Spark Operator** (`infra/helm/dataplane/templates/spark-operator.yaml`): Kubernetes operator for Spark jobs
  - Deploys Spark Operator CRD controller
  - Service account with RBAC for managing SparkApplications
  - Supports Spark 3.5.0+ with Iceberg extensions

## Runtime Architecture

*This section documents how requests flow through the system and how jobs are submitted/executed. Update when flows change.*

### Job Submission Flow

Current implementation flow:

```mermaid
sequenceDiagram
  participant User
  participant API as ControlPlaneAPI
  participant DB as Postgres
  participant Worker
  participant Trino
  participant SparkOp as SparkOperator
  participant Iceberg as IcebergRESTCatalog
  participant MinIO

  User->>API: POST /jobs/{id}/runs
  API->>DB: INSERT INTO runs (status='queued')
  API-->>User: Run created (status=queued)
  
  Note over Worker: Polls every 5 seconds
  Worker->>DB: SELECT * FROM runs WHERE status='queued'
  Worker->>DB: UPDATE runs SET status='running'
  
  alt Trino SQL Run
    Worker->>Trino: Execute SQL query (TODO: implement client)
    Trino->>Iceberg: GET /namespaces/{ns}/tables/{table}
    Trino->>MinIO: Read Iceberg table data/metadata
    Trino-->>Worker: Query results
  else Spark Batch Run
    Worker->>SparkOp: kubectl create SparkApplication CR
    SparkOp->>Iceberg: GET catalog metadata
    SparkOp->>MinIO: Write Iceberg table data/metadata
    SparkOp-->>Worker: Watch SparkApplication status
  end
  
  Worker->>DB: UPDATE runs SET status='succeeded', artifacts={...}
```

### Request Flow (API → Database)

**Create Workspace**:
1. Client → `POST /workspaces` with name/description
2. API validates schema → creates `Workspace` record → returns 201

**Create Connection**:
1. Client → `POST /connections` with workspace_id, type, config
2. API validates → creates `Connection` record → returns 201

**Create Job**:
1. Client → `POST /jobs` with workspace_id, job_type, definition
2. API validates → creates `Job` record → returns 201

**Create Run**:
1. Client → `POST /jobs/{job_id}/runs` with optional parameters
2. API verifies job exists → creates `Run` with status=`queued` → returns 201
3. Worker picks up run via polling → executes → updates status

## Configuration Map

*This section documents where to configure each component. Update when config locations/options change.*

### Control Plane Configuration

- **API Service** (`control_plane/api/main.py`):
  - `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:dev@localhost:5432/sadeem_platform`)
  - CORS origins: Currently `["*"]` (restrict in production)

- **Database** (`control_plane/db/alembic.ini`):
  - Connection string in `[alembic]` section: `sqlalchemy.url`
  - Migrations directory: `control_plane/db/migrations/versions/`

- **Worker** (`control_plane/worker/worker.py`):
  - `POLL_INTERVAL`: Seconds between polling cycles (default: 5)
  - `DATABASE_URL`: Same as API service

### Data Plane Configuration

- **MinIO** (`infra/helm/dataplane/values.yaml` or `values-dev.yaml`):
  - `minio.accessKey` / `minio.secretKey`: Credentials
  - `minio.buckets`: List of buckets to create on startup
  - `minio.service.type`: Service type (ClusterIP or NodePort for dev)
  - `minio.service.nodePort`: NodePort number (dev only)

- **Iceberg REST Catalog** (`infra/helm/dataplane/templates/iceberg-catalog.yaml`):
  - Environment variables in deployment:
    - `CATALOG_WAREHOUSE`: S3 warehouse path (e.g., `s3://sadeem-data/warehouse`)
    - `CATALOG_JDBC_URL`: Postgres connection for catalog metadata
    - `CATALOG_IO__S3__ENDPOINT`: MinIO endpoint URL

- **Trino** (`infra/helm/dataplane/templates/trino.yaml`):
  - ConfigMap `trino-config` contains:
    - `config.properties`: Coordinator/worker settings, memory limits
    - `catalog.properties`: Iceberg connector config (catalog URI, S3 endpoint)
  - Resource limits: `values.yaml` → `trino.coordinator.resources` / `trino.worker.resources`

- **Spark Operator** (`infra/helm/dataplane/templates/spark-operator.yaml`):
  - Operator image: `gcr.io/spark-operator/spark-operator:v1beta2-1.3.8-3.1.1`
  - SparkApplication CRs specify:
    - `sparkConf`: Iceberg catalog config, S3 endpoint, credentials
    - Example: `infra/examples/spark-iceberg-example.yaml`

## Operational Notes

*This section provides practical operational information. Update when procedures change.*

### Local Development Setup

#### Prerequisites
- Docker and Docker Compose (for Postgres)
- Kubernetes cluster: k3d, kind, or minikube
- kubectl configured to access the cluster
- Helm 3.x

#### Quick Start
1. **Start local Kubernetes cluster** (example with k3d):
   ```bash
   k3d cluster create sadeem-platform
   ```

2. **Deploy data plane**:
   ```bash
   cd infra/helm
   helm install dataplane ./dataplane
   kubectl get pods -w
   ```

3. **Start control plane** (local):
   ```bash
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15
   cd control_plane
   alembic upgrade head
   uvicorn api.main:app --reload
   ```

4. **Run demo**:
   ```bash
   cd infra/examples
   ./demo-spark-to-trino.sh
   ```

### Health Checks

- **API**: `GET /health` returns `{"status": "healthy", "service": "control-plane-api"}`
- **Data plane components**:
  - MinIO: `kubectl get pods -l app=minio`
  - Trino: `kubectl get pods -l app=trino`
  - Iceberg Catalog: `kubectl get pods -l app=iceberg-catalog`
  - Spark Operator: `kubectl get pods -l app=spark-operator`

### Troubleshooting

**Control Plane**:
- API not starting: Check Postgres is running and `DATABASE_URL` is correct
- Worker not processing runs: Check worker logs, verify database connection
- Migration errors: Ensure Postgres is accessible, run `alembic upgrade head` manually

**Data Plane**:
- Pods not starting: Check resource limits, node capacity
- MinIO bucket not created: Check init container logs
- Trino can't connect to Iceberg: Verify catalog service is running, check catalog endpoint in Trino config
- SparkApplication fails: Check SparkApplication CR status, driver/executor logs

## Change Log

*Chronological record of significant changes. Add entries when making changes.*

### 2025-12-24
- **Initial SSOT**: Created overview.md consolidating archived design documents
- **Documentation Contract**: Established mandatory rule that all code changes must update this document
- **Repository Skeleton**: Created directory structure (`control_plane/`, `infra/helm/`, `infra/examples/`)
- **Control Plane API**: Implemented FastAPI service with endpoints for workspaces, connections, jobs, runs
  - Database models: Workspace, Connection, Job, Run, AuditEvent
  - Alembic migration: Initial schema with all tables
  - Pydantic schemas for request/response validation
- **Worker Service**: Implemented async worker that polls for queued runs
  - Supports Trino SQL and Spark batch runs (simulated execution)
  - Updates run status and stores artifacts
- **Data Plane Helm Charts**: Created Helm chart for data plane deployment
  - MinIO: Single-node deployment with bucket creation
  - Iceberg REST Catalog: Postgres-backed catalog with S3 file IO
  - Trino: Coordinator + worker with Iceberg connector
  - Spark Operator: Kubernetes operator for Spark jobs
- **Demo Script**: Created `demo-spark-to-trino.sh` for end-to-end testing
- **Development Workflow**: Added Makefile with targets for local dev (`dev-k8s-up`, `dev-cp-up`, `demo`)

### [Future entries]
*Add entries here as implementation progresses*


## Source Material (for traceability)

This SSOT consolidates and supersedes the intent from:
- `docs/archived/control_plane_design_proposal.md`
- `docs/archived/architecture_thoughts.md`
- `docs/archived/project_master_plan.md`
- `docs/archived/minimal BOM`
- `docs/archived/readme.md`


