"""
Sistema de generación de embeddings para RAG.
Usa Ollama con modelo nomic-embed-text.
"""
import hashlib
import sqlite3
from typing import List, Optional, Dict
import logging
import requests
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    
    def __init__(
        self, 
        model: str = "nomic-embed-text",
        ollama_url: str = "http://localhost:11434",
        cache_db: Path = None
    ):
        self.model = model
        self.ollama_url = ollama_url
        
        if cache_db is None:
            cache_db = Path(".patcode_cache/embeddings.db")
        
        self.cache_db = cache_db
        
        self.cache_db.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_cache_db()
        
        logger.info(f"EmbeddingGenerator inicializado con modelo: {model}")
    
    def _init_cache_db(self):
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                text_hash TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def generate_embedding(self, text: str) -> List[float]:
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        cached = self.get_cached_embedding(text_hash)
        if cached:
            logger.debug(f"Embedding encontrado en caché: {text_hash[:8]}...")
            return cached
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            
            embedding = response.json()["embedding"]
            
            self._save_to_cache(text_hash, embedding)
            
            logger.debug(f"Embedding generado: {text_hash[:8]}... (dim: {len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generando embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for i, text in enumerate(texts):
            if i % 10 == 0:
                logger.info(f"Generando embeddings: {i}/{len(texts)}")
            embeddings.append(self.generate_embedding(text))
        return embeddings
    
    def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            cursor.execute("SELECT embedding FROM embeddings WHERE text_hash = ?", (text_hash,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Error leyendo caché: {str(e)}")
            return None
    
    def _save_to_cache(self, text_hash: str, embedding: List[float]):
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO embeddings (text_hash, embedding) VALUES (?, ?)",
                (text_hash, json.dumps(embedding))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error guardando en caché: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_tokens = len(line.split())
            
            if current_size + line_tokens > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                
                overlap_lines = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_lines + [line]
                current_size = sum(len(l.split()) for l in current_chunk)
            else:
                current_chunk.append(line)
                current_size += line_tokens
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        logger.debug(f"Texto dividido en {len(chunks)} chunks")
        return chunks
    
    def clear_cache(self):
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM embeddings")
        conn.commit()
        conn.close()
        logger.info("Caché de embeddings limpiado")
