"""
Sistema RAG (Retrieval Augmented Generation) para PatCode.
Incluye embeddings, vector store, indexación y recuperación de contexto.
"""

from rag.embeddings import EmbeddingGenerator
from rag.vector_store import VectorStore
from rag.retriever import ContextRetriever

__all__ = [
    'EmbeddingGenerator',
    'VectorStore',
    'ContextRetriever'
]
