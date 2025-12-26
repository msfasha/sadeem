"""
Control Plane API - FastAPI application
"""
import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db.models import (
    init_db,
    get_db,
    Workspace,
    Connection,
    Job,
    Run,
    RunStatus,
)
from api.schemas import (
    WorkspaceCreate,
    WorkspaceResponse,
    ConnectionCreate,
    ConnectionResponse,
    JobCreate,
    JobResponse,
    RunCreate,
    RunResponse,
)

# Initialize database
database_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:dev@localhost:5432/sadeem_platform"
)
init_db(database_url)

app = FastAPI(
    title="Big Data Platform Control Plane API",
    description="API for managing workspaces, connections, jobs, and runs",
    version="0.1.0",
)

# CORS middleware for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "control-plane-api"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Big Data Platform Control Plane API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Workspace endpoints
@app.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(workspace: WorkspaceCreate, db: Session = Depends(get_db)):
    """Create a new workspace"""
    db_workspace = Workspace(**workspace.dict())
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace


@app.get("/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(db: Session = Depends(get_db)):
    """List all workspaces"""
    return db.query(Workspace).all()


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    """Get a workspace by ID"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


# Connection endpoints
@app.post("/connections", response_model=ConnectionResponse, status_code=201)
async def create_connection(
    connection: ConnectionCreate, db: Session = Depends(get_db)
):
    """Create a new connection"""
    db_connection = Connection(**connection.dict())
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


@app.get("/connections", response_model=List[ConnectionResponse])
async def list_connections(db: Session = Depends(get_db)):
    """List all connections"""
    return db.query(Connection).all()


@app.get("/connections/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: int, db: Session = Depends(get_db)):
    """Get a connection by ID"""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


# Job endpoints
@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job"""
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@app.get("/jobs", response_model=List[JobResponse])
async def list_jobs(db: Session = Depends(get_db)):
    """List all jobs"""
    return db.query(Job).all()


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# Run endpoints
@app.post("/jobs/{job_id}/runs", response_model=RunResponse, status_code=201)
async def create_run(job_id: int, run: RunCreate, db: Session = Depends(get_db)):
    """Create a new run for a job"""
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    run_data = run.dict()
    run_data["job_id"] = job_id
    run_data["status"] = RunStatus.QUEUED.value
    db_run = Run(**run_data)
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run


@app.get("/runs", response_model=List[RunResponse])
async def list_runs(db: Session = Depends(get_db)):
    """List all runs"""
    return db.query(Run).all()


@app.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get a run by ID"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/jobs/{job_id}/runs", response_model=List[RunResponse])
async def list_job_runs(job_id: int, db: Session = Depends(get_db)):
    """List all runs for a job"""
    return db.query(Run).filter(Run.job_id == job_id).all()

