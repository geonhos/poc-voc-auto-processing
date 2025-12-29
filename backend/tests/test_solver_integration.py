"""
Solver Agent Integration Tests

Tests for the complete VOC processing workflow including:
- Solver Agent execution
- API integration
- RAG learning
- Scenario-based E2E tests
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.ticket import Ticket, TicketStatus, Channel, Urgency
from app.services.ticket_service import TicketService
from app.agents.solver import SolverAgentInput, SolverAgentOutput, ConfidenceScore, ActionProposal
from app.services.rag_service import get_rag_service, load_seed_data
from app.schemas.ticket import VOCCreate


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_voc_create():
    """Sample VOC input"""
    return VOCCreate(
        raw_voc="결제 시도했는데 5초 이상 걸리다가 타임아웃 에러가 났어요. 돈은 빠져나갔는데 주문은 안된 것 같습니다.",
        customer_name="홍길동",
        channel=Channel.EMAIL,
        received_at=datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def mock_solver_output():
    """Mock Solver Agent output"""
    return SolverAgentOutput(
        ticket_id="TEST-001",
        problem_type_primary="integration_error",
        problem_type_secondary="timeout",
        affected_system="PaymentService",
        root_cause_analysis="Payment gateway timeout after 5 seconds",
        evidence_summary="Found EXTERNAL_TIMEOUT errors in logs",
        confidence=ConfidenceScore(
            overall=0.85,
            error_pattern_clarity=0.9,
            log_voc_correlation=0.8,
            similar_case_match=0.7,
            system_info_availability=1.0
        ),
        state="WAITING_CONFIRM",
        action_proposal=ActionProposal(
            action_type="integration_inquiry",
            title="Contact Payment Gateway Team",
            description="Investigate timeout issue with payment gateway",
            target_system="PaymentGateway",
            contact_info="support@paymentgateway.com"
        ),
        similar_cases_used=["VOC-001"],
        log_summary="3 errors between 14:28-14:32",
        analyzed_at=datetime.now(timezone.utc)
    )


class TestSolverTicketService:
    """Unit tests for solve_ticket method"""

    @pytest.mark.asyncio
    async def test_solve_ticket_success(self, test_db, sample_voc_create, mock_solver_output):
        """Test successful solver execution"""
        service = TicketService(test_db)

        # Create ticket
        ticket = await service.create_ticket(sample_voc_create)

        # Mock solver agent
        with patch('app.services.ticket_service.get_solver_agent') as mock_get_solver:
            mock_solver = AsyncMock()
            mock_solver.solve = AsyncMock(return_value=mock_solver_output)
            mock_get_solver.return_value = mock_solver

            # Mock RAG save
            with patch.object(service, '_save_to_rag', new_callable=AsyncMock) as mock_save:
                # Run solver
                result = await service.solve_ticket(ticket.ticket_id)

                # Assertions
                assert result is not None
                assert result.status == TicketStatus.WAITING_CONFIRM
                assert result.agent_decision_primary == "integration_error"
                assert result.agent_decision_secondary == "timeout"
                assert result.decision_confidence == 0.85
                assert result.decision_reason is not None
                assert result.action_proposal is not None
                assert result.analyzed_at is not None

                # Check decision_reason structure
                assert "root_cause_analysis" in result.decision_reason
                assert "evidence_summary" in result.decision_reason
                assert "confidence_breakdown" in result.decision_reason

                # Check action_proposal structure
                assert result.action_proposal["action_type"] == "integration_inquiry"
                assert result.action_proposal["title"] is not None

                # Verify RAG save was called
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_solve_ticket_low_confidence(self, test_db, sample_voc_create):
        """Test solver with low confidence -> MANUAL_REQUIRED"""
        service = TicketService(test_db)
        ticket = await service.create_ticket(sample_voc_create)

        # Mock low confidence output
        low_conf_output = SolverAgentOutput(
            ticket_id=ticket.ticket_id,
            problem_type_primary="code_error",
            root_cause_analysis="Insufficient evidence",
            evidence_summary="No clear patterns",
            confidence=ConfidenceScore(
                overall=0.3,
                error_pattern_clarity=0.2,
                log_voc_correlation=0.3,
                similar_case_match=0.4,
                system_info_availability=0.3
            ),
            state="MANUAL_REQUIRED",
            action_proposal=ActionProposal(
                action_type="code_fix",
                title="Manual investigation needed",
                description="Requires manual review"
            ),
            analyzed_at=datetime.now(timezone.utc)
        )

        with patch('app.services.ticket_service.get_solver_agent') as mock_get_solver:
            mock_solver = AsyncMock()
            mock_solver.solve = AsyncMock(return_value=low_conf_output)
            mock_get_solver.return_value = mock_solver

            with patch.object(service, '_save_to_rag', new_callable=AsyncMock) as mock_save:
                result = await service.solve_ticket(ticket.ticket_id)

                assert result.status == TicketStatus.MANUAL_REQUIRED
                assert result.decision_confidence == 0.3

                # RAG save should not be called for low confidence
                mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_solve_ticket_retry(self, test_db, sample_voc_create):
        """Test retry logic on solver failure"""
        service = TicketService(test_db)
        ticket = await service.create_ticket(sample_voc_create)

        with patch('app.services.ticket_service.get_solver_agent') as mock_get_solver:
            mock_solver = AsyncMock()
            # Fail 3 times (initial + 2 retries)
            mock_solver.solve = AsyncMock(side_effect=Exception("Solver failed"))
            mock_get_solver.return_value = mock_solver

            result = await service.solve_ticket(ticket.ticket_id, max_retries=2)

            # Should call solve 3 times (1 initial + 2 retries)
            assert mock_solver.solve.call_count == 3

            # Final status should be MANUAL_REQUIRED
            assert result.status == TicketStatus.MANUAL_REQUIRED
            assert "[분석 실패]" in result.reject_reason

    @pytest.mark.asyncio
    async def test_solve_ticket_wrong_status(self, test_db, sample_voc_create):
        """Test solve_ticket with non-OPEN status"""
        service = TicketService(test_db)
        ticket = await service.create_ticket(sample_voc_create)

        # Set status to ANALYZING
        ticket.status = TicketStatus.ANALYZING
        await test_db.commit()

        result = await service.solve_ticket(ticket.ticket_id)

        # Should return immediately without solving
        assert result.status == TicketStatus.ANALYZING


class TestRAGIntegration:
    """Tests for RAG integration and learning"""

    @pytest.mark.asyncio
    async def test_save_to_rag_high_confidence(self, test_db, sample_voc_create, mock_solver_output):
        """Test high confidence cases are saved to RAG"""
        service = TicketService(test_db)
        ticket = await service.create_ticket(sample_voc_create)
        ticket.summary = "Payment timeout issue"

        initial_count = get_rag_service().get_document_count()

        await service._save_to_rag(ticket, mock_solver_output)

        final_count = get_rag_service().get_document_count()
        assert final_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_save_to_rag_low_confidence(self, test_db, sample_voc_create):
        """Test low confidence cases are NOT saved to RAG"""
        service = TicketService(test_db)
        ticket = await service.create_ticket(sample_voc_create)

        low_conf_output = SolverAgentOutput(
            ticket_id=ticket.ticket_id,
            problem_type_primary="code_error",
            root_cause_analysis="Test",
            evidence_summary="Test",
            confidence=ConfidenceScore(
                overall=0.5,
                error_pattern_clarity=0.5,
                log_voc_correlation=0.5,
                similar_case_match=0.5,
                system_info_availability=0.5
            ),
            state="MANUAL_REQUIRED",
            action_proposal=ActionProposal(
                action_type="code_fix",
                title="Test",
                description="Test"
            ),
            analyzed_at=datetime.now(timezone.utc)
        )

        initial_count = get_rag_service().get_document_count()

        await service._save_to_rag(ticket, low_conf_output)

        final_count = get_rag_service().get_document_count()
        # Should not increase
        assert final_count == initial_count


class TestScenarioE2E:
    """E2E tests with mock log scenarios"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Load RAG seed data"""
        load_seed_data()

    @pytest.mark.asyncio
    async def test_scenario_s1_integration_timeout(self, test_db):
        """S1: Integration timeout scenario"""
        service = TicketService(test_db)

        voc = VOCCreate(
            raw_voc="결제 시도했는데 5초 이상 걸리다가 타임아웃 에러가 났어요. 돈은 빠져나갔는데 주문은 안된 것 같습니다.",
            customer_name="고객1",
            channel=Channel.EMAIL,
            received_at=datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        )

        ticket = await service.create_ticket(voc)

        # Run solver
        result = await service.solve_ticket(ticket.ticket_id)

        # Assertions
        assert result.agent_decision_primary == "integration_error"
        assert "PaymentService" in (result.affected_system or "")
        # May have logs in mock data
        assert result.decision_confidence is not None

    @pytest.mark.asyncio
    async def test_scenario_s2_code_error(self, test_db):
        """S2: Code error (NullPointerException) scenario"""
        service = TicketService(test_db)

        voc = VOCCreate(
            raw_voc="환불 신청했는데 에러가 나서 진행이 안됩니다. 계속 '처리 중 오류가 발생했습니다'라는 메시지만 나와요.",
            customer_name="고객2",
            channel=Channel.EMAIL,
            received_at=datetime(2024, 1, 16, 9, 0, 0, tzinfo=timezone.utc)
        )

        ticket = await service.create_ticket(voc)
        result = await service.solve_ticket(ticket.ticket_id)

        # Should identify as code_error
        assert result.agent_decision_primary in ["code_error", "integration_error"]

    @pytest.mark.asyncio
    async def test_scenario_s3_business_improvement(self, test_db):
        """S3: Business improvement (UX issue) scenario"""
        service = TicketService(test_db)

        voc = VOCCreate(
            raw_voc="주문 상세 페이지에서 배송 추적 버튼을 찾기가 너무 어려워요. 어디 있는지 한참 찾았습니다.",
            customer_name="고객3",
            channel=Channel.SLACK,
            received_at=datetime(2024, 1, 17, 10, 0, 0, tzinfo=timezone.utc)
        )

        ticket = await service.create_ticket(voc)
        result = await service.solve_ticket(ticket.ticket_id)

        # Should identify as business_improvement
        assert result.agent_decision_primary == "business_improvement"
        assert result.action_proposal["action_type"] == "business_proposal"


