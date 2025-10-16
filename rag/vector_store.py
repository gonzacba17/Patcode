"""
Vector Store para almacenar y buscar embeddings.
Implementa búsqueda por similitud coseno.
"""
import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import logging
import uuid

logger = logging.getLogger(__name__)

class VectorStore:
    
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path(".patcode_cache/vectors.db")
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"VectorStore inicializado: {db_path}")
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                filepath TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                chunk_type TEXT,
                language TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filepath ON documents(filepath)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_type ON documents(chunk_type)")
        
        conn.commit()
        conn.close()
    
    def add_document(
        self, 
        content: str, 
        embedding: List[float], 
        metadata: Dict
    ) -> str:
        doc_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents 
            (id, content, embedding, filepath, start_line, end_line, chunk_type, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            content,
            json.dumps(embedding),
            metadata.get('filepath', ''),
            metadata.get('start_line', 0),
            metadata.get('end_line', 0),
            metadata.get('chunk_type', 'other'),
            metadata.get('language', 'unknown')
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Documento agregado: {doc_id} ({metadata.get('filepath')})")
        return doc_id
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, content, embedding, filepath, start_line, end_line, chunk_type FROM documents"
        params = []
        
        if filters:
            conditions = []
            if 'filepath' in filters:
                conditions.append("filepath LIKE ?")
                params.append(f"%{filters['filepath']}%")
            if 'chunk_type' in filters:
                conditions.append("chunk_type = ?")
                params.append(filters['chunk_type'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        query_vec = np.array(query_embedding)
        
        for row in rows:
            doc_id, content, embedding_json, filepath, start_line, end_line, chunk_type = row
            doc_embedding = np.array(json.loads(embedding_json))
            
            similarity = np.dot(query_vec, doc_embedding) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_embedding)
            )
            
            results.append({
                'id': doc_id,
                'content': content,
                'filepath': filepath,
                'start_line': start_line,
                'end_line': end_line,
                'chunk_type': chunk_type,
                'similarity': float(similarity)
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def delete_by_file(self, filepath: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE filepath = ?", (filepath,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"Eliminados {deleted} documentos de {filepath}")
        return deleted
    
    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT filepath) FROM documents")
        total_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT chunk_type, COUNT(*) FROM documents GROUP BY chunk_type")
        by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_documents': total_docs,
            'total_files': total_files,
            'by_chunk_type': by_type
        }
    
    def clear(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()
        logger.info("Vector store limpiado")
