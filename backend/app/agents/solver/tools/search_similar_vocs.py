"""
search_similar_vocs tool - Search for similar VOC cases using RAG
"""

import logging
from typing import List

from app.agents.solver.tools.schemas import (
    SearchSimilarVocsInput,
    SearchSimilarVocsOutput,
    SimilarVocCase
)
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


def search_similar_vocs(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.5
) -> SearchSimilarVocsOutput:
    """
    Search for similar VOC cases using RAG

    Args:
        query: VOC text to search for
        top_k: Number of similar cases to return
        min_similarity: Minimum similarity threshold

    Returns:
        SearchSimilarVocsOutput with similar cases
    """
    try:
        # Validate input
        input_data = SearchSimilarVocsInput(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # Search using RAG service
        rag_service = get_rag_service()
        results = rag_service.search_similar_vocs(
            query=input_data.query,
            top_k=input_data.top_k,
            min_similarity=input_data.min_similarity
        )

        # Convert to SimilarVocCase
        similar_cases = []
        for result in results:
            doc = result.document
            case = SimilarVocCase(
                ticket_id=doc.ticket_id,
                similarity_score=result.similarity_score,
                problem_type_primary=doc.problem_type_primary,
                problem_type_secondary=doc.problem_type_secondary,
                resolution=doc.resolution,
                summary=doc.summary or doc.raw_voc[:100]
            )
            similar_cases.append(case)

        logger.info(
            f"Found {len(similar_cases)} similar VOC cases for query: {query[:50]}..."
        )

        return SearchSimilarVocsOutput(
            similar_cases=similar_cases,
            total_found=len(similar_cases)
        )

    except Exception as e:
        logger.error(f"Error in search_similar_vocs tool: {e}")
        return SearchSimilarVocsOutput(similar_cases=[], total_found=0)
