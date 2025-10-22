import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestEmbeddingGenerator:
    
    def test_embedding_generation(self, tmp_path):
        from rag.embeddings import EmbeddingGenerator
        
        cache_path = tmp_path / "test_embeddings.db"
        gen = EmbeddingGenerator(cache_db=cache_path)
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'embedding': [0.1, 0.2, 0.3]}
            
            embedding = gen.generate_embedding("test text")
            
            assert embedding is not None
            assert len(embedding) == 3


class TestVectorStore:
    
    def test_vector_store_initialization(self, tmp_path):
        from rag.vector_store import VectorStore
        
        db_path = tmp_path / "test_vectors.db"
        store = VectorStore(db_path=db_path)
        assert store is not None
    
    def test_add_and_search(self, tmp_path):
        from rag.vector_store import VectorStore
        
        db_path = tmp_path / "test_vectors.db"
        store = VectorStore(db_path=db_path)
        
        embedding = [0.1] * 768
        metadata = {
            'filepath': 'test.py',
            'start_line': 1,
            'end_line': 10,
            'chunk_type': 'function',
            'language': 'python'
        }
        
        doc_id = store.add_document(
            content="test content",
            embedding=embedding,
            metadata=metadata
        )
        
        results = store.search(embedding, top_k=1)
        assert len(results) >= 1
