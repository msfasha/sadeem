# Control Plane Design Proposal: "Junior Databricks"

## 1. Vision
To build a **general-purpose Data Platform Control Plane** that can interpret and manage modern open-source big data stacks (Trino, Iceberg, Spark, MinIO) across various industries (Utilities, Gov, Banking).

**Key Philosophy:** "Keep it Simple."
Instead of building a complex cloud orchestrator from day one, we build a **Unified Console** that wraps standard open-source APIs into a cohesive "Workspace" experience.

---

## 2. Architecture Overview

 The Control Plane sits *above* the infrastructure (K8s/VMs) and *in front of* the data services.

```mermaid
graph TD
    User[User / Analyst] --> UI[Platform Console (React)]
    UI --> API[Control Plane API (FastAPI)]
    
    subgraph "Control Plane Services"
        API --> DB[(Platform DB - Postgres)]
        API --> Auth[Identity Provider (Keycloak)]
    end
    
    subgraph "Data Plane (The actual engines)"
        API --> |Submits Jobs| Spark[Spark Operator]
        API --> |Queries Metadata| Iceberg[Iceberg REST Catalog]
        API --> |Proxy Queries| Trino[Trino Coordinator]
        API --> |Mng Buckets| MinIO[MinIO]
    end
```

## 3. Core Concepts

### 3.1 The "Workspace" (Tenant)
A Workspace is the logical container for a team or project.
- **Data**: A dedicated Namespace in the Iceberg Catalog (e.g., `water_utility_prod`).
- **Storage**: A bucket or prefix in MinIO (e.g., `s3://water-utility/`).
- **Compute**: Quotas for Spark and Trino usage.
- **Users**: A group of users in Keycloak with permissions to this workspace.

### 3.2 The "Control Plane API"
A lightweight Python (FastAPI) service.
**Responsibilities:**
1.  **Workspace Provisioning**: "Create new project" -> Creates S3 bucket, creates Iceberg Namespace, creates Keycloak Group.
2.  **SQL Proxy**: A unified endpoint to run SQL through Trino (enabling the UI to include a "SQL Worksheet").
3.  **Job Manager**: Submit and track status of background tasks (Spark jobs, dbt runs).
4.  **Catalog Explorer**: Browse tables, schemas, and columns (read from Iceberg REST).

---

## 4. Phase 1: The "Control Plane" MVP

We focus purely on the **Management Layer** first. We assume the underlying engines (Trino, MinIO) are running (even if manually installed initially).

### Stack Recommendation
*   **Backend**: **FastAPI** (Python). Easy to write, great ecosystem, async for handling long-running platform tasks.
*   **Frontend**: **React** + **Tailwind** + **ShadCN UI**. Clean, modern, reliable "Databricks-like" look.
*   **State**: **Postgres**. Stores workspace metadata, query history, saved queries, user preferences.
*   **Infrastructure Interface**: **Kubernetes Client (Python)**. To interact with the cluster directly (listing pods, logs, etc.).

### Build Process (Iterative)
1.  **Step 1: Scaffold**: Setup monorepo (frontend + backend).
2.  **Step 2: Connection Manager**: API to connect to an external MinIO and Trino instance.
3.  **Step 3: Catalog Browser**: UI to tree-view schemas and tables (read-only).
4.  **Step 4: SQL Runner**: Simple text area to run SQL against Trino and see results.
5.  **Step 5: Workspace Logic**: Add "Create Workspace" flow that automates the setup of buckets/schemas.

---

## 5. Why this fits "Junior Databricks"
*   **Databricks** = Unified UI for Notebooks, SQL, and Jobs over Spark/Delta.
*   **Our Platform** = Unified UI for SQL and Jobs over Trino/Iceberg.

By abstracting the distinct open-source tools behind a single "Platform API", we give the user that "single product" feel without rewriting the heavy engines.
