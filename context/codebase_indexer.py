# context/codebase_indexer.py
import os
from pathlib import Path
from typing import List, Dict

class CodebaseIndexer:
    """Indexa y analiza todo el codebase"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.file_index = {}
        self.symbol_index = {}
    
    def index_project(self):
        """Crea un índice completo del proyecto"""
        for file_path in self._get_all_files():
            # Leer archivo
            content = self._read_file(file_path)
            
            # Extraer información
            self.file_index[str(file_path)] = {
                'content': content,
                'size': len(content),
                'functions': self._extract_functions(content),
                'classes': self._extract_classes(content),
                'imports': self._extract_imports(content)
            }
    
    def search_symbol(self, symbol: str) -> List[Dict]:
        """Busca un símbolo (función, clase, variable) en todo el proyecto"""
        results = []
        for file_path, info in self.file_index.items():
            if symbol in info['functions'] or symbol in info['classes']:
                results.append({
                    'file': file_path,
                    'type': 'function' if symbol in info['functions'] else 'class'
                })
        return results
    
    def get_file_context(self, file_path: str, lines: int = 50) -> str:
        """Obtiene contexto relevante de un archivo"""
        if file_path not in self.file_index:
            return ""
        
        content = self.file_index[file_path]['content']
        # Retornar primeras N líneas o resumen
        return '\n'.join(content.split('\n')[:lines])