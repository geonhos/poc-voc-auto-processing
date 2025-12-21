"""
VOC input endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ticket import VOCCreate, TicketCreateResponse
from app.services.ticket_service import TicketService
from app.models.ticket import TicketStatus

router = APIRouter(prefix="/voc", tags=["voc"])


@router.post("", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_voc(
    voc: VOCCreate,
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
        ticket = await service.create_ticket(voc)

        return TicketCreateResponse(
            ticket_id=ticket.ticket_id,
            status=ticket.status,
            message="Ticket이 생성되었습니다. 분석이 시작됩니다."
                   if ticket.status == TicketStatus.OPEN
                   else "VOC 정규화에 실패했습니다. 수동 분류가 필요합니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {str(e)}"
        )
