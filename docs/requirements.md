# DEPRECATED - See overview.md

This file is deprecated. Please refer to [overview.md](overview.md) for the current specification.

---

### Overview (Single Source of Truth)

This document is the authoritative specification for this repo/product. If anything conflicts with other docs, **this doc wins**.

### Product goal

Build a **simple, on‑prem / hybrid “junior Databricks”**:
- **Control plane**: manage workspaces, connections, catalogs, jobs, runs, users (simple in dev), audit basics, and an admin UI/API.
- **Data plane**: run open-source engines on Kubernetes to ingest, store, transform, and serve analytics/ML data.

Target domains include utilities (water/electric), banks, and government. We stay domain-agnostic: domain specifics live in connectors and data models, not the core platform.

### Core principles

- **Keep it simple**: prefer fewer components, boring tech, and clear boundaries.
- **Kubernetes-first**: one deployment story; local dev uses lightweight equivalents.
- **Iceberg-first**: open table format for multi-engine interoperability.
- **Trino for SQL/BI**: interactive SQL is first-class.
- **Batch-first** initially: streaming comes after a stable control plane + data plane foundation.

### Default stack (v1)

#### Data plane (v1)
- **Object storage**: MinIO (S3-compatible)
- **Table format**: Apache Iceberg
- **SQL engine**: Trino (queries Iceberg tables)
- **Batch compute**: Spark on Kubernetes (ETL/ML feature jobs)
- **Orchestration/execution**: start with a simple control-plane worker submitting jobs; integrate a mature workflow engine later
- **Metadata catalog**: choose one catalog interface for Iceberg (REST catalog recommended) and keep it consistent

#### Control plane (v1)
- **Backend**: Python + FastAPI
- **DB**: Postgres (platform metadata: workspaces, connections, jobs, runs, audit)
- **Frontend**: Admin GUI (simple) — can be a small React/Next.js app or even server-rendered pages early if speed matters
- **Auth (dev phase)**: simple practical auth module (local users, hashed passwords, roles)
- **Auth (prod target)**: OIDC (e.g., Keycloak/AzureAD/Okta) — planned, not required for Phase 1

### What we are building (definition)

#### Control plane responsibilities
- **Workspace/projects**
  - Single-org model with multiple workspaces
- **Connections**
  - Store and validate connection configs (MinIO, Trino, Spark, Postgres, etc.)
  - Secrets handled safely (k8s secrets in v1; external secret manager later)
- **Catalog registration**
  - Register datasets/tables (logical name, owner, location, format=Iceberg, tags)
- **Jobs**
  - Job types: Trino SQL job, Spark batch job
  - Versioned job definitions, parameters, and schedules (optional in v1)
- **Runs**
  - Submit, monitor, stop, retry
  - Persist run state + logs links
- **Admin GUI**
  - Workspaces, connections, jobs, runs, basic health view
- **Audit (baseline)**
  - “who did what and when” for key actions

#### Data plane responsibilities
- Provide reliable, scalable execution for:
  - Batch ingest + transforms (Spark)
  - Interactive SQL for BI (Trino)
  - Durable ACID tables (Iceberg on MinIO)

### Non-goals (v1)

- No custom compute engine (we orchestrate existing engines).
- No full governance suite (fine-grained masking/lineage) in Phase 1.
- No streaming pipeline requirements in Phase 1 (batch only).

### Phased build plan (high-level)

#### Phase 0 — Repo + local dev skeleton
- FastAPI service scaffold + Postgres schema migrations
- Minimal Admin UI scaffold
- Local dev environment (docker-compose or kind/minikube)
- “Hello run”: submit a trivial Trino query and record a run

#### Phase 1 — Minimal Kubernetes foundation (data plane baseline)
- Kubernetes baseline manifests/Helm chart structure
- MinIO deployed and reachable
- Trino deployed and able to query a sample Iceberg table
- Spark on k8s able to write an Iceberg table to MinIO
- Basic observability hooks (health endpoints; minimal metrics later)

Exit criteria:
- We can ingest sample batch data -> write Iceberg -> query in Trino -> show results in UI.

#### Phase 2 — Minimal control plane MVP
- Workspaces + connections + job definitions + runs (persisted)
- Admin GUI: manage connections/jobs/runs
- Simple auth module (dev practical)
- Role-based checks for admin vs user actions

Exit criteria:
- From UI/API: create connection -> create job -> run -> see status/logs -> rerun.

#### Phase 3 — Hardening
- OIDC integration (Keycloak or customer IdP)
- Backups + retention policies (MinIO + Postgres)
- Resource isolation / quotas (prevent BI from starving batch)
- Operational docs for install/upgrade

#### Phase 4 — Streaming (after foundation is solid)
- Introduce Kafka (or equivalent) only when requirements justify it
- Streaming ingestion to Iceberg with clear late-data + dedupe strategy
- Control-plane support for streaming jobs and monitoring

### Design constraints and portability

This product must run in different environments:
- Minimal assumptions: Kubernetes cluster + storage + network + basic DNS/TLS.
- Cloud/hybrid is allowed, but the platform must work on-prem without vendor lock-in.
- Components should be replaceable behind interfaces (object store, catalog, auth provider).

### Repo structure (suggested)

- control_plane/
  - api/ (FastAPI)
  - worker/ (async execution/submission)
  - db/ (migrations, models)
- admin_ui/
- infra/
  - helm/ (charts)
  - k8s/ (manifests if needed)
  - examples/ (sample configs)
- docs/
  - overview.md (this file)
  - runbooks.md (later)
  - architecture.md (later, generated from this doc)

### Open decisions (tracked here)

- Iceberg catalog implementation (REST catalog vs HMS) for v1
- Workflow engine choice for Phase 3+ (Temporal vs Airflow/Argo integration)
- UI choice (React/Next.js vs minimal server-rendered admin)