# Antigravity Platform: Master Vision & Roadmap

**Status:** Draft
**Last Updated:** 2025-12-15
**Document Type:** Single Source of Truth

---

## 1. Executive Summary
**Objective:** Build a "Junior Databricks" — a simplified, general-purpose Data Platform Control Plane.
**Target Audience:** Utilities, Government, Banking (On-premise / Private Cloud).
**Core Value:** A unified, user-friendly interface to manage powerful open-source big data tools (Trino, Iceberg, Spark, MinIO) without the complexity of raw infrastructure management.

---

## 2. Strategic Objectives

1.  **Simplicity First:** The complexity of Kubernetes/Hadoop must be hidden from the end-user (Analyst/Data Scientist).
2.  **Industry Agnostic:** The core platform provides "Workspaces" and "Compute". Business logic (Water, Finance) lives *inside* the workspace, not the platform code.
3.  **Separation of Concerns:**
    *   **Control Plane (The App):** Lightweight, manages state, permissions, and orchestration.
    *   **Data Plane (The Engine):** Heavy lifters (Trino, Spark, MinIO) that scale independently.
4.  **No Vendor Lock-in:** All data stored in open formats (Apache Iceberg). All APIs are standard (S3, connection strings).

---

## 3. Technology Stack

### Control Plane (The "Junior Databricks" App)
*   **Frontend:** React + Tailwind + ShadCN UI (Modern, responsive, "Premium" feel).
*   **Backend:** Python FastAPI (Async, integration-heavy).
*   **Database:** Postgres (Relational state for users, workspaces, query history).

### Data Plane (The Infrastructure)
*   **Storage:** MinIO (S3 Compatible Object Storage).
*   **Table Format:** Apache Iceberg (ACID transactions, Schema evolution).
*   **SQL Engine:** Trino (Fast interactive SQL for BI/Dashboards).
*   **Processing:** Apache Spark (Heavy batch jobs, ML).
*   **Security:** Keycloak (SSO, Identity Management).

---

## 4. Development Roadmap

We will develop in **Phased Batches**, focusing on the Control Plane first.

### Phase 1: Local Development Environment (The "Mini-Lab")
*Goal: Spin up the entire data plane locally using Docker so we have something to build against.*
1.  **Infrastructure-as-Code (Local)**: Create a `docker-compose.yml` that launches:
    *   **MinIO** (Simulating Storage)
    *   **Trino** (Simulating SQL Engine)
    *   **Iceberg REST Catalog** (Metadata)
    *   **Postgres** (Control Plane DB)
2.  **Verification**: Prove we can write a file to local MinIO and query it via local Trino.

### Phase 2: The Control Plane "Read-Only" Console
*Goal: Build the UI to manage the Local Dev Stack.*
1.  **Scaffold**: Monorepo setup (FastAPI + React).
2.  **Connectivity**: Connect the App to the local Docker containers.
3.  **Catalog Viewer**: Browse the local Iceberg tables.
4.  **SQL Worksheet**: Query the local Trino.

### Phase 3: Workspace Management (The "Manager")
*Goal: Self-service creation of data environments.*
1.  **Workspace Entity**: Define "Workspace" in DB.
2.  **Provisioning Logic**: Calling `create bucket`, `create schema` APIs.

### Phase 4: Job Runner & Real Scale
*Goal: Moving to Spark and generic Kubernetes.*
1.  **Job Submission**: Spark job runner.
2.  **K8s Deployment**: Helm charts for production.

---

## 5. Immediate Next Steps (Phase 1 Execution)
1.  [x] Define Architecture & Stack (Done).
2.  [ ] **Initialize Repository**: Create the project structure.
3.  [ ] **"Hello World" Connection**: A simple API endpoint that lists buckets from MinIO.
