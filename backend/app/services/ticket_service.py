"""
Ticket business logic service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import VOCCreate


def generate_ticket_id() -> str:
    """Generate ticket ID in format VOC-YYYYMMDD-XXXX"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    # TODO: Implement proper sequence number generation
    # For now, use timestamp
    seq = now.strftime("%H%M")
    return f"VOC-{date_str}-{seq}"


class TicketService:
    """Ticket service for business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(self, voc: VOCCreate) -> Ticket:
        """Create a new ticket from VOC input"""
        ticket = Ticket(
            ticket_id=generate_ticket_id(),
            status=TicketStatus.OPEN,
            raw_voc=voc.raw_voc,
            customer_name=voc.customer_name,
            channel=voc.channel,
            received_at=voc.received_at,
        )

        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        result = await self.db.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def list_tickets(
        self,
        status: Optional[List[TicketStatus]] = None,
        urgency: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Ticket], int]:
        """List tickets with filtering and pagination"""
        # Build query
        query = select(Ticket)

        # Apply filters
        if status:
            query = query.where(Ticket.status.in_(status))
        if urgency:
            query = query.where(Ticket.urgency == urgency)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(desc(Ticket.created_at))
        query = query.offset((page - 1) * limit).limit(limit)

        # Execute
        result = await self.db.execute(query)
        tickets = list(result.scalars().all())

        return tickets, total_count

    async def confirm_ticket(
        self, ticket_id: str, assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Confirm a ticket (WAITING_CONFIRM -> DONE)"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        if ticket.status != TicketStatus.WAITING_CONFIRM:
            raise ValueError(
                f"Cannot confirm ticket in status {ticket.status}. "
                f"Expected {TicketStatus.WAITING_CONFIRM}"
            )

        ticket.status = TicketStatus.DONE
        ticket.confirmed_at = datetime.utcnow()
        if assignee:
            ticket.assignee = assignee

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def reject_ticket(
        self, ticket_id: str, reject_reason: str, assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Reject a ticket (WAITING_CONFIRM -> REJECTED)"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        if ticket.status != TicketStatus.WAITING_CONFIRM:
            raise ValueError(
                f"Cannot reject ticket in status {ticket.status}. "
                f"Expected {TicketStatus.WAITING_CONFIRM}"
            )

        ticket.status = TicketStatus.REJECTED
        ticket.reject_reason = reject_reason
        ticket.confirmed_at = datetime.utcnow()
        if assignee:
            ticket.assignee = assignee

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def retry_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Retry ticket analysis (WAITING_CONFIRM -> ANALYZING)"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        if ticket.status != TicketStatus.WAITING_CONFIRM:
            raise ValueError(
                f"Cannot retry ticket in status {ticket.status}. "
                f"Expected {TicketStatus.WAITING_CONFIRM}"
            )

        ticket.status = TicketStatus.ANALYZING

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def complete_manual_ticket(
        self, ticket_id: str, manual_resolution: str, assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Complete manual ticket (MANUAL_REQUIRED -> DONE)"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        if ticket.status != TicketStatus.MANUAL_REQUIRED:
            raise ValueError(
                f"Cannot complete ticket in status {ticket.status}. "
                f"Expected {TicketStatus.MANUAL_REQUIRED}"
            )

        ticket.status = TicketStatus.DONE
        ticket.manual_resolution = manual_resolution
        ticket.confirmed_at = datetime.utcnow()
        if assignee:
            ticket.assignee = assignee

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket
