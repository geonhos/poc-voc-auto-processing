"""
Ticket business logic service
"""

from datetime import datetime
from typing import List, Optional
import random
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketStatus, Urgency
from app.schemas.ticket import VOCCreate
from app.agents.normalizer.agent import NormalizerAgent
from app.agents.normalizer.schemas import NormalizerInput
from app.agents.solver import get_solver_agent, SolverAgentInput
from app.rag.schemas import VocDocument
from app.services.rag_service import get_rag_service


def generate_ticket_id() -> str:
    """Generate ticket ID in format VOC-YYYYMMDD-XXXX"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    # Use microseconds + random for uniqueness
    microsec = now.microsecond % 10000  # 0-9999
    rand = random.randint(0, 99)  # 0-99
    seq = f"{microsec:04d}{rand:02d}"[:4]  # Take first 4 digits
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

    async def normalize_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """
        Run normalization on a ticket

        Args:
            ticket_id: Ticket ID to normalize

        Returns:
            Updated ticket or None if not found
        """
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        # Update status to ANALYZING
        ticket.status = TicketStatus.ANALYZING
        await self.db.commit()

        # Run normalization
        normalizer = NormalizerAgent()
        normalizer_input = NormalizerInput(
            raw_voc=ticket.raw_voc,
            customer_name=ticket.customer_name,
            channel=ticket.channel,
            received_at=ticket.received_at,
        )

        result = await normalizer.normalize(normalizer_input)

        if result.success and result.data:
            # Update ticket with normalization result
            ticket.summary = result.data.summary
            ticket.suspected_type_primary = result.data.suspected_type.primary_type
            ticket.suspected_type_secondary = result.data.suspected_type.secondary_type
            ticket.affected_system = result.data.affected_system
            ticket.urgency = Urgency(result.data.urgency)
            # Move to next status (for now, set back to OPEN - will be handled by solver agent later)
            ticket.status = TicketStatus.OPEN
        else:
            # Normalization failed - mark as manual required
            ticket.status = TicketStatus.MANUAL_REQUIRED
            if result.error:
                ticket.reject_reason = f"[정규화 실패] {result.error.message}"

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def solve_ticket(self, ticket_id: str, max_retries: int = 2) -> Optional[Ticket]:
        """
        Run Solver Agent on a ticket

        Args:
            ticket_id: Ticket ID to solve
            max_retries: Maximum retry attempts

        Returns:
            Updated ticket or None if not found
        """
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        # Can only solve OPEN tickets (after normalization)
        if ticket.status != TicketStatus.OPEN:
            return ticket

        # Update status to ANALYZING
        ticket.status = TicketStatus.ANALYZING
        await self.db.commit()

        # Retry logic
        for attempt in range(max_retries + 1):
            try:
                # Run Solver Agent
                solver = get_solver_agent()
                solver_input = SolverAgentInput(
                    ticket_id=ticket.ticket_id,
                    raw_voc=ticket.raw_voc,
                    received_at=ticket.received_at,
                )

                result = await solver.solve(solver_input)

                # Update ticket with solver result
                ticket.agent_decision_primary = result.problem_type_primary
                ticket.agent_decision_secondary = result.problem_type_secondary
                ticket.affected_system = result.affected_system or ticket.affected_system
                ticket.decision_confidence = result.confidence.overall

                # Store detailed decision reason
                ticket.decision_reason = {
                    "root_cause_analysis": result.root_cause_analysis,
                    "evidence_summary": result.evidence_summary,
                    "confidence_breakdown": {
                        "error_pattern_clarity": result.confidence.error_pattern_clarity,
                        "log_voc_correlation": result.confidence.log_voc_correlation,
                        "similar_case_match": result.confidence.similar_case_match,
                        "system_info_availability": result.confidence.system_info_availability,
                    },
                    "similar_cases_used": result.similar_cases_used,
                    "log_summary": result.log_summary,
                }

                # Store action proposal
                ticket.action_proposal = {
                    "action_type": result.action_proposal.action_type,
                    "title": result.action_proposal.title,
                    "description": result.action_proposal.description,
                    "target_system": result.action_proposal.target_system,
                    "contact_info": result.action_proposal.contact_info,
                    "code_location": result.action_proposal.code_location,
                    "error_details": result.action_proposal.error_details,
                    "business_impact": result.action_proposal.business_impact,
                    "suggested_improvement": result.action_proposal.suggested_improvement,
                }

                ticket.analyzed_at = result.analyzed_at

                # Set final status based on solver state
                if result.state == "WAITING_CONFIRM":
                    ticket.status = TicketStatus.WAITING_CONFIRM
                else:  # MANUAL_REQUIRED
                    ticket.status = TicketStatus.MANUAL_REQUIRED

                await self.db.commit()
                await self.db.refresh(ticket)

                # If analysis succeeded and confidence is high, save to RAG for future learning
                if result.state == "WAITING_CONFIRM":
                    await self._save_to_rag(ticket, result)

                return ticket

            except Exception as e:
                # On last retry, mark as manual required
                if attempt == max_retries:
                    ticket.status = TicketStatus.MANUAL_REQUIRED
                    ticket.reject_reason = f"[분석 실패] {str(e)}"
                    await self.db.commit()
                    await self.db.refresh(ticket)
                    return ticket
                # Otherwise, retry
                continue

        return ticket

    async def _save_to_rag(self, ticket: Ticket, solver_result) -> None:
        """
        Save resolved ticket to RAG vector database for future learning

        Args:
            ticket: Ticket with solver results
            solver_result: SolverAgentOutput
        """
        try:
            # Only save high-confidence resolutions
            if solver_result.confidence.overall < 0.7:
                return

            # Create VOC document
            voc_doc = VocDocument(
                ticket_id=ticket.ticket_id,
                raw_voc=ticket.raw_voc,
                summary=ticket.summary,
                problem_type_primary=solver_result.problem_type_primary,
                problem_type_secondary=solver_result.problem_type_secondary,
                affected_system=solver_result.affected_system,
                resolution=solver_result.action_proposal.description,
                confidence=solver_result.confidence.overall,
                resolved_at=solver_result.analyzed_at,
            )

            # Add to vector database
            rag_service = get_rag_service()
            rag_service.add_voc_case(voc_doc)

        except Exception as e:
            # Log error but don't fail the ticket update
            print(f"Failed to save ticket {ticket.ticket_id} to RAG: {e}")

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
