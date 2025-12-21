"""
Service layer tests
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ticket_service import TicketService, generate_ticket_id
from app.schemas.ticket import VOCCreate
from app.models.ticket import TicketStatus, Channel


@pytest.mark.unit
class TestTicketIdGeneration:
    """Ticket ID generation tests"""

    def test_generate_ticket_id_format(self):
        """Test ticket ID format"""
        ticket_id = generate_ticket_id()
        assert ticket_id.startswith("VOC-")
        parts = ticket_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 4  # HHMM


@pytest.mark.integration
class TestTicketService:
    """Ticket service tests"""

    async def test_create_ticket(self, test_db: AsyncSession):
        """Test ticket creation"""
        service = TicketService(test_db)
        voc_data = VOCCreate(
            raw_voc="테스트 VOC 내용",
            customer_name="홍길동",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        ticket = await service.create_ticket(voc_data)
        assert ticket.ticket_id is not None
        assert ticket.status == TicketStatus.OPEN
        assert ticket.raw_voc == voc_data.raw_voc
        assert ticket.customer_name == voc_data.customer_name

    async def test_get_ticket(self, test_db: AsyncSession):
        """Test getting ticket by ID"""
        service = TicketService(test_db)
        voc_data = VOCCreate(
            raw_voc="테스트 VOC",
            customer_name="테스터",
            channel=Channel.SLACK,
            received_at=datetime.now(),
        )

        # Create ticket
        created_ticket = await service.create_ticket(voc_data)

        # Get ticket
        ticket = await service.get_ticket(created_ticket.ticket_id)
        assert ticket is not None
        assert ticket.ticket_id == created_ticket.ticket_id
        assert ticket.raw_voc == voc_data.raw_voc

    async def test_get_ticket_not_found(self, test_db: AsyncSession):
        """Test getting non-existent ticket"""
        service = TicketService(test_db)
        ticket = await service.get_ticket("VOC-99999999-9999")
        assert ticket is None

    async def test_list_tickets(self, test_db: AsyncSession):
        """Test listing tickets"""
        service = TicketService(test_db)

        # Create multiple tickets
        for i in range(3):
            voc_data = VOCCreate(
                raw_voc=f"VOC {i}",
                customer_name=f"Customer {i}",
                channel=Channel.EMAIL,
                received_at=datetime.now(),
            )
            await service.create_ticket(voc_data)

        # List all tickets
        tickets, total = await service.list_tickets()
        assert len(tickets) == 3
        assert total == 3

    async def test_list_tickets_pagination(self, test_db: AsyncSession):
        """Test ticket list pagination"""
        service = TicketService(test_db)

        # Create 5 tickets
        for i in range(5):
            voc_data = VOCCreate(
                raw_voc=f"VOC {i}",
                customer_name=f"Customer {i}",
                channel=Channel.EMAIL,
                received_at=datetime.now(),
            )
            await service.create_ticket(voc_data)

        # Get page 1 with limit 2
        tickets, total = await service.list_tickets(page=1, limit=2)
        assert len(tickets) == 2
        assert total == 5

        # Get page 2
        tickets, total = await service.list_tickets(page=2, limit=2)
        assert len(tickets) == 2
        assert total == 5

    async def test_list_tickets_filter_by_status(self, test_db: AsyncSession):
        """Test filtering tickets by status"""
        service = TicketService(test_db)

        # Create ticket
        voc_data = VOCCreate(
            raw_voc="Test VOC",
            customer_name="Test User",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )
        await service.create_ticket(voc_data)

        # Filter by OPEN status
        tickets, total = await service.list_tickets(status=[TicketStatus.OPEN])
        assert len(tickets) == 1
        assert total == 1

        # Filter by DONE status (should be empty)
        tickets, total = await service.list_tickets(status=[TicketStatus.DONE])
        assert len(tickets) == 0
        assert total == 0

    async def test_confirm_ticket(self, test_db: AsyncSession):
        """Test confirming a ticket"""
        service = TicketService(test_db)

        # Create and prepare ticket for confirmation
        voc_data = VOCCreate(
            raw_voc="Test",
            customer_name="User",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )
        ticket = await service.create_ticket(voc_data)

        # Manually set status to WAITING_CONFIRM (normally done by agent)
        ticket.status = TicketStatus.WAITING_CONFIRM
        await test_db.commit()

        # Confirm ticket
        confirmed = await service.confirm_ticket(ticket.ticket_id, "admin@test.com")
        assert confirmed is not None
        assert confirmed.status == TicketStatus.DONE
        assert confirmed.assignee == "admin@test.com"
        assert confirmed.confirmed_at is not None

    async def test_confirm_ticket_invalid_status(self, test_db: AsyncSession):
        """Test confirming ticket with invalid status"""
        service = TicketService(test_db)

        # Create ticket (status=OPEN)
        voc_data = VOCCreate(
            raw_voc="Test",
            customer_name="User",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )
        ticket = await service.create_ticket(voc_data)

        # Try to confirm ticket with OPEN status (should fail)
        with pytest.raises(ValueError):
            await service.confirm_ticket(ticket.ticket_id)

    async def test_reject_ticket(self, test_db: AsyncSession):
        """Test rejecting a ticket"""
        service = TicketService(test_db)

        # Create and prepare ticket
        voc_data = VOCCreate(
            raw_voc="Test",
            customer_name="User",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )
        ticket = await service.create_ticket(voc_data)

        # Set to WAITING_CONFIRM
        ticket.status = TicketStatus.WAITING_CONFIRM
        await test_db.commit()

        # Reject ticket
        rejected = await service.reject_ticket(
            ticket.ticket_id, "분석 결과가 정확하지 않음", "admin@test.com"
        )
        assert rejected is not None
        assert rejected.status == TicketStatus.REJECTED
        assert rejected.reject_reason == "분석 결과가 정확하지 않음"
        assert rejected.assignee == "admin@test.com"

    async def test_retry_ticket(self, test_db: AsyncSession):
        """Test retrying ticket analysis"""
        service = TicketService(test_db)

        # Create and prepare ticket
        voc_data = VOCCreate(
            raw_voc="Test",
            customer_name="User",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )
        ticket = await service.create_ticket(voc_data)

        # Set to WAITING_CONFIRM
        ticket.status = TicketStatus.WAITING_CONFIRM
        await test_db.commit()

        # Retry analysis
        retried = await service.retry_ticket(ticket.ticket_id)
        assert retried is not None
        assert retried.status == TicketStatus.ANALYZING

    async def test_complete_manual_ticket(self, test_db: AsyncSession):
        """Test completing manual ticket"""
        service = TicketService(test_db)

        # Create and prepare ticket
        voc_data = VOCCreate(
            raw_voc="Test",
            customer_name="User",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )
        ticket = await service.create_ticket(voc_data)

        # Set to MANUAL_REQUIRED
        ticket.status = TicketStatus.MANUAL_REQUIRED
        await test_db.commit()

        # Complete manually
        completed = await service.complete_manual_ticket(
            ticket.ticket_id, "수동으로 처리 완료", "admin@test.com"
        )
        assert completed is not None
        assert completed.status == TicketStatus.DONE
        assert completed.manual_resolution == "수동으로 처리 완료"
        assert completed.assignee == "admin@test.com"
