"""
Ticket schemas for request/response
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.ticket import TicketStatus, Channel, Urgency


# VOC Input Schema
class VOCCreate(BaseModel):
    """Schema for creating a VOC"""
    raw_voc: str = Field(..., min_length=1, max_length=5000)
    customer_name: str = Field(..., min_length=1, max_length=100)
    channel: Channel
    received_at: datetime


# Ticket Response Schemas
class ProblemType(BaseModel):
    """Problem type schema"""
    primary_type: str
    secondary_type: Optional[str] = None


class DecisionReason(BaseModel):
    """Decision reason schema"""
    summary: str
    evidence: List[str]
    ruled_out: List[str]


class TicketBase(BaseModel):
    """Base ticket schema"""
    ticket_id: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime


class TicketSummary(TicketBase):
    """Ticket summary for list view"""
    summary: Optional[str] = None
    urgency: Optional[Urgency] = None
    customer_name: str
    decision_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class TicketDetail(TicketBase):
    """Ticket detail for single view"""
    assignee: Optional[str] = None

    # VOC input
    raw_voc: str
    customer_name: str
    channel: Channel
    received_at: datetime

    # Normalization result
    summary: Optional[str] = None
    suspected_type_primary: Optional[str] = None
    suspected_type_secondary: Optional[str] = None
    affected_system: Optional[str] = None
    urgency: Optional[Urgency] = None

    # Agent analysis
    agent_decision_primary: Optional[str] = None
    agent_decision_secondary: Optional[str] = None
    decision_confidence: Optional[float] = None
    decision_reason: Optional[dict] = None
    action_proposal: Optional[dict] = None
    analyzed_at: Optional[datetime] = None

    # Admin action
    confirmed_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    manual_resolution: Optional[str] = None

    class Config:
        from_attributes = True


# Action Schemas
class TicketConfirm(BaseModel):
    """Schema for confirming a ticket"""
    assignee: Optional[str] = None


class TicketReject(BaseModel):
    """Schema for rejecting a ticket"""
    reject_reason: str = Field(..., min_length=1)
    assignee: Optional[str] = None


class TicketComplete(BaseModel):
    """Schema for completing manual ticket"""
    manual_resolution: str = Field(..., min_length=1)
    assignee: Optional[str] = None


# Response Schemas
class TicketCreateResponse(BaseModel):
    """Response after creating a ticket"""
    ticket_id: str
    status: TicketStatus
    message: str


class TicketListResponse(BaseModel):
    """Response for ticket list"""
    tickets: List[TicketSummary]
    total_count: int
    page: int
    limit: int
    total_pages: int
