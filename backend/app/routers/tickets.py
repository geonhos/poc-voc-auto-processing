"""
Ticket management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.database import get_db
from app.schemas.ticket import (
    TicketDetail, TicketListResponse, TicketSummary,
    TicketConfirm, TicketReject, TicketComplete
)
from app.services.ticket_service import TicketService
from app.models.ticket import TicketStatus

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[List[TicketStatus]] = Query(None),
    urgency: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List tickets with optional filtering

    - **status**: Filter by status (can specify multiple)
    - **urgency**: Filter by urgency (low/medium/high)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    service = TicketService(db)
    tickets, total_count = await service.list_tickets(
        status=status,
        urgency=urgency,
        page=page,
        limit=limit
    )

    return TicketListResponse(
        tickets=[TicketSummary.model_validate(t) for t in tickets],
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=math.ceil(total_count / limit) if total_count > 0 else 0
    )


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get ticket details by ID"""
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )

    return TicketDetail.model_validate(ticket)


@router.post("/{ticket_id}/confirm", response_model=TicketDetail)
async def confirm_ticket(
    ticket_id: str,
    data: TicketConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Confirm a ticket (WAITING_CONFIRM -> DONE)"""
    service = TicketService(db)

    try:
        ticket = await service.confirm_ticket(ticket_id, data.assignee)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        return TicketDetail.model_validate(ticket)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{ticket_id}/reject", response_model=TicketDetail)
async def reject_ticket(
    ticket_id: str,
    data: TicketReject,
    db: AsyncSession = Depends(get_db)
):
    """Reject a ticket (WAITING_CONFIRM -> REJECTED)"""
    service = TicketService(db)

    try:
        ticket = await service.reject_ticket(
            ticket_id, data.reject_reason, data.assignee
        )
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        return TicketDetail.model_validate(ticket)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{ticket_id}/retry", response_model=TicketDetail)
async def retry_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retry ticket analysis (WAITING_CONFIRM -> ANALYZING)"""
    service = TicketService(db)

    try:
        ticket = await service.retry_ticket(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        return TicketDetail.model_validate(ticket)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{ticket_id}/complete", response_model=TicketDetail)
async def complete_manual_ticket(
    ticket_id: str,
    data: TicketComplete,
    db: AsyncSession = Depends(get_db)
):
    """Complete manual ticket (MANUAL_REQUIRED -> DONE)"""
    service = TicketService(db)

    try:
        ticket = await service.complete_manual_ticket(
            ticket_id, data.manual_resolution, data.assignee
        )
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        return TicketDetail.model_validate(ticket)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
