"""
Mock module for Issue Solver Agent
"""

from app.mock.schemas import LogEntry, LogQueryParams, LogQueryResult
from app.mock.log_service import MockLogService, get_mock_log_service

__all__ = [
    "LogEntry",
    "LogQueryParams",
    "LogQueryResult",
    "MockLogService",
    "get_mock_log_service",
]
