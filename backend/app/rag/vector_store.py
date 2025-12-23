"""
ChromaDB Vector Store for VOC documents
"""

import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.rag.schemas import VocDocument, SearchResult
from app.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

# Collection name for VOC documents
VOC_COLLECTION_NAME = "voc_documents"


class VocVectorStore:
    """Vector store for VOC documents using ChromaDB"""

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None
        self._embedding_service = get_embedding_service()
        self._init_client()

    def _init_client(self) -> None:
        """Initialize ChromaDB client"""
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        self._collection = self._client.get_or_create_collection(
            name=VOC_COLLECTION_NAME,
            metadata={"description": "VOC documents for similarity search"}
        )
        logger.info(f"Collection '{VOC_COLLECTION_NAME}' ready. Documents: {self._collection.count()}")

    def add_document(self, document: VocDocument) -> None:
        """Add a single VOC document to the vector store"""
        text = document.to_text()
        embedding = self._embedding_service.embed_text(text)
        metadata = document.to_metadata()

        self._collection.upsert(
            ids=[document.ticket_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        logger.info(f"Added document: {document.ticket_id}")

    def add_documents(self, documents: List[VocDocument]) -> None:
        """Add multiple VOC documents to the vector store"""
        if not documents:
            return

        ids = [doc.ticket_id for doc in documents]
        texts = [doc.to_text() for doc in documents]
        embeddings = self._embedding_service.embed_texts(texts)
        metadatas = [doc.to_metadata() for doc in documents]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"Added {len(documents)} documents")

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
        filter_problem_type: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search for similar VOC documents"""
        if not query or not query.strip():
            return []

        top_k = top_k or settings.similarity_top_k
        min_similarity = min_similarity or settings.similarity_threshold

        # Build where filter
        where_filter = None
        if filter_problem_type:
            where_filter = {"problem_type_primary": filter_problem_type}

        # Generate query embedding
        query_embedding = self._embedding_service.embed_text(query)

        # Search
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # Convert to SearchResult
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, ticket_id in enumerate(results["ids"][0]):
                # ChromaDB returns L2 distance, convert to similarity
                distance = results["distances"][0][i]
                similarity = 1 / (1 + distance)  # Convert distance to similarity

                if similarity < min_similarity:
                    continue

                metadata = results["metadatas"][0][i]
                document = VocDocument(
                    ticket_id=ticket_id,
                    raw_voc=results["documents"][0][i],
                    summary=None,
                    problem_type_primary=metadata.get("problem_type_primary") or None,
                    problem_type_secondary=metadata.get("problem_type_secondary") or None,
                    affected_system=metadata.get("affected_system") or None,
                    confidence=metadata.get("confidence"),
                )

                search_results.append(SearchResult(
                    document=document,
                    similarity_score=similarity
                ))

        logger.info(f"Search found {len(search_results)} results (query: {query[:50]}...)")
        return search_results

    def delete_document(self, ticket_id: str) -> None:
        """Delete a document from the vector store"""
        self._collection.delete(ids=[ticket_id])
        logger.info(f"Deleted document: {ticket_id}")

    def get_document_count(self) -> int:
        """Get total document count"""
        return self._collection.count()

    def reset(self) -> None:
        """Reset the collection (delete all documents)"""
        self._client.delete_collection(VOC_COLLECTION_NAME)
        self._collection = self._client.create_collection(
            name=VOC_COLLECTION_NAME,
            metadata={"description": "VOC documents for similarity search"}
        )
        logger.warning("Vector store reset - all documents deleted")


_vector_store_instance: Optional[VocVectorStore] = None


def get_vector_store() -> VocVectorStore:
    """Get singleton vector store instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VocVectorStore()
    return _vector_store_instance
