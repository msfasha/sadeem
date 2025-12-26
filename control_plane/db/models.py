"""
SQLAlchemy models for platform metadata
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class RunStatus(str, Enum):
    """Run execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type"""
    TRINO_SQL = "trino_sql"
    SPARK_BATCH = "spark_batch"


class ConnectionType(str, Enum):
    """Connection type"""
    MINIO = "minio"
    S3 = "s3"
    TRINO = "trino"
    SPARK = "spark"
    POSTGRES = "postgres"


class Workspace(Base):
    """Workspace (logical tenant)"""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    connections = relationship("Connection", back_populates="workspace", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="workspace", cascade="all, delete-orphan")


class Connection(Base):
    """Connection configuration to external services"""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    connection_type = Column(String(50), nullable=False)  # ConnectionType enum value
    config = Column(JSON, nullable=False)  # Connection-specific config (endpoints, credentials refs)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="connections")


class Job(Base):
    """Job definition (versioned work)"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    job_type = Column(String(50), nullable=False)  # JobType enum value
    definition = Column(JSON, nullable=False)  # Job-specific definition (SQL, Spark config, etc.)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="jobs")
    runs = relationship("Run", back_populates="job", cascade="all, delete-orphan")


class Run(Base):
    """Run (execution instance of a job)"""
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    status = Column(String(50), default=RunStatus.QUEUED.value, nullable=False, index=True)
    parameters = Column(JSON, nullable=True)  # Runtime parameters
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    artifacts = Column(JSON, nullable=True)  # Links to logs, results, query IDs, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="runs")


class AuditEvent(Base):
    """Audit log for control plane actions"""
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True)  # Will be populated when auth is added
    action = Column(String(255), nullable=False)  # e.g., "create_workspace", "run_job"
    resource_type = Column(String(100), nullable=False)  # e.g., "workspace", "job", "run"
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# Database session factory (will be configured in app startup)
engine = None
SessionLocal = None


def init_db(database_url: str):
    """Initialize database engine and session factory"""
    global engine, SessionLocal
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




