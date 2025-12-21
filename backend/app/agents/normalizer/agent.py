"""
Normalizer Agent Implementation
"""

import json
import re
from typing import Optional
import asyncio

from app.agents.normalizer.schemas import (
    NormalizerInput,
    NormalizerOutput,
    NormalizerData,
    NormalizerError,
)
from app.agents.normalizer.prompts import SYSTEM_PROMPT, create_user_prompt
from app.services.llm_service import get_llm_service


class NormalizerAgent:
    """Normalizer Agent for converting raw VOC to structured data"""

    def __init__(self):
        """Initialize normalizer agent"""
        self.llm_service = get_llm_service()
        self.timeout = 60  # 60 seconds timeout

    async def normalize(self, input_data: NormalizerInput) -> NormalizerOutput:
        """
        Normalize VOC input to structured data

        Args:
            input_data: Raw VOC input

        Returns:
            Normalized output with success/failure status
        """
        # Validate input length
        if len(input_data.raw_voc) > 5000:
            return NormalizerOutput(
                success=False,
                error=NormalizerError(
                    code="INPUT_TOO_LONG",
                    message="VOC 내용이 너무 깁니다. 최대 5000자까지 지원합니다.",
                ),
            )

        # Check for empty or meaningless content
        if not input_data.raw_voc.strip() or len(input_data.raw_voc.strip()) < 5:
            return NormalizerOutput(
                success=False,
                error=NormalizerError(
                    code="NORMALIZATION_FAILED",
                    message="VOC 내용을 분석할 수 없습니다. 수동 분류가 필요합니다.",
                ),
            )

        try:
            # Create prompts
            user_prompt = create_user_prompt(
                raw_voc=input_data.raw_voc,
                customer_name=input_data.customer_name,
                channel=input_data.channel.value,  # Use enum value
                received_at=input_data.received_at.isoformat(),
            )

            # Call LLM with timeout
            response = await asyncio.wait_for(
                self.llm_service.generate_json(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=0.1,
                ),
                timeout=self.timeout,
            )

            # Parse JSON response
            normalized_data = self._parse_response(response)

            if normalized_data is None:
                return NormalizerOutput(
                    success=False,
                    error=NormalizerError(
                        code="NORMALIZATION_FAILED",
                        message="VOC 내용을 분석할 수 없습니다. 수동 분류가 필요합니다.",
                    ),
                )

            return NormalizerOutput(success=True, data=normalized_data)

        except asyncio.TimeoutError:
            return NormalizerOutput(
                success=False,
                error=NormalizerError(
                    code="TIMEOUT",
                    message="분석 시간이 초과되었습니다. 다시 시도해주세요.",
                ),
            )
        except Exception as e:
            return NormalizerOutput(
                success=False,
                error=NormalizerError(
                    code="NORMALIZATION_FAILED",
                    message=f"정규화 중 오류가 발생했습니다: {str(e)}",
                ),
            )

    def _parse_response(self, response: str) -> Optional[NormalizerData]:
        """
        Parse LLM response to NormalizerData

        Args:
            response: Raw LLM response

        Returns:
            Parsed NormalizerData or None if parsing fails
        """
        try:
            # Try to extract JSON from response
            # Some models may wrap JSON in markdown code blocks
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response.strip()

            # Parse JSON
            data = json.loads(json_str)

            # Validate and create NormalizerData
            normalized_data = NormalizerData.model_validate(data)

            # Additional validation
            if len(normalized_data.summary) > 200:
                # Truncate if too long
                normalized_data.summary = normalized_data.summary[:197] + "..."

            return normalized_data

        except (json.JSONDecodeError, ValueError) as e:
            # JSON parsing or validation failed
            return None
