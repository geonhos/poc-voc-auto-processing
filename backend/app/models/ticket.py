"""
Ticket database model
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.database import Base


class TicketStatus(str, enum.Enum):
    """Ticket status enum"""
    OPEN = "OPEN"
    ANALYZING = "ANALYZING"
    WAITING_CONFIRM = "WAITING_CONFIRM"
    DONE = "DONE"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    REJECTED = "REJECTED"


class Channel(str, enum.Enum):
    """VOC input channel enum"""
    EMAIL = "email"
    SLACK = "slack"


class Urgency(str, enum.Enum):
    """Urgency level enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ticket(Base):
    """Ticket model"""

    __tablename__ = "tickets"

    # Basic info
    ticket_id = Column(String(50), primary_key=True, index=True)
    status = Column(SQLEnum(TicketStatus), nullable=False, default=TicketStatus.OPEN, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    assignee = Column(String(100), nullable=True)

    # VOC input info
    raw_voc = Column(Text, nullable=False)
    customer_name = Column(String(100), nullable=False)
    channel = Column(SQLEnum(Channel), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)

    # Normalization result
    summary = Column(Text, nullable=True)
    suspected_type_primary = Column(String(50), nullable=True)
    suspected_type_secondary = Column(String(50), nullable=True)
    affected_system = Column(String(100), nullable=True)
    urgency = Column(SQLEnum(Urgency), nullable=True, index=True)

    # Agent analysis result
    agent_decision_primary = Column(String(50), nullable=True)
    agent_decision_secondary = Column(String(50), nullable=True)
    decision_confidence = Column(Float, nullable=True)
    decision_reason = Column(JSON, nullable=True)  # {summary, evidence[], ruled_out[]}
    action_proposal = Column(JSON, nullable=True)  # Type-specific action
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Admin action
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    reject_reason = Column(Text, nullable=True)
    manual_resolution = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Ticket {self.ticket_id} ({self.status})>"
