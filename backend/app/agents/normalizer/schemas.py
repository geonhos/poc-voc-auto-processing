"""
Normalizer Agent Schemas
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.ticket import Channel


class NormalizerInput(BaseModel):
    """Input schema for normalizer agent"""

    raw_voc: str = Field(..., description="VOC 원문")
    customer_name: str = Field(..., description="고객명")
    channel: Channel = Field(..., description="접수 채널")
    received_at: datetime = Field(..., description="접수일시")


class SuspectedType(BaseModel):
    """Suspected problem type"""

    primary_type: Literal["integration_error", "code_error", "business_improvement"] = (
        Field(..., description="주요 문제 유형")
    )
    secondary_type: Optional[
        Literal["integration_error", "code_error", "business_improvement"]
    ] = Field(None, description="부가 문제 유형")


class NormalizerData(BaseModel):
    """Normalized VOC data"""

    summary: str = Field(..., description="문제 요약 (1-2문장, 최대 200자)")
    suspected_type: SuspectedType = Field(..., description="추정 문제 유형")
    affected_system: str = Field(..., description="영향받는 시스템")
    urgency: Literal["low", "medium", "high"] = Field(..., description="긴급도")


class NormalizerError(BaseModel):
    """Normalization error"""

    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")


class NormalizerOutput(BaseModel):
    """Output schema for normalizer agent"""

    success: bool = Field(..., description="정규화 성공 여부")
    data: Optional[NormalizerData] = Field(None, description="정규화된 데이터")
    error: Optional[NormalizerError] = Field(None, description="에러 정보")
