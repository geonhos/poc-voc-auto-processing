"""
Normalizer Agent Tests
"""

import pytest
from datetime import datetime
from app.agents.normalizer.agent import NormalizerAgent
from app.agents.normalizer.schemas import NormalizerInput
from app.models.ticket import Channel


@pytest.mark.integration
class TestNormalizerAgent:
    """Normalizer agent integration tests"""

    async def test_normalize_integration_error(self):
        """Test normalizing integration error VOC"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="어제 밤에 카드 결제를 했는데 PG사에서 결제 실패 문자가 왔어요. 근데 제 카드에서는 빠져나갔거든요? 이거 확인 좀 해주세요.",
            customer_name="김철수",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is True
        assert result.data is not None
        assert result.data.suspected_type.primary_type in [
            "integration_error",
            "code_error",
        ]
        assert result.data.urgency in ["high", "medium"]
        assert len(result.data.summary) > 0
        assert len(result.data.summary) <= 200

    async def test_normalize_code_error(self):
        """Test normalizing code error VOC"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="앱이 자꾸 튕겨요. 로그인하면 바로 크래시가 발생합니다. 진짜 너무 불편해요.",
            customer_name="이영희",
            channel=Channel.SLACK,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is True
        assert result.data is not None
        assert result.data.suspected_type.primary_type in [
            "code_error",
            "business_improvement",
        ]
        assert len(result.data.summary) > 0

    async def test_normalize_business_improvement(self):
        """Test normalizing business improvement VOC"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="다른 서비스는 자동 로그인 기능이 있는데 왜 이 앱은 매번 로그인해야 하나요? 개선 좀 해주세요.",
            customer_name="박민수",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is True
        assert result.data is not None
        assert result.data.suspected_type.primary_type in [
            "business_improvement",
            "code_error",
        ]
        assert result.data.urgency in ["low", "medium"]

    async def test_normalize_empty_voc(self):
        """Test normalizing empty VOC"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="",
            customer_name="테스트",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is False
        assert result.error is not None
        assert result.error.code == "NORMALIZATION_FAILED"

    async def test_normalize_meaningless_voc(self):
        """Test normalizing meaningless VOC"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="ㅋㅋㅋㅋㅋ",
            customer_name="익명",
            channel=Channel.SLACK,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is False
        assert result.error is not None
        assert result.error.code == "NORMALIZATION_FAILED"

    async def test_normalize_too_long_voc(self):
        """Test normalizing VOC that exceeds max length"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="테스트 " * 2000,  # > 5000 chars
            customer_name="테스트",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is False
        assert result.error is not None
        assert result.error.code == "INPUT_TOO_LONG"

    async def test_normalize_urgent_case(self):
        """Test normalizing urgent VOC (payment failure)"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="결제가 실패했는데 돈은 빠져나갔습니다. 빨리 환불 처리 해주세요.",
            customer_name="김긴급",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is True
        assert result.data is not None
        # Should be classified as high urgency due to payment issue
        assert result.data.urgency == "high"

    async def test_normalize_low_urgency_case(self):
        """Test normalizing low urgency VOC (inquiry)"""
        agent = NormalizerAgent()
        input_data = NormalizerInput(
            raw_voc="앱 사용 방법이 궁금합니다. 매뉴얼 어디서 볼 수 있나요?",
            customer_name="김문의",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        assert result.success is True
        assert result.data is not None
        # Should be classified as low urgency (inquiry)
        assert result.data.urgency == "low"


@pytest.mark.unit
class TestNormalizerValidation:
    """Normalizer validation tests"""

    async def test_summary_max_length(self):
        """Test that summary is truncated if too long"""
        agent = NormalizerAgent()
        # Create a long VOC that might generate a long summary
        input_data = NormalizerInput(
            raw_voc="결제 시스템에서 오류가 발생했습니다. " * 50,
            customer_name="테스트",
            channel=Channel.EMAIL,
            received_at=datetime.now(),
        )

        result = await agent.normalize(input_data)

        if result.success and result.data:
            # Summary should not exceed 200 characters
            assert len(result.data.summary) <= 200
