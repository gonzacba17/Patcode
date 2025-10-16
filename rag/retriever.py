"""
Sistema de recuperación de contexto para RAG.
"""
from typing import List, Dict
import logging
from rag.embeddings import EmbeddingGenerator
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

class ContextRetriever:
    
    def __init__(self, vector_store: VectorStore, embedding_gen: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_gen = embedding_gen
        logger.info("ContextRetriever inicializado")
    
    def retrieve_context(self, query: str, top_k: int = 5) -> str:
        logger.info(f"Recuperando contexto para: {query[:50]}...")
        
        query_embedding = self.embedding_gen.generate_embedding(query)
        
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        if not results:
            return "No se encontró contexto relevante en el proyecto."
        
        context = self.build_context_prompt(query, results)
        
        logger.info(f"Contexto recuperado: {len(results)} chunks")
        return context
    
    def retrieve_related_code(self, filepath: str, top_k: int = 3) -> List[Dict]:
        from pathlib import Path
        try:
            content = Path(filepath).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error leyendo {filepath}: {str(e)}")
            return []
        
        file_embedding = self.embedding_gen.generate_embedding(content[:1000])
        
        results = self.vector_store.search(file_embedding, top_k=top_k * 2)
        
        related = [r for r in results if r['filepath'] != filepath]
        
        return related[:top_k]
    
    def build_context_prompt(self, query: str, results: List[Dict]) -> str:
        context_parts = [
            "# Contexto relevante del proyecto:\n"
        ]
        
        for i, result in enumerate(results, 1):
            similarity = result['similarity']
            filepath = result['filepath']
            lines = f"L{result['start_line']}-{result['end_line']}"
            chunk_type = result['chunk_type']
            content = result['content']
            
            context_parts.append(
                f"## [{i}] {filepath} ({lines}) - {chunk_type} (similitud: {similarity:.2f})\n"
                f"```\n{content}\n```\n"
            )
        
        return '\n'.join(context_parts)
