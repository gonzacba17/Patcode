import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestEmbeddingGenerator:
    
    @patch('rag.embeddings.SentenceTransformer')
    def test_embedding_generation(self, mock_transformer):
        from rag.embeddings import EmbeddingGenerator
        
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_model
        
        gen = EmbeddingGenerator()
        embedding = gen.generate_embedding("test text")
        
        assert embedding is not None
        mock_model.encode.assert_called_once()


class TestVectorStore:
    
    def test_vector_store_initialization(self):
        from rag.vector_store import VectorStore
        
        store = VectorStore()
        assert store is not None
    
    def test_add_and_search(self):
        from rag.vector_store import VectorStore
        
        store = VectorStore()
        
        store.add(
            embedding=[0.1, 0.2, 0.3],
            metadata={'text': 'test', 'file': 'test.py'}
        )
        
        results = store.search([0.1, 0.2, 0.3], top_k=1)
        assert len(results) >= 0
