"""
RAG Retriever for VOC similarity search
"""

import logging
from typing import List, Optional

from app.rag.vector_store import get_vector_store, VocVectorStore
from app.rag.schemas import VocDocument, SearchResult, SimilarCasesContext
from app.config import settings

logger = logging.getLogger(__name__)


class VocRetriever:
    """Retriever for finding similar VOC cases"""

    def __init__(self, vector_store: Optional[VocVectorStore] = None):
        self._vector_store = vector_store or get_vector_store()

    def retrieve_similar_cases(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
        filter_problem_type: Optional[str] = None,
    ) -> List[SearchResult]:
        """Retrieve similar VOC cases"""
        return self._vector_store.search(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
            filter_problem_type=filter_problem_type,
        )

    def get_context_for_agent(
        self,
        voc_text: str,
        top_k: Optional[int] = None,
    ) -> SimilarCasesContext:
        """Get similar cases context for agent prompt injection"""
        results = self.retrieve_similar_cases(
            query=voc_text,
            top_k=top_k or settings.similarity_top_k,
        )
        return SimilarCasesContext(similar_cases=results)

    def add_resolved_case(self, document: VocDocument) -> None:
        """Add a resolved VOC case to the knowledge base"""
        self._vector_store.add_document(document)
        logger.info(f"Added resolved case to knowledge base: {document.ticket_id}")

    def add_resolved_cases(self, documents: List[VocDocument]) -> None:
        """Add multiple resolved VOC cases to the knowledge base"""
        self._vector_store.add_documents(documents)
        logger.info(f"Added {len(documents)} resolved cases to knowledge base")


_retriever_instance: Optional[VocRetriever] = None


def get_retriever() -> VocRetriever:
    """Get singleton retriever instance"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = VocRetriever()
    return _retriever_instance
