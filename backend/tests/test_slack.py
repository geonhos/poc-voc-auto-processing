"""
Slack Service Tests
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.slack_service import SlackService, slack_service


class TestSlackService:
    """Slack 서비스 테스트"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with webhook URL"""
        with patch('app.services.slack_service.settings') as mock:
            mock.slack_webhook_url = "https://hooks.slack.com/test/webhook"
            yield mock

    @pytest.fixture
    def service_with_webhook(self, mock_settings):
        """Create service with webhook URL"""
        return SlackService()

    @pytest.fixture
    def service_without_webhook(self):
        """Create service without webhook URL"""
        with patch('app.services.slack_service.settings') as mock:
            mock.slack_webhook_url = ""
            yield SlackService()

    @pytest.mark.asyncio
    async def test_send_message_success(self, service_with_webhook):
        """메시지 전송 성공 테스트"""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            result = await service_with_webhook.send_message({"text": "test"})

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self, service_with_webhook):
        """메시지 전송 실패 테스트"""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=400)

            result = await service_with_webhook.send_message({"text": "test"})

            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_no_webhook(self, service_without_webhook):
        """Webhook URL 없을 때 테스트"""
        result = await service_without_webhook.send_message({"text": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_send_urgent_ticket_notification(self, service_with_webhook):
        """긴급 티켓 알림 전송 테스트"""
        with patch.object(service_with_webhook, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await service_with_webhook.send_urgent_ticket_notification(
                ticket_id="VOC-20240115-0001",
                summary="결제 오류 발생",
                urgency="high",
                customer_name="홍길동",
                channel="email",
            )

            assert result is True
            mock_send.assert_called_once()

            # 메시지 구조 검증
            call_args = mock_send.call_args[0][0]
            assert "blocks" in call_args
            assert len(call_args["blocks"]) >= 3

    @pytest.mark.asyncio
    async def test_send_analysis_complete_notification_high_urgency(self, service_with_webhook):
        """분석 완료 알림 전송 테스트 (긴급)"""
        with patch.object(service_with_webhook, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await service_with_webhook.send_analysis_complete_notification(
                ticket_id="VOC-20240115-0001",
                primary_type="integration_error",
                confidence=0.85,
                urgency="high",
            )

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_analysis_complete_notification_not_urgent(self, service_with_webhook):
        """분석 완료 알림 전송 테스트 (긴급 아님 - 알림 안 보냄)"""
        with patch.object(service_with_webhook, 'send_message', new_callable=AsyncMock) as mock_send:
            result = await service_with_webhook.send_analysis_complete_notification(
                ticket_id="VOC-20240115-0001",
                primary_type="integration_error",
                confidence=0.85,
                urgency="medium",
            )

            assert result is True  # 성공으로 처리 (알림 안 보내도 됨)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_exception_handling(self, service_with_webhook):
        """예외 처리 테스트"""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection error")

            result = await service_with_webhook.send_message({"text": "test"})

            assert result is False