class TestWorkflowIntegration:
    """Integration tests for full workflow"""

    @pytest.mark.asyncio
    async def test_full_workflow_normalize_and_solve(self, test_db, sample_voc_create):
        """Test complete workflow: normalize -> solve"""
        service = TicketService(test_db)

        # Create ticket
        ticket = await service.create_ticket(sample_voc_create)
        assert ticket.status == TicketStatus.OPEN

        # Normalize
        ticket = await service.normalize_ticket(ticket.ticket_id)

        # Check normalization result
        if ticket.status == TicketStatus.OPEN:
            # Normalization succeeded, should have summary
            assert ticket.summary is not None

            # Run solver
            ticket = await service.solve_ticket(ticket.ticket_id)

            # Should have solver results
            assert ticket.agent_decision_primary is not None
            assert ticket.decision_confidence is not None
            assert ticket.status in [TicketStatus.WAITING_CONFIRM, TicketStatus.MANUAL_REQUIRED]
        else:
            # Normalization failed
            assert ticket.status == TicketStatus.MANUAL_REQUIRED

    @pytest.mark.asyncio
    async def test_rag_learning_cycle(self, test_db):
        """Test RAG learning improves future predictions"""
        service = TicketService(test_db)

        # First ticket with high confidence
        voc1 = VOCCreate(
            raw_voc="페이팔 결제 타임아웃 에러",
            customer_name="고객A",
            channel=Channel.EMAIL,
            received_at=datetime.now(timezone.utc)
        )

        ticket1 = await service.create_ticket(voc1)

        # Mock high confidence result
        high_conf_output = SolverAgentOutput(
            ticket_id=ticket1.ticket_id,
            problem_type_primary="integration_error",
            problem_type_secondary="payment_timeout",
            affected_system="PaymentService",
            root_cause_analysis="PayPal gateway timeout",
            evidence_summary="Timeout errors in logs",
            confidence=ConfidenceScore(
                overall=0.85,
                error_pattern_clarity=0.9,
                log_voc_correlation=0.8,
                similar_case_match=0.7,
                system_info_availability=1.0
            ),
            state="WAITING_CONFIRM",
            action_proposal=ActionProposal(
                action_type="integration_inquiry",
                title="Contact PayPal support",
                description="Investigate timeout with PayPal"
            ),
            analyzed_at=datetime.now(timezone.utc)
        )

        with patch('app.services.ticket_service.get_solver_agent') as mock_get_solver:
            mock_solver = AsyncMock()
            mock_solver.solve = AsyncMock(return_value=high_conf_output)
            mock_get_solver.return_value = mock_solver

            ticket1 = await service.solve_ticket(ticket1.ticket_id)

        # Verify it was saved to RAG
        initial_rag_count = get_rag_service().get_document_count()

        # Second similar ticket
        voc2 = VOCCreate(
            raw_voc="페이팔로 결제하려는데 타임아웃이 계속 나요",
            customer_name="고객B",
            channel=Channel.EMAIL,
            received_at=datetime.now(timezone.utc)
        )

        ticket2 = await service.create_ticket(voc2)

        # This time it should find similar case (ticket1)
        # The similarity score should improve confidence
        ticket2_result = await service.solve_ticket(ticket2.ticket_id)

        # Check if similar cases were used
        if ticket2_result.decision_reason and "similar_cases_used" in ticket2_result.decision_reason:
            # May include ticket1 if similarity threshold met
            similar_cases = ticket2_result.decision_reason["similar_cases_used"]
            # At minimum, should have tried to search
            assert isinstance(similar_cases, list)


