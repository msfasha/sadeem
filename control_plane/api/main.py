"""FastAPI main application."""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta

from db.database import get_db, init_db
from db.models import User, Workspace, Connection, Job, Run, UserRole
from api.schemas import (
    ConnectionCreate, ConnectionResponse, ConnectionUpdate,
    JobCreate, JobResponse, JobUpdate,
    RunCreate, RunResponse,
    WorkspaceCreate, WorkspaceResponse,
    UserCreate, UserResponse, Token
)
from api.auth import (
    authenticate_user, get_current_user, get_current_admin_user,
    create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from worker.executor import execute_trino_sql_job

app = FastAPI(
    title="Lakehouse Platform Control Plane",
    description="Control plane API for managing workspaces, connections, jobs, and runs",
    version="0.1.0"
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Authentication endpoints
@app.post("/api/auth/login", response_model=Token)
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login endpoint."""
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (dev phase - no auth required)."""
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Workspace endpoints
@app.post("/api/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a workspace."""
    db_workspace = Workspace(**workspace.dict())
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace


@app.get("/api/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all workspaces."""
    workspaces = db.query(Workspace).all()
    return workspaces


@app.get("/api/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a workspace by ID."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


# Connection endpoints
@app.post("/api/connections", response_model=ConnectionResponse)
async def create_connection(
    connection: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a connection."""
    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == connection.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db_connection = Connection(**connection.dict())
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


@app.get("/api/connections", response_model=list[ConnectionResponse])
async def list_connections(
    workspace_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List connections, optionally filtered by workspace."""
    query = db.query(Connection)
    if workspace_id:
        query = query.filter(Connection.workspace_id == workspace_id)
    connections = query.all()
    return connections


@app.get("/api/connections/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a connection by ID."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


# Job endpoints
@app.post("/api/jobs", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a job."""
    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == job.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    job_dict = job.dict()
    job_dict["created_by"] = current_user.username
    db_job = Job(**job_dict)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@app.get("/api/jobs", response_model=list[JobResponse])
async def list_jobs(
    workspace_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List jobs, optionally filtered by workspace."""
    query = db.query(Job)
    if workspace_id:
        query = query.filter(Job.workspace_id == workspace_id)
    jobs = query.all()
    return jobs


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# Run endpoints
@app.post("/api/runs", response_model=RunResponse)
async def create_run(
    run: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and execute a run."""
    # Verify job exists
    job = db.query(Job).filter(Job.id == run.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create run record
    run_dict = run.dict()
    run_dict["created_by"] = current_user.username
    db_run = Run(**run_dict)
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    
    # Execute job asynchronously (in production, use Celery/worker queue)
    # For now, execute synchronously for simplicity
    try:
        if job.job_type.value == "trino_sql":
            execute_trino_sql_job(db, db_run, job)
        else:
            raise HTTPException(status_code=400, detail=f"Job type {job.job_type} not yet supported")
    except Exception as e:
        db_run.status = "failed"
        db_run.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    
    return db_run


@app.get("/api/runs", response_model=list[RunResponse])
async def list_runs(
    job_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List runs, optionally filtered by job."""
    query = db.query(Run)
    if job_id:
        query = query.filter(Run.job_id == job_id)
    runs = query.all()
    return runs


@app.get("/api/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a run by ID."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

