"""Database models for control plane."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class ConnectionType(str, enum.Enum):
    """Types of connections."""
    MINIO = "minio"
    TRINO = "trino"
    SPARK = "spark"
    POSTGRES = "postgres"
    ICEBERG_CATALOG = "iceberg_catalog"


class JobType(str, enum.Enum):
    """Types of jobs."""
    TRINO_SQL = "trino_sql"
    SPARK_BATCH = "spark_batch"


class RunStatus(str, enum.Enum):
    """Status of a run."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"


class Workspace(Base):
    """Workspace model."""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    connections = relationship("Connection", back_populates="workspace", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="workspace", cascade="all, delete-orphan")


class Connection(Base):
    """Connection model."""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    connection_type = Column(Enum(ConnectionType), nullable=False)
    config = Column(JSON, nullable=False)  # Store connection config (endpoints, credentials reference)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="connections")
    jobs = relationship("Job", back_populates="connection")


class Job(Base):
    """Job model."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    job_type = Column(Enum(JobType), nullable=False)
    definition = Column(JSON, nullable=False)  # Job-specific config (SQL query, Spark config, etc.)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)

    workspace = relationship("Workspace", back_populates="jobs")
    connection = relationship("Connection", back_populates="jobs")
    runs = relationship("Run", back_populates="job", cascade="all, delete-orphan")


class Run(Base):
    """Run model."""
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING, nullable=False, index=True)
    parameters = Column(JSON, nullable=True)  # Runtime parameters
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    logs_url = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)  # Run results/metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)

    job = relationship("Job", back_populates="runs")


class User(Base):
    """User model (simple auth for dev phase)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(255), nullable=False, index=True)  # e.g., "create_job", "run_job"
    resource_type = Column(String(255), nullable=True)  # e.g., "job", "connection"
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

