"""
Mock Log Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Mock log entry"""

    timestamp: datetime = Field(..., description="Log timestamp")
    level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = Field(..., description="Log level")
    service: str = Field(..., description="Service/module name")
    message: str = Field(..., description="Log message")
    error_code: Optional[str] = Field(None, description="Error code")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogQueryParams(BaseModel):
    """Parameters for log query"""

    service: str = Field(..., description="Service name to query")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    level: Optional[Literal["DEBUG", "INFO", "WARN", "ERROR"]] = Field(None, description="Filter by level")
    limit: int = Field(100, description="Max number of logs", ge=1, le=100)


class LogQueryResult(BaseModel):
    """Result of log query"""

    logs: list[LogEntry] = Field(default_factory=list)
    total_count: int = Field(0, description="Total matching logs")
    filtered_count: int = Field(0, description="Count after limit applied")
