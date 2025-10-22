"""
Tests para el sistema RAG de PatCode.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from rag.embeddings import EmbeddingGenerator
from rag.vector_store import VectorStore
from rag.code_indexer import CodeIndexer
from rag.retriever import ContextRetriever


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test_vectors.db"


@pytest.fixture
def temp_cache_path(tmp_path):
    return tmp_path / "test_embeddings.db"


@pytest.fixture
def embedding_gen(temp_cache_path):
    return EmbeddingGenerator(cache_db=temp_cache_path)


@pytest.fixture
def vector_store(temp_db_path):
    return VectorStore(db_path=temp_db_path)


@pytest.fixture
def code_indexer(vector_store, embedding_gen):
    return CodeIndexer(vector_store, embedding_gen)


@pytest.fixture
def retriever(vector_store, embedding_gen):
    return ContextRetriever(vector_store, embedding_gen)


@pytest.mark.requires_ollama
def test_embedding_generation(embedding_gen):
    text = "def hello_world(): return 'Hello'"
    embedding = embedding_gen.generate_embedding(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)


def test_embedding_cache(embedding_gen):
    text = "def test(): pass"
    
    mock_embedding = [0.1] * 768
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'embedding': mock_embedding}
        
        emb1 = embedding_gen.generate_embedding(text)
        emb2 = embedding_gen.generate_embedding(text)
        
        assert emb1 == emb2
        assert mock_post.call_count == 1


def test_chunk_text(embedding_gen):
    text = "line1\n" * 100
    chunks = embedding_gen.chunk_text(text, chunk_size=50, overlap=10)
    
    assert len(chunks) > 1
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_vector_store_add_document(vector_store):
    embedding = [0.1] * 768
    metadata = {
        'filepath': 'test.py',
        'start_line': 1,
        'end_line': 10,
        'chunk_type': 'function',
        'language': 'python'
    }
    
    doc_id = vector_store.add_document(
        content="def test(): pass",
        embedding=embedding,
        metadata=metadata
    )
    
    assert isinstance(doc_id, str)
    assert len(doc_id) > 0


def test_vector_store_search(vector_store):
    embedding1 = [0.1] * 768
    embedding2 = [0.9] * 768
    
    vector_store.add_document(
        "def func1(): pass",
        embedding1,
        {'filepath': 'file1.py', 'chunk_type': 'function', 'language': 'python', 'start_line': 1, 'end_line': 2}
    )
    
    vector_store.add_document(
        "def func2(): pass",
        embedding2,
        {'filepath': 'file2.py', 'chunk_type': 'function', 'language': 'python', 'start_line': 1, 'end_line': 2}
    )
    
    results = vector_store.search(embedding1, top_k=2)
    
    assert len(results) == 2
    assert results[0]['similarity'] > results[1]['similarity']


def test_vector_store_stats(vector_store):
    embedding = [0.1] * 768
    
    vector_store.add_document(
        "content1",
        embedding,
        {'filepath': 'file1.py', 'chunk_type': 'function', 'language': 'python', 'start_line': 1, 'end_line': 2}
    )
    
    stats = vector_store.get_stats()
    
    assert stats['total_documents'] == 1
    assert stats['total_files'] == 1


def test_code_indexer_should_ignore(code_indexer):
    assert code_indexer.should_ignore(Path('.git/config'))
    assert code_indexer.should_ignore(Path('__pycache__/file.pyc'))
    assert code_indexer.should_ignore(Path('node_modules/package/index.js'))
    assert not code_indexer.should_ignore(Path('src/main.py'))


def test_retriever_build_context(retriever, vector_store):
    embedding = [0.1] * 768
    
    vector_store.add_document(
        "def example(): return True",
        embedding,
        {'filepath': 'test.py', 'chunk_type': 'function', 'language': 'python', 'start_line': 1, 'end_line': 2}
    )
    
    results = [
        {
            'content': 'def example(): return True',
            'filepath': 'test.py',
            'start_line': 1,
            'end_line': 2,
            'chunk_type': 'function',
            'similarity': 0.95
        }
    ]
    
    context = retriever.build_context_prompt("test query", results)
    
    assert "Contexto relevante" in context
    assert "test.py" in context
    assert "def example()" in context


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
