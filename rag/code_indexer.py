"""
Indexador de código para RAG.
Escanea proyecto y extrae elementos de código usando AST.
"""
import ast
from pathlib import Path
from typing import List, Dict, Optional
import logging
from rag.embeddings import EmbeddingGenerator
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

class CodeIndexer:
    
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', 
        '.venv', 'venv', 'env', 'dist', 'build',
        '.pytest_cache', '.mypy_cache', 'coverage',
        '.patcode_cache', '.patcode_backups'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.md': 'markdown',
        '.txt': 'text'
    }
    
    def __init__(self, vector_store: VectorStore, embedding_gen: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_gen = embedding_gen
        logger.info("CodeIndexer inicializado")
    
    def index_project(
        self, 
        root_path: Path = Path('.'),
        extensions: Optional[List[str]] = None
    ) -> Dict:
        root_path = root_path.resolve()
        extensions = extensions or list(self.SUPPORTED_EXTENSIONS.keys())
        
        logger.info(f"Iniciando indexación de proyecto: {root_path}")
        
        stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'chunks_indexed': 0,
            'errors': []
        }
        
        for filepath in root_path.rglob('*'):
            if not filepath.is_file():
                continue
            
            if self.should_ignore(filepath):
                stats['files_skipped'] += 1
                continue
            
            if filepath.suffix not in extensions:
                stats['files_skipped'] += 1
                continue
            
            try:
                chunks_count = self.index_file(filepath)
                stats['files_processed'] += 1
                stats['chunks_indexed'] += chunks_count
                
                if stats['files_processed'] % 10 == 0:
                    logger.info(f"Progreso: {stats['files_processed']} archivos procesados")
                    
            except Exception as e:
                logger.error(f"Error indexando {filepath}: {str(e)}")
                stats['errors'].append(str(filepath))
        
        logger.info(f"Indexación completa: {stats}")
        return stats
    
    def index_file(self, filepath: Path) -> int:
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error leyendo {filepath}: {str(e)}")
            return 0
        
        language = self.SUPPORTED_EXTENSIONS.get(filepath.suffix, 'unknown')
        
        if language == 'python':
            elements = self.extract_code_elements(filepath)
        else:
            chunks = self.embedding_gen.chunk_text(content)
            elements = [
                {
                    'content': chunk,
                    'start_line': 1,
                    'end_line': len(chunk.split('\n')),
                    'chunk_type': 'module'
                }
                for chunk in chunks
            ]
        
        chunks_created = 0
        for element in elements:
            try:
                embedding = self.embedding_gen.generate_embedding(element['content'])
                
                metadata = {
                    'filepath': str(filepath.relative_to(Path.cwd())),
                    'start_line': element['start_line'],
                    'end_line': element['end_line'],
                    'chunk_type': element['chunk_type'],
                    'language': language
                }
                
                self.vector_store.add_document(
                    content=element['content'],
                    embedding=embedding,
                    metadata=metadata
                )
                chunks_created += 1
                
            except Exception as e:
                logger.error(f"Error procesando chunk de {filepath}: {str(e)}")
        
        return chunks_created
    
    def extract_code_elements(self, filepath: Path) -> List[Dict]:
        try:
            content = filepath.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except Exception as e:
            logger.error(f"Error parseando {filepath}: {str(e)}")
            return []
        
        elements = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                
                element_code = '\n'.join(lines[start_line-1:end_line])
                
                chunk_type = 'function' if isinstance(node, ast.FunctionDef) else 'class'
                
                elements.append({
                    'content': element_code,
                    'start_line': start_line,
                    'end_line': end_line,
                    'chunk_type': chunk_type,
                    'name': node.name
                })
        
        if not elements:
            elements.append({
                'content': content,
                'start_line': 1,
                'end_line': len(lines),
                'chunk_type': 'module'
            })
        
        return elements
    
    def should_ignore(self, path: Path) -> bool:
        if any(ignore_dir in path.parts for ignore_dir in self.IGNORE_DIRS):
            return True
        
        try:
            if path.stat().st_size > 1_000_000:
                return True
        except:
            pass
        
        if path.name.startswith('.'):
            return True
        
        return False
    
    def reindex_file(self, filepath: Path) -> int:
        self.vector_store.delete_by_file(str(filepath.relative_to(Path.cwd())))
        
        return self.index_file(filepath)
