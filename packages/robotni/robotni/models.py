from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobCreate(BaseModel):
    name: str
    params: Optional[dict[str, Any]] = Field(default_factory=dict)


class Job(BaseModel):
    id: str
    name: str
    status: JobStatus
    params: dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
