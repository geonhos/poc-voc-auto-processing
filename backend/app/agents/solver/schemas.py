"""
Solver Agent Input/Output Schemas
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class SolverAgentInput(BaseModel):
    """Input schema for Solver Agent"""
    ticket_id: str = Field(..., description="VOC ticket ID")
    raw_voc: str = Field(..., description="Raw VOC text from user")
    received_at: datetime = Field(..., description="VOC received timestamp")


class ConfidenceScore(BaseModel):
    """Confidence score breakdown"""
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    error_pattern_clarity: float = Field(..., ge=0.0, le=1.0, description="Error pattern clarity score")
    log_voc_correlation: float = Field(..., ge=0.0, le=1.0, description="Log-VOC correlation score")
    similar_case_match: float = Field(..., ge=0.0, le=1.0, description="Similar case match score")
    system_info_availability: float = Field(..., ge=0.0, le=1.0, description="System info availability score")


class ActionProposal(BaseModel):
    """Action proposal for resolving the issue"""
    action_type: Literal["integration_inquiry", "code_fix", "business_proposal"]
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed action description")
    target_system: Optional[str] = Field(None, description="Target system (for integration_inquiry)")
    contact_info: Optional[str] = Field(None, description="Contact info (for integration_inquiry)")
    code_location: Optional[str] = Field(None, description="Code location (for code_fix)")
    error_details: Optional[str] = Field(None, description="Error details (for code_fix)")
    business_impact: Optional[str] = Field(None, description="Business impact (for business_proposal)")
    suggested_improvement: Optional[str] = Field(None, description="Suggested improvement (for business_proposal)")


class SolverAgentOutput(BaseModel):
    """Output schema for Solver Agent"""
    ticket_id: str
    problem_type_primary: Literal["integration_error", "code_error", "business_improvement"]
    problem_type_secondary: Optional[str] = None
    affected_system: Optional[str] = None

    # Analysis results
    root_cause_analysis: str = Field(..., description="Root cause analysis summary")
    evidence_summary: str = Field(..., description="Evidence from logs and similar cases")

    # Confidence and state
    confidence: ConfidenceScore
    state: Literal["WAITING_CONFIRM", "MANUAL_REQUIRED"]

    # Action proposal
    action_proposal: ActionProposal

    # Supporting data
    similar_cases_used: List[str] = Field(default_factory=list, description="Ticket IDs of similar cases")
    log_summary: Optional[str] = None
    analyzed_at: datetime = Field(default_factory=datetime.now)


class SolverAnalysisContext(BaseModel):
    """Internal context used during analysis"""
    ticket_id: str
    raw_voc: str
    received_at: datetime

    # Retrieved data
    logs: List[dict] = Field(default_factory=list)
    error_patterns: Optional[dict] = None
    similar_cases: List[dict] = Field(default_factory=list)
    system_info: Optional[dict] = None

    # Analysis progress
    problem_type_identified: bool = False
    confidence_calculated: bool = False
    action_generated: bool = False
