"""
Pydantic schemas for API request/response models
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionCreate(BaseModel):
    workspace_id: int
    name: str = Field(..., min_length=1, max_length=255)
    connection_type: str
    config: Dict[str, Any]
    is_active: bool = True


class ConnectionResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    connection_type: str
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    workspace_id: int
    name: str = Field(..., min_length=1, max_length=255)
    job_type: str
    definition: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = True


class JobResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    job_type: str
    definition: Dict[str, Any]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunCreate(BaseModel):
    job_id: int
    parameters: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    id: int
    job_id: int
    status: str
    parameters: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    artifacts: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




