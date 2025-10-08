"""
Indexador de código.
Crea índices y mapas de símbolos, funciones, clases y definiciones en el código.
"""

import os
import re
import json
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class CodeIndexer:
    """Indexa código para búsqueda rápida de símbolos y definiciones."""
    
    def __init__(self, root_path: str = "."):
        """
        Inicializa el indexador de código.
        
        Args:
            root_path: Ruta raíz del proyecto
        """
        self.root_path = os.path.abspath(root_path)
        self.index = {
            "functions": {},      # nombre -> [ubicaciones]
            "classes": {},        # nombre -> [ubicaciones]
            "imports": {},        # módulo -> [archivos que lo importan]
            "variables": {},      # nombre -> [ubicaciones]
            "definitions": []     # lista de todas las definiciones
        }
        self._indexed = False
    
    def build_index(self, extensions: Optional[List[str]] = None) -> Dict:
        """
        Construye el índice completo del código.
        
        Args:
            extensions: Lista de extensiones a indexar (default: código común)
            
        Returns:
            Diccionario con el índice construido
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
        
        # Resetear índice
        self.index = {
            "functions": {},
            "classes": {},
            "imports": {},
            "variables": {},
            "definitions": []
        }
        
        # Recorrer archivos
        for root, dirs, files in os.walk(self.root_path):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in extensions and not self._should_ignore(filepath):
                    rel_path = os.path.relpath(filepath, self.root_path)
                    self._index_file(rel_path, ext)
        
        self._indexed = True
        return self.index
    
    def find_definition(self, symbol_name: str) -> List[Dict]:
        """
        Encuentra la definición de un símbolo (función, clase, variable).
        
        Args:
            symbol_name: Nombre del símbolo a buscar
            
        Returns:
            Lista de ubicaciones donde se define el símbolo
        """
        if not self._indexed:
            self.build_index()
        
        results = []
        
        # Buscar en funciones
        if symbol_name in self.index["functions"]:
            for location in self.index["functions"][symbol_name]:
                results.append({
                    "type": "function",
                    "name": symbol_name,
                    **location
                })
        
        # Buscar en clases
        if symbol_name in self.index["classes"]:
            for location in self.index["classes"][symbol_name]:
                results.append({
                    "type": "class",
                    "name": symbol_name,
                    **location
                })
        
        # Buscar en variables
        if symbol_name in self.index["variables"]:
            for location in self.index["variables"][symbol_name]:
                results.append({
                    "type": "variable",
                    "name": symbol_name,
                    **location
                })
        
        return results
    
    def find_references(self, symbol_name: str) -> List[Dict]:
        """
        Encuentra todas las referencias a un símbolo.
        
        Args:
            symbol_name: Nombre del símbolo
            
        Returns:
            Lista de ubicaciones donde se usa el símbolo
        """
        references = []
        
        # Buscar en todos los archivos indexados
        files_to_search = set()
        for definitions in self.index.values():
            if isinstance(definitions, dict):
                for locations in definitions.values():
                    for loc in locations:
                        files_to_search.add(loc["file"])
        
        # Buscar el símbolo en cada archivo
        for filepath in files_to_search:
            refs = self._find_symbol_in_file(filepath, symbol_name)
            references.extend(refs)
        
        return references
    
    def get_file_symbols(self, relative_path: str) -> Dict:
        """
        Obtiene todos los símbolos definidos en un archivo.
        
        Args:
            relative_path: Ruta relativa del archivo
            
        Returns:
            Diccionario con símbolos del archivo
        """
        full_path = os.path.join(self.root_path, relative_path)
        ext = os.path.splitext(relative_path)[1].lower()
        
        if not os.path.exists(full_path):
            return {}
        
        symbols = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if ext == '.py':
                symbols = self._extract_python_symbols(content, relative_path)
            elif ext in ['.js', '.ts']:
                symbols = self._extract_javascript_symbols(content, relative_path)
            elif ext == '.java':
                symbols = self._extract_java_symbols(content, relative_path)
        
        except Exception:
            pass
        
        return symbols
    
    def get_imports_for_file(self, relative_path: str) -> List[str]:
        """
        Obtiene todos los imports de un archivo.
        
        Args:
            relative_path: Ruta relativa del archivo
            
        Returns:
            Lista de módulos importados
        """
        symbols = self.get_file_symbols(relative_path)
        return symbols.get("imports", [])
    
    def get_files_importing(self, module_name: str) -> List[str]:
        """
        Encuentra archivos que importan un módulo específico.
        
        Args:
            module_name: Nombre del módulo
            
        Returns:
            Lista de archivos que importan el módulo
        """
        if not self._indexed:
            self.build_index()
        
        return self.index["imports"].get(module_name, [])
    
    def search_symbol(self, query: str, symbol_type: Optional[str] = None) -> List[Dict]:
        """
        Busca símbolos que coincidan con una query.
        
        Args:
            query: Texto a buscar (puede ser parcial)
            symbol_type: Tipo de símbolo ('function', 'class', 'variable', None=todos)
            
        Returns:
            Lista de símbolos encontrados
        """
        if not self._indexed:
            self.build_index()
        
        results = []
        query_lower = query.lower()
        
        # Determinar qué índices buscar
        search_in = []
        if symbol_type is None:
            search_in = ["functions", "classes", "variables"]
        elif symbol_type in ["functions", "classes", "variables"]:
            search_in = [symbol_type]
        
        # Buscar en los índices seleccionados
        for idx_type in search_in:
            for symbol_name, locations in self.index[idx_type].items():
                if query_lower in symbol_name.lower():
                    for location in locations:
                        results.append({
                            "type": idx_type[:-1],  # quitar la 's' final
                            "name": symbol_name,
                            **location
                        })
        
        return results
    
    def get_index_statistics(self) -> Dict:
        """
        Obtiene estadísticas del índice.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self._indexed:
            self.build_index()
        
        return {
            "total_functions": len(self.index["functions"]),
            "total_classes": len(self.index["classes"]),
            "total_variables": len(self.index["variables"]),
            "total_definitions": len(self.index["definitions"]),
            "indexed_modules": len(self.index["imports"])
        }
    
    def _index_file(self, relative_path: str, extension: str):
        """Indexa un archivo específico."""
        full_path = os.path.join(self.root_path, relative_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if extension == '.py':
                self._index_python_file(content, relative_path)
            elif extension in ['.js', '.ts']:
                self._index_javascript_file(content, relative_path)
            elif extension == '.java':
                self._index_java_file(content, relative_path)
        
        except Exception:
            pass
    
    def _index_python_file(self, content: str, filepath: str):
        """Indexa un archivo Python."""
        lines = content.splitlines()
        
        # Funciones
        func_pattern = r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        for i, line in enumerate(lines, 1):
            match = re.match(func_pattern, line)
            if match:
                func_name = match.group(1)
                location = {"file": filepath, "line": i, "code": line.strip()}
                
                if func_name not in self.index["functions"]:
                    self.index["functions"][func_name] = []
                self.index["functions"][func_name].append(location)
                self.index["definitions"].append(location)
        
        # Clases
        class_pattern = r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]'
        for i, line in enumerate(lines, 1):
            match = re.match(class_pattern, line)
            if match:
                class_name = match.group(1)
                location = {"file": filepath, "line": i, "code": line.strip()}
                
                if class_name not in self.index["classes"]:
                    self.index["classes"][class_name] = []
                self.index["classes"][class_name].append(location)
                self.index["definitions"].append(location)
        
        # Imports
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Extraer módulo
                if stripped.startswith('import '):
                    module = stripped.split()[1].split('.')[0]
                else:  # from X import Y
                    parts = stripped.split()
                    if len(parts) >= 2:
                        module = parts[1].split('.')[0]
                    else:
                        continue
                
                if module not in self.index["imports"]:
                    self.index["imports"][module] = []
                if filepath not in self.index["imports"][module]:
                    self.index["imports"][module].append(filepath)
    
    def _index_javascript_file(self, content: str, filepath: str):
        """Indexa un archivo JavaScript/TypeScript."""
        lines = content.splitlines()
        
        # Funciones (function name() y const name = () =>)
        patterns = [
            r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            r'^\s*const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>',
            r'^\s*export\s+function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(1)
                    location = {"file": filepath, "line": i, "code": line.strip()}
                    
                    if func_name not in self.index["functions"]:
                        self.index["functions"][func_name] = []
                    self.index["functions"][func_name].append(location)
                    self.index["definitions"].append(location)
        
        # Clases
        class_pattern = r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[{]'
        for i, line in enumerate(lines, 1):
            match = re.match(class_pattern, line)
            if match:
                class_name = match.group(1)
                location = {"file": filepath, "line": i, "code": line.strip()}
                
                if class_name not in self.index["classes"]:
                    self.index["classes"][class_name] = []
                self.index["classes"][class_name].append(location)
                self.index["definitions"].append(location)
        
        # Imports
        import_pattern = r'^\s*import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
        for i, line in enumerate(lines, 1):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1).split('/')[0]
                
                if module not in self.index["imports"]:
                    self.index["imports"][module] = []
                if filepath not in self.index["imports"][module]:
                    self.index["imports"][module].append(filepath)
    
    def _index_java_file(self, content: str, filepath: str):
        """Indexa un archivo Java."""
        lines = content.splitlines()
        
        # Métodos públicos/privados
        method_pattern = r'^\s*(public|private|protected)?\s+\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        for i, line in enumerate(lines, 1):
            match = re.match(method_pattern, line)
            if match:
                method_name = match.group(2)
                if method_name not in ['if', 'for', 'while', 'switch']:
                    location = {"file": filepath, "line": i, "code": line.strip()}
                    
                    if method_name not in self.index["functions"]:
                        self.index["functions"][method_name] = []
                    self.index["functions"][method_name].append(location)
                    self.index["definitions"].append(location)
        
        # Clases
        class_pattern = r'^\s*(public|private)?\s+class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for i, line in enumerate(lines, 1):
            match = re.match(class_pattern, line)
            if match:
                class_name = match.group(2)
                location = {"file": filepath, "line": i, "code": line.strip()}
                
                if class_name not in self.index["classes"]:
                    self.index["classes"][class_name] = []
                self.index["classes"][class_name].append(location)
                self.index["definitions"].append(location)
        
        # Imports
        import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
        for i, line in enumerate(lines, 1):
            match = re.match(import_pattern, line)
            if match:
                full_import = match.group(1)
                module = full_import.split('.')[0]
                
                if module not in self.index["imports"]:
                    self.index["imports"][module] = []
                if filepath not in self.index["imports"][module]:
                    self.index["imports"][module].append(filepath)
    
    def _extract_python_symbols(self, content: str, filepath: str) -> Dict:
        """Extrae símbolos de código Python."""
        symbols = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }
        
        lines = content.splitlines()
        
        # Funciones
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line):
                match = re.match(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                symbols["functions"].append({
                    "name": match.group(1),
                    "line": i,
                    "code": line.strip()
                })
        
        # Clases
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line):
                match = re.match(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                symbols["classes"].append({
                    "name": match.group(1),
                    "line": i,
                    "code": line.strip()
                })
        
        # Imports
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                symbols["imports"].append(stripped)
        
        return symbols
    
    def _extract_javascript_symbols(self, content: str, filepath: str) -> Dict:
        """Extrae símbolos de código JavaScript/TypeScript."""
        symbols = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }
        
        lines = content.splitlines()
        
        # Funciones
        patterns = [
            r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>'
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    symbols["functions"].append({
                        "name": match.group(1),
                        "line": i,
                        "code": line.strip()
                    })
        
        # Clases
        for i, line in enumerate(lines, 1):
            match = re.search(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                symbols["classes"].append({
                    "name": match.group(1),
                    "line": i,
                    "code": line.strip()
                })
        
        # Imports
        for line in lines:
            if re.match(r'^\s*import\s+', line.strip()):
                symbols["imports"].append(line.strip())
        
        return symbols
    
    def _extract_java_symbols(self, content: str, filepath: str) -> Dict:
        """Extrae símbolos de código Java."""
        symbols = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }
        
        lines = content.splitlines()
        
        # Métodos
        for i, line in enumerate(lines, 1):
            match = re.search(r'(public|private|protected)?\s+\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
            if match:
                method_name = match.group(2)
                if method_name not in ['if', 'for', 'while', 'switch']:
                    symbols["functions"].append({
                        "name": method_name,
                        "line": i,
                        "code": line.strip()
                    })
        
        # Clases
        for i, line in enumerate(lines, 1):
            match = re.search(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                symbols["classes"].append({
                    "name": match.group(1),
                    "line": i,
                    "code": line.strip()
                })
        
        # Imports
        for line in lines:
            if re.match(r'^\s*import\s+', line):
                symbols["imports"].append(line.strip())
        
        return symbols
    
    def _find_symbol_in_file(self, filepath: str, symbol_name: str) -> List[Dict]:
        """Busca todas las ocurrencias de un símbolo en un archivo."""
        full_path = os.path.join(self.root_path, filepath)
        references = []
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if symbol_name in line:
                    references.append({
                        "file": filepath,
                        "line": i,
                        "code": line.strip(),
                        "context": self._get_context_lines(lines, i-1, 2)
                    })
        
        except Exception:
            pass
        
        return references
    
    def _get_context_lines(self, lines: List[str], line_idx: int, context: int) -> List[str]:
        """Obtiene líneas de contexto alrededor de una línea."""
        start = max(0, line_idx - context)
        end = min(len(lines), line_idx + context + 1)
        return [line.rstrip() for line in lines[start:end]]
    
    def _should_ignore(self, path: str) -> bool:
        """Determina si un path debe ser ignorado."""
        ignore_patterns = {
            '__pycache__', '.git', 'node_modules', '.venv',
            'venv', 'dist', 'build', '.pytest_cache'
        }
        
        basename = os.path.basename(path)
        return basename in ignore_patterns or basename.startswith('.')  