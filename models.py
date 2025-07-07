"""
Data models for Tekton pipeline statistics
"""
from datetime import datetime
from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RUNNING = "running"
    PENDING = "pending"
    UNKNOWN = "unknown"


class TaskExecution(BaseModel):
    """Single task execution details"""
    name: str
    status: TaskStatus
    duration: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class PipelineExecution(BaseModel):
    """Single pipeline execution details"""
    name: str
    pipelinerun_name: Optional[str] = None
    status: TaskStatus
    success_rate: Optional[float] = None
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    tasks: List[TaskExecution] = Field(default_factory=list)
    duration: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pipeline_logs_url: Optional[str] = None
    troubleshooting_guide_url: Optional[str] = None
    restart_command: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    comment_id: Optional[int] = None
    repository: Optional[str] = None
    parsed_at: datetime = Field(default_factory=datetime.now)


class PipelineStatistics(BaseModel):
    """Aggregated statistics for a pipeline"""
    name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    task_statistics: Dict[str, Dict[str, Union[int, float]]] = Field(default_factory=dict)
    average_duration: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    repositories: List[str] = Field(default_factory=list)


class StatisticsDatabase(BaseModel):
    """Container for all pipeline statistics"""
    pipelines: Dict[str, PipelineStatistics] = Field(default_factory=dict)
    executions: List[PipelineExecution] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_executions: int = 0
    repositories: List[str] = Field(default_factory=list)
