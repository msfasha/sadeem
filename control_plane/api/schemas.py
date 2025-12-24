"""Pydantic schemas for API."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from db.models import ConnectionType, JobType, RunStatus, UserRole


# Connection schemas
class ConnectionBase(BaseModel):
    name: str
    connection_type: ConnectionType
    config: Dict[str, Any]


class ConnectionCreate(ConnectionBase):
    workspace_id: int


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class ConnectionResponse(ConnectionBase):
    id: int
    workspace_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Job schemas
class JobBase(BaseModel):
    name: str
    description: Optional[str] = None
    job_type: JobType
    definition: Dict[str, Any]


class JobCreate(JobBase):
    workspace_id: int
    connection_id: Optional[int] = None


class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


class JobResponse(JobBase):
    id: int
    workspace_id: int
    connection_id: Optional[int]
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


# Run schemas
class RunCreate(BaseModel):
    job_id: int
    parameters: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    id: int
    job_id: int
    status: RunStatus
    parameters: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    logs_url: Optional[str]
    error_message: Optional[str]
    result: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


# Workspace schemas
class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceResponse(WorkspaceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User schemas (simple auth)
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: UserRole = UserRole.USER


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