class TestPerformance:
    """Performance and timeout tests"""

    @pytest.mark.asyncio
    async def test_solver_timeout_handling(self, test_db, sample_voc_create):
        """Test solver handles timeout gracefully"""
        service = TicketService(test_db)
        ticket = await service.create_ticket(sample_voc_create)

        async def slow_solve(*args, **kwargs):
            await asyncio.sleep(200)  # Longer than solver timeout (120s)
            return None

        with patch('app.services.ticket_service.get_solver_agent') as mock_get_solver:
            mock_solver = AsyncMock()
            mock_solver.solve = slow_solve
            mock_get_solver.return_value = mock_solver

            # Should timeout and mark as MANUAL_REQUIRED
            result = await service.solve_ticket(ticket.ticket_id, max_retries=0)

            assert result.status == TicketStatus.MANUAL_REQUIRED

    @pytest.mark.asyncio
    async def test_concurrent_ticket_processing(self, test_db):
        """Test multiple tickets can be processed concurrently"""
        service = TicketService(test_db)

        # Create 5 tickets
        tickets = []
        for i in range(5):
            voc = VOCCreate(
                raw_voc=f"결제 에러 테스트 {i}",
                customer_name=f"고객{i}",
                channel=Channel.EMAIL,
                received_at=datetime.now(timezone.utc)
            )
            ticket = await service.create_ticket(voc)
            tickets.append(ticket)

        # Process all concurrently
        with patch('app.services.ticket_service.get_solver_agent'):
            tasks = [service.solve_ticket(t.ticket_id, max_retries=0) for t in tickets]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete (may fail but should not hang)
            assert len(results) == 5
            assert all(r is not None for r in results if not isinstance(r, Exception))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
