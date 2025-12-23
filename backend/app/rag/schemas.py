"""
RAG module schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class VocDocument(BaseModel):
    """VOC document for vector store"""

    ticket_id: str = Field(..., description="Ticket ID")
    raw_voc: str = Field(..., description="Original VOC text")
    summary: Optional[str] = Field(None, description="Normalized summary")

    # Classification
    problem_type_primary: Optional[str] = Field(None, description="Primary problem type")
    problem_type_secondary: Optional[str] = Field(None, description="Secondary problem type")
    affected_system: Optional[str] = Field(None, description="Affected system")

    # Resolution
    resolution: Optional[str] = Field(None, description="Resolution description")
    action_proposal: Optional[dict] = Field(None, description="Action proposal")

    # Metadata
    confidence: Optional[float] = Field(None, description="Decision confidence")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    def to_text(self) -> str:
        """Convert to searchable text"""
        parts = [self.raw_voc]
        if self.summary:
            parts.append(self.summary)
        return " ".join(parts)

    def to_metadata(self) -> dict:
        """Convert to ChromaDB metadata"""
        metadata = {
            "ticket_id": self.ticket_id,
            "problem_type_primary": self.problem_type_primary or "",
            "problem_type_secondary": self.problem_type_secondary or "",
            "affected_system": self.affected_system or "",
            "confidence": self.confidence or 0.0,
        }
        if self.resolved_at:
            metadata["resolved_at"] = self.resolved_at.isoformat()
        return metadata


class SearchResult(BaseModel):
    """Search result from vector store"""

    document: VocDocument = Field(..., description="Retrieved VOC document")
    similarity_score: float = Field(..., description="Similarity score (0-1)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SimilarCasesContext(BaseModel):
    """Context for agent prompt injection"""

    similar_cases: List[SearchResult] = Field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Format for agent prompt"""
        if not self.similar_cases:
            return "유사한 과거 VOC 사례가 없습니다."

        lines = ["## 유사한 과거 VOC 사례"]
        for i, result in enumerate(self.similar_cases, 1):
            doc = result.document
            lines.append(f"\n### 사례 {i} (유사도: {result.similarity_score:.2%})")
            lines.append(f"- **문제 유형**: {doc.problem_type_primary or 'N/A'} > {doc.problem_type_secondary or 'N/A'}")
            lines.append(f"- **영향 시스템**: {doc.affected_system or 'N/A'}")
            lines.append(f"- **VOC 요약**: {doc.summary or doc.raw_voc[:100]}")
            if doc.resolution:
                lines.append(f"- **해결 방법**: {doc.resolution}")

        return "\n".join(lines)
