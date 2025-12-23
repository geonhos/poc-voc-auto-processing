"""
Tests for RAG module
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from app.rag.schemas import VocDocument, SearchResult, SimilarCasesContext
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VocVectorStore
from app.rag.retriever import VocRetriever
from app.services.rag_service import RagService, load_seed_data


class TestVocDocument:
    """Tests for VocDocument schema"""

    def test_to_text_basic(self):
        """Test basic text conversion"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="결제가 안 돼요",
        )
        assert doc.to_text() == "결제가 안 돼요"

    def test_to_text_with_summary(self):
        """Test text conversion with summary"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="결제가 안 돼요",
            summary="결제 오류 발생",
        )
        text = doc.to_text()
        assert "결제가 안 돼요" in text
        assert "결제 오류 발생" in text

    def test_to_metadata(self):
        """Test metadata conversion"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="결제가 안 돼요",
            problem_type_primary="integration_error",
            problem_type_secondary="code_error",
            affected_system="결제 시스템",
            confidence=0.85,
        )
        metadata = doc.to_metadata()
        assert metadata["ticket_id"] == "TEST-001"
        assert metadata["problem_type_primary"] == "integration_error"
        assert metadata["problem_type_secondary"] == "code_error"
        assert metadata["affected_system"] == "결제 시스템"
        assert metadata["confidence"] == 0.85


