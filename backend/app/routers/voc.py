"""
VOC input endpoint
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.schemas.ticket import VOCCreate, TicketCreateResponse
from app.services.ticket_service import TicketService
from app.models.ticket import TicketStatus

router = APIRouter(prefix="/voc", tags=["voc"])


async def run_normalization_and_solve(ticket_id: str):
    """Background task to run normalization and solver"""
    async with async_session() as db:
        service = TicketService(db)

        # Step 1: Normalize the ticket
        ticket = await service.normalize_ticket(ticket_id)
        if not ticket:
            return

        # Step 2: If normalization succeeded, run solver
        if ticket.status == TicketStatus.OPEN:
            await service.solve_ticket(ticket_id, max_retries=2)


@router.post("", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_voc(
    voc: VOCCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a VOC and generate a ticket

    - **raw_voc**: VOC content (max 5000 chars)
    - **customer_name**: Customer name
    - **channel**: Input channel (email or slack)
    - **received_at**: When the VOC was received
    """
    service = TicketService(db)

    try:
        # Create ticket
        ticket = await service.create_ticket(voc)

        # Run normalization and solver in background
        background_tasks.add_task(run_normalization_and_solve, ticket.ticket_id)

        return TicketCreateResponse(
            ticket_id=ticket.ticket_id,
            status=ticket.status,
            message="Ticket이 생성되었습니다. 분석이 시작됩니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {str(e)}"
        )
