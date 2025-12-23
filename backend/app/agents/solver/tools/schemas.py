"""
Tool schemas for Solver Agent
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# get_logs tool
class GetLogsInput(BaseModel):
    """Input for get_logs tool"""

    service: str = Field(..., description="Service name to query logs from")
    start_time: datetime = Field(..., description="Start time for log query")
    end_time: datetime = Field(..., description="End time for log query")
    level: Optional[str] = Field(None, description="Filter by log level (DEBUG, INFO, WARN, ERROR)")
    limit: int = Field(100, description="Maximum number of logs to return", ge=1, le=100)


class GetLogsOutput(BaseModel):
    """Output from get_logs tool"""

    logs: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved log entries")
    total_count: int = Field(0, description="Total matching logs")


# analyze_error_patterns tool
class AnalyzeErrorPatternsInput(BaseModel):
    """Input for analyze_error_patterns tool"""

    logs: List[Dict[str, Any]] = Field(..., description="Log entries to analyze")


class ErrorSummary(BaseModel):
    """Summary of an error pattern"""

    error_code: str = Field(..., description="Error code")
    count: int = Field(..., description="Number of occurrences")
    first_occurrence: datetime = Field(..., description="First occurrence timestamp")
    last_occurrence: datetime = Field(..., description="Last occurrence timestamp")
    sample_message: str = Field(..., description="Sample error message")


class ExternalSystemError(BaseModel):
    """External system error summary"""

    system: str = Field(..., description="External system name")
    error_count: int = Field(..., description="Number of errors")


class AnalyzeErrorPatternsOutput(BaseModel):
    """Output from analyze_error_patterns tool"""

    error_summary: List[ErrorSummary] = Field(default_factory=list, description="Error summaries grouped by code")
    stack_trace_patterns: List[str] = Field(default_factory=list, description="Common stack trace patterns")
    external_system_errors: List[ExternalSystemError] = Field(default_factory=list, description="External system errors")
    total_errors: int = Field(0, description="Total error count")
    total_warnings: int = Field(0, description="Total warning count")


# get_system_info tool
class GetSystemInfoInput(BaseModel):
    """Input for get_system_info tool"""

    system_name: str = Field(..., description="System name to query")


class GetSystemInfoOutput(BaseModel):
    """Output from get_system_info tool"""

    system_name: str = Field(..., description="System name")
    type: str = Field(..., description="System type (internal/external)")
    contact_info: Optional[str] = Field(None, description="Contact information")
    recent_incidents: List[str] = Field(default_factory=list, description="Recent incidents")


# search_similar_vocs tool
class SearchSimilarVocsInput(BaseModel):
    """Input for search_similar_vocs tool"""

    query: str = Field(..., description="VOC text to search for similar cases")
    top_k: int = Field(5, description="Number of similar cases to return", ge=1, le=10)
    min_similarity: float = Field(0.5, description="Minimum similarity threshold", ge=0.0, le=1.0)


class SimilarVocCase(BaseModel):
    """Similar VOC case"""

    ticket_id: str = Field(..., description="Ticket ID")
    similarity_score: float = Field(..., description="Similarity score")
    problem_type_primary: Optional[str] = Field(None, description="Primary problem type")
    problem_type_secondary: Optional[str] = Field(None, description="Secondary problem type")
    resolution: Optional[str] = Field(None, description="Resolution description")
    summary: Optional[str] = Field(None, description="VOC summary")


class SearchSimilarVocsOutput(BaseModel):
    """Output from search_similar_vocs tool"""

    similar_cases: List[SimilarVocCase] = Field(default_factory=list, description="Similar VOC cases")
    total_found: int = Field(0, description="Total cases found")