class TestSimilarCasesContext:
    """Tests for SimilarCasesContext"""

    def test_empty_context(self):
        """Test empty context prompt"""
        context = SimilarCasesContext(similar_cases=[])
        prompt = context.to_prompt_context()
        assert "유사한 과거 VOC 사례가 없습니다" in prompt

    def test_context_with_cases(self):
        """Test context with similar cases"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="결제가 안 돼요",
            summary="결제 오류",
            problem_type_primary="integration_error",
            affected_system="결제 시스템",
            resolution="PG사 연동 오류 수정",
        )
        result = SearchResult(document=doc, similarity_score=0.85)
        context = SimilarCasesContext(similar_cases=[result])

        prompt = context.to_prompt_context()
        assert "유사한 과거 VOC 사례" in prompt
        assert "85.00%" in prompt
        assert "integration_error" in prompt
        assert "결제 시스템" in prompt


class TestEmbeddingService:
    """Tests for EmbeddingService"""

    @pytest.fixture
    def embedding_service(self):
        """Get embedding service instance"""
        return EmbeddingService()

    def test_embed_text(self, embedding_service):
        """Test single text embedding"""
        text = "결제가 실패했습니다"
        embedding = embedding_service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_texts(self, embedding_service):
        """Test multiple text embeddings"""
        texts = ["결제 오류", "배송 지연", "로그인 실패"]
        embeddings = embedding_service.embed_texts(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert isinstance(emb, list)
            assert len(emb) > 0

    def test_embed_empty_text_raises(self, embedding_service):
        """Test that empty text raises error"""
        with pytest.raises(ValueError):
            embedding_service.embed_text("")

    def test_embedding_dimension(self, embedding_service):
        """Test embedding dimension property"""
        dim = embedding_service.embedding_dimension
        assert isinstance(dim, int)
        assert dim > 0


class TestVocVectorStore:
    """Tests for VocVectorStore"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for ChromaDB"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def vector_store(self, temp_dir):
        """Create vector store with temporary directory"""
        with patch("app.config.settings.chroma_persist_directory", temp_dir):
            # Reset singleton
            import app.rag.vector_store as vs_module
            vs_module._vector_store_instance = None

            store = VocVectorStore()
            yield store

            # Cleanup singleton
            vs_module._vector_store_instance = None

    def test_add_and_search_document(self, vector_store):
        """Test adding and searching a document"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="신용카드 결제가 실패했습니다",
            problem_type_primary="integration_error",
        )
        vector_store.add_document(doc)

        # Use same query text for high similarity
        results = vector_store.search("신용카드 결제가 실패했습니다", top_k=5, min_similarity=0.1)
        assert len(results) > 0
        assert results[0].document.ticket_id == "TEST-001"

    def test_add_multiple_documents(self, vector_store):
        """Test adding multiple documents"""
        docs = [
            VocDocument(ticket_id="TEST-001", raw_voc="결제 오류"),
            VocDocument(ticket_id="TEST-002", raw_voc="배송 지연"),
            VocDocument(ticket_id="TEST-003", raw_voc="로그인 실패"),
        ]
        vector_store.add_documents(docs)

        assert vector_store.get_document_count() == 3

    def test_search_with_filter(self, vector_store):
        """Test search with problem type filter"""
        docs = [
            VocDocument(
                ticket_id="TEST-001",
                raw_voc="결제 오류",
                problem_type_primary="integration_error"
            ),
            VocDocument(
                ticket_id="TEST-002",
                raw_voc="결제 버그",
                problem_type_primary="code_error"
            ),
        ]
        vector_store.add_documents(docs)

        results = vector_store.search(
            "결제 문제",
            filter_problem_type="integration_error",
            min_similarity=0.3
        )

        # Should only return integration_error
        for result in results:
            assert result.document.problem_type_primary == "integration_error"

    def test_delete_document(self, vector_store):
        """Test document deletion"""
        doc = VocDocument(ticket_id="TEST-001", raw_voc="테스트")
        vector_store.add_document(doc)
        assert vector_store.get_document_count() == 1

        vector_store.delete_document("TEST-001")
        assert vector_store.get_document_count() == 0


class TestVocRetriever:
    """Tests for VocRetriever"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def retriever(self, temp_dir):
        """Create retriever with temporary directory"""
        with patch("app.config.settings.chroma_persist_directory", temp_dir):
            import app.rag.vector_store as vs_module
            import app.rag.retriever as ret_module
            vs_module._vector_store_instance = None
            ret_module._retriever_instance = None

            retriever = VocRetriever()
            yield retriever

            vs_module._vector_store_instance = None
            ret_module._retriever_instance = None

    def test_retrieve_similar_cases(self, retriever):
        """Test retrieving similar cases"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="카드 결제 중 오류가 발생했습니다",
            problem_type_primary="integration_error",
            resolution="PG사 오류 수정",
        )
        retriever.add_resolved_case(doc)

        # Use same query text for high similarity
        results = retriever.retrieve_similar_cases(
            "카드 결제 중 오류가 발생했습니다",
            min_similarity=0.1
        )
        assert len(results) > 0

    def test_get_context_for_agent(self, retriever):
        """Test getting context for agent"""
        doc = VocDocument(
            ticket_id="TEST-001",
            raw_voc="결제 오류",
            summary="결제 시스템 오류",
            problem_type_primary="integration_error",
            resolution="PG사 연동 수정",
        )
        retriever.add_resolved_case(doc)

        context = retriever.get_context_for_agent("결제가 안됩니다")
        prompt = context.to_prompt_context()
        assert isinstance(prompt, str)


class TestRagService:
    """Tests for RagService"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def rag_service(self, temp_dir):
        """Create RAG service with temporary directory"""
        with patch("app.config.settings.chroma_persist_directory", temp_dir):
            import app.rag.vector_store as vs_module
            import app.rag.retriever as ret_module
            import app.services.rag_service as svc_module
            vs_module._vector_store_instance = None
            ret_module._retriever_instance = None
            svc_module._rag_service_instance = None

            service = RagService()
            yield service

            vs_module._vector_store_instance = None
            ret_module._retriever_instance = None
            svc_module._rag_service_instance = None

    def test_add_and_search(self, rag_service):
        """Test adding and searching through service"""
        rag_service.add_resolved_ticket(
            ticket_id="TEST-001",
            raw_voc="결제가 실패했습니다",
            summary="결제 오류",
            problem_type_primary="integration_error",
        )

        # Use same query text for high similarity
        results = rag_service.search_similar_vocs("결제가 실패했습니다", min_similarity=0.1)
        assert len(results) > 0

    def test_get_agent_context(self, rag_service):
        """Test getting agent context string"""
        rag_service.add_resolved_ticket(
            ticket_id="TEST-001",
            raw_voc="결제가 실패했습니다",
            problem_type_primary="integration_error",
            resolution="PG사 오류 수정",
        )

        context = rag_service.get_agent_context("결제 오류")
        assert isinstance(context, str)


class TestSeedDataLoading:
    """Tests for seed data loading"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_load_seed_data(self, temp_dir):
        """Test loading seed data"""
        with patch("app.config.settings.chroma_persist_directory", temp_dir):
            import app.rag.vector_store as vs_module
            import app.rag.retriever as ret_module
            vs_module._vector_store_instance = None
            ret_module._retriever_instance = None

            count = load_seed_data()
            assert count >= 10  # At least 10 seed documents

            vs_module._vector_store_instance = None
            ret_module._retriever_instance = None
