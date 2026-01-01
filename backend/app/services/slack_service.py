"""
Slack Notification Service
"""

import httpx
import logging
from typing import Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    """Slack 알림 서비스"""

    def __init__(self):
        self.webhook_url = settings.slack_webhook_url
        self.enabled = bool(self.webhook_url)

    async def send_message(self, message: dict) -> bool:
        """Slack 메시지 전송"""
        if not self.enabled:
            logger.warning("Slack webhook URL이 설정되지 않았습니다.")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    logger.info("Slack 알림 전송 성공")
                    return True
                else:
                    logger.error(f"Slack 알림 전송 실패: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Slack 알림 전송 오류: {str(e)}")
            return False

    async def send_urgent_ticket_notification(
        self,
        ticket_id: str,
        summary: str,
        urgency: str,
        customer_name: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> bool:
        """긴급 Ticket 알림 전송"""

        urgency_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }

        emoji = urgency_emoji.get(urgency, "⚪")

        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} 긴급 VOC 티켓 생성",
                        "emoji": True,
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Ticket ID:*\n`{ticket_id}`",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*긴급도:*\n{emoji} {urgency.upper()}",
                        },
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*요약:*\n{summary}",
                    }
                },
            ]
        }

        # 고객 정보 추가
        if customer_name or channel:
            fields = []
            if customer_name:
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*고객명:*\n{customer_name}",
                })
            if channel:
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*채널:*\n{channel}",
                })
            message["blocks"].append({
                "type": "section",
                "fields": fields,
            })

        # 타임스탬프 추가
        message["blocks"].append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                }
            ]
        })

        return await self.send_message(message)

    async def send_analysis_complete_notification(
        self,
        ticket_id: str,
        primary_type: str,
        confidence: float,
        urgency: str,
    ) -> bool:
        """분석 완료 알림 전송 (긴급 티켓만)"""

        if urgency != "high":
            return True  # 긴급이 아니면 알림 안 보냄

        type_labels = {
            "integration_error": "🔗 연동사 오류",
            "code_error": "🐛 코드 오류",
            "business_improvement": "💡 비즈니스 개선",
        }

        type_label = type_labels.get(primary_type, primary_type)
        confidence_percent = int(confidence * 100)

        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ 긴급 Ticket 분석 완료",
                        "emoji": True,
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Ticket ID:*\n`{ticket_id}`",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*문제 유형:*\n{type_label}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*신뢰도:*\n{confidence_percent}%",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*상태:*\n⏳ 승인 대기 중",
                        },
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        }
                    ]
                },
            ]
        }

        return await self.send_message(message)


# 싱글톤 인스턴스
slack_service = SlackService()
