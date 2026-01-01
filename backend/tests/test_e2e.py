"""
E2E Integration Tests
End-to-End 시나리오 테스트
"""

import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient

from app.models.ticket import TicketStatus, Channel, Urgency

# API prefix
API_V1 = "/api/v1"


class TestE2ENormalFlow:
    """정상 흐름 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_tc001_integration_error_flow(self, client: AsyncClient):
        """
        TC-001: 연동사 오류 VOC의 정상 처리 흐름
        VOC 입력 → 분석 → 승인 → 완료
        """
        # Step 1: VOC 입력
        voc_data = {
            "raw_voc": "어제 저녁에 결제를 시도했는데 한참 기다려도 결제가 안 되더라고요. 나중에 보니까 결제 실패로 되어 있었어요. 카드는 정상인데 왜 그런 건가요?",
            "customer_name": "김철수",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 201

        result = response.json()
        ticket_id = result["ticket_id"]
        assert ticket_id.startswith("VOC-")
        assert result["status"] == TicketStatus.OPEN.value

        # Step 2: Ticket 상세 조회 (초기 상태)
        response = await client.get(f"{API_V1}/tickets/{ticket_id}")
        assert response.status_code == 200
        ticket = response.json()
        assert ticket["raw_voc"] == voc_data["raw_voc"]

    @pytest.mark.asyncio
    async def test_tc002_code_error_flow(self, client: AsyncClient):
        """
        TC-002: 코드 오류 VOC의 정상 처리 흐름
        """
        voc_data = {
            "raw_voc": "주문 상세 페이지에서 '환불 요청' 버튼을 누르면 에러가 뜹니다. 여러 번 시도해도 같은 에러가 나와요.",
            "customer_name": "박영희",
            "channel": Channel.SLACK.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 201

        result = response.json()
        ticket_id = result["ticket_id"]
        assert ticket_id.startswith("VOC-")

    @pytest.mark.asyncio
    async def test_tc003_business_improvement_flow(self, client: AsyncClient):
        """
        TC-003: 비즈니스 개선 VOC의 정상 처리 흐름
        """
        voc_data = {
            "raw_voc": "결제 취소하려고 하는데 버튼이 어디 있는지 모르겠어요. 주문 상세에서 한참 찾아봤는데 없고, 결국 고객센터에 전화했습니다.",
            "customer_name": "이민수",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 201

        result = response.json()
        assert result["ticket_id"].startswith("VOC-")


class TestE2EExceptionFlow:
    """예외 흐름 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_tc004_reject_flow(self, client: AsyncClient):
        """
        TC-004: 관리자 거부 처리 흐름
        """
        # VOC 생성
        voc_data = {
            "raw_voc": "테스트용 VOC 입니다. 거부 흐름을 테스트합니다.",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 201
        ticket_id = response.json()["ticket_id"]

        # 거부 사유 없이 거부 시도 - 실패해야 함
        response = await client.post(
            f"{API_V1}/tickets/{ticket_id}/reject",
            json={"reject_reason": ""}
        )
        # 빈 문자열은 유효성 검사 실패
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_tc006_normalization_failure(self, client: AsyncClient):
        """
        TC-006: 정규화 실패 - 수동 처리 흐름
        의미 없는 VOC는 정규화 실패 가능
        """
        voc_data = {
            "raw_voc": "ㅋㅋㅋㅋㅋ",
            "customer_name": "테스트",
            "channel": Channel.SLACK.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 201

        result = response.json()
        assert result["ticket_id"].startswith("VOC-")

    @pytest.mark.asyncio
    async def test_tc007_low_confidence_fallback(self, client: AsyncClient):
        """
        TC-007: 저신뢰도 - Fallback 처리
        모호한 VOC는 저신뢰도로 MANUAL_REQUIRED 가능
        """
        voc_data = {
            "raw_voc": "뭔가 이상해요. 자세히는 모르겠는데 예전이랑 다른 것 같아요.",
            "customer_name": "최지은",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 201


class TestE2EUIValidation:
    """UI 검증 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_tc010_ticket_list_filtering(self, client: AsyncClient):
        """
        TC-010: Ticket 목록 필터링
        """
        # 전체 목록 조회
        response = await client.get(f"{API_V1}/tickets")
        assert response.status_code == 200
        result = response.json()
        assert "tickets" in result
        assert "total_count" in result
        assert "page" in result
        assert "limit" in result

    @pytest.mark.asyncio
    async def test_tc010_ticket_list_status_filter(self, client: AsyncClient):
        """
        TC-010: 상태별 필터링
        """
        response = await client.get(f"{API_V1}/tickets?status=OPEN")
        assert response.status_code == 200

        response = await client.get(f"{API_V1}/tickets?status=WAITING_CONFIRM")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_tc010_ticket_list_urgency_filter(self, client: AsyncClient):
        """
        TC-010: 긴급도별 필터링
        """
        response = await client.get(f"{API_V1}/tickets?urgency=high")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_tc010_ticket_list_pagination(self, client: AsyncClient):
        """
        TC-010: 페이지네이션
        """
        response = await client.get(f"{API_V1}/tickets?page=1&limit=10")
        assert response.status_code == 200

        result = response.json()
        assert result["page"] == 1
        assert result["limit"] == 10

    @pytest.mark.asyncio
    async def test_tc011_validation_empty_voc(self, client: AsyncClient):
        """
        TC-011: VOC 내용 없이 제출 - 에러
        """
        voc_data = {
            "raw_voc": "",  # 빈 내용
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_tc011_validation_long_voc(self, client: AsyncClient):
        """
        TC-011: 5000자 초과 입력 - 에러
        """
        voc_data = {
            "raw_voc": "A" * 5001,  # 5000자 초과
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        assert response.status_code == 422  # Validation error


class TestE2ETicketActions:
    """Ticket 액션 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_confirm_action_invalid_status(self, client: AsyncClient):
        """
        승인 액션 - 잘못된 상태에서 시도
        """
        # VOC 생성 (OPEN 상태)
        voc_data = {
            "raw_voc": "테스트 VOC 입니다.",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        ticket_id = response.json()["ticket_id"]

        # OPEN 상태에서 승인 시도 - 실패해야 함
        response = await client.post(f"{API_V1}/tickets/{ticket_id}/confirm", json={})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_manual_invalid_status(self, client: AsyncClient):
        """
        수동 처리 완료 - 잘못된 상태에서 시도
        """
        # VOC 생성 (OPEN 상태)
        voc_data = {
            "raw_voc": "테스트 VOC 입니다.",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        response = await client.post(f"{API_V1}/voc", json=voc_data)
        ticket_id = response.json()["ticket_id"]

        # OPEN 상태에서 수동 처리 완료 시도 - 실패해야 함
        response = await client.post(
            f"{API_V1}/tickets/{ticket_id}/complete",
            json={"manual_resolution": "수동 처리 완료"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_ticket_not_found(self, client: AsyncClient):
        """
        존재하지 않는 Ticket 조회
        """
        response = await client.get(f"{API_V1}/tickets/VOC-99999999-9999")
        assert response.status_code == 404


class TestE2EHealthCheck:
    """헬스체크 테스트"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """
        헬스체크 엔드포인트
        """
        response = await client.get("/health")
        assert response.status_code == 200

        result = response.json()
        assert result["status"] == "healthy"
