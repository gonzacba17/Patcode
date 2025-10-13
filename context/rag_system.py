# context/rag_system.py
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class RAGSystem:
    """Sistema de Retrieval Augmented Generation para contexto"""
    
    def __init__(self):
        # Modelo de embeddings local
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.embeddings = None
    
    def add_codebase(self, codebase_index: dict):
        """Agrega el codebase al sistema RAG"""
        for file_path, info in codebase_index.items():
            # Dividir en chunks semánticos
            chunks = self._chunk_code(info['content'], file_path)
            self.chunks.extend(chunks)
        
        # Crear embeddings
        texts = [c['text'] for c in self.chunks]
        self.embeddings = self.model.encode(texts)
    
    def retrieve_relevant_context(self, query: str, top_k: int = 5) -> List[str]:
        """Recupera el contexto más relevante para una query"""
        # Embedding de la query
        query_embedding = self.model.encode([query])[0]
        
        # Calcular similitud
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Top K resultados
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.chunks[i] for i in top_indices]