"""
RAG Service for VOC similarity search and knowledge management
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from app.rag import VocRetriever, VocDocument, SearchResult, SimilarCasesContext
from app.rag.retriever import get_retriever
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# Seed data path
SEED_DATA_PATH = Path(__file__).parent.parent / "data" / "seed" / "sample_vocs.json"


class RagService:
    """Service for RAG operations"""

    def __init__(self, retriever: Optional[VocRetriever] = None):
        self._retriever = retriever or get_retriever()

    def search_similar_vocs(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.5,
    ) -> List[SearchResult]:
        """Search for similar VOC cases"""
        return self._retriever.retrieve_similar_cases(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
        )

    def get_agent_context(self, voc_text: str, top_k: int = 3) -> str:
        """Get context string for agent prompt"""
        context = self._retriever.get_context_for_agent(voc_text, top_k=top_k)
        return context.to_prompt_context()

    def add_voc_case(self, document: VocDocument) -> None:
        """Add a VOC case document to the knowledge base"""
        self._retriever.add_resolved_case(document)

    def add_resolved_ticket(
        self,
        ticket_id: str,
        raw_voc: str,
        summary: Optional[str] = None,
        problem_type_primary: Optional[str] = None,
        problem_type_secondary: Optional[str] = None,
        affected_system: Optional[str] = None,
        resolution: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> None:
        """Add a resolved ticket to the knowledge base"""
        document = VocDocument(
            ticket_id=ticket_id,
            raw_voc=raw_voc,
            summary=summary,
            problem_type_primary=problem_type_primary,
            problem_type_secondary=problem_type_secondary,
            affected_system=affected_system,
            resolution=resolution,
            confidence=confidence,
        )
        self.add_voc_case(document)

    def get_document_count(self) -> int:
        """Get total number of documents in vector store"""
        return get_vector_store().get_document_count()


def load_seed_data() -> int:
    """Load seed VOC data into vector store"""
    if not SEED_DATA_PATH.exists():
        logger.warning(f"Seed data file not found: {SEED_DATA_PATH}")
        return 0

    with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
        seed_data = json.load(f)

    documents = []
    for item in seed_data:
        doc = VocDocument(
            ticket_id=item["ticket_id"],
            raw_voc=item["raw_voc"],
            summary=item.get("summary"),
            problem_type_primary=item.get("problem_type_primary"),
            problem_type_secondary=item.get("problem_type_secondary"),
            affected_system=item.get("affected_system"),
            resolution=item.get("resolution"),
            confidence=item.get("confidence"),
        )
        documents.append(doc)

    if documents:
        retriever = get_retriever()
        retriever.add_resolved_cases(documents)
        logger.info(f"Loaded {len(documents)} seed documents")

    return len(documents)


_rag_service_instance: Optional[RagService] = None


def get_rag_service() -> RagService:
    """Get singleton RAG service instance"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RagService()
    return _rag_service_instance
