"""
Búsqueda semántica en código.
Proporciona búsqueda avanzada y contextual en el código del proyecto.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from pathlib import Path


class SemanticSearch:
    """Búsqueda semántica y contextual en código."""
    
    def __init__(self, root_path: str = "."):
        """
        Inicializa el sistema de búsqueda semántica.
        
        Args:
            root_path: Ruta raíz del proyecto
        """
        self.root_path = os.path.abspath(root_path)
        self.file_cache = {}
        self.ignore_patterns = self._load_ignore_patterns()
    
    def search_text(self, query: str, file_extensions: Optional[List[str]] = None,
                   case_sensitive: bool = False, regex: bool = False,
                   max_results: int = 100) -> List[Dict]:
        """
        Busca texto en archivos del proyecto.
        
        Args:
            query: Texto o patrón a buscar
            file_extensions: Lista de extensiones a buscar (ej: ['.py', '.js'])
            case_sensitive: Si la búsqueda distingue mayúsculas
            regex: Si el query es una expresión regular
            max_results: Número máximo de resultados
            
        Returns:
            Lista de coincidencias con contexto
        """
        results = []
        
        # Compilar patrón de búsqueda
        if regex:
            try:
                pattern = re.compile(query, 0 if case_sensitive else re.IGNORECASE)
            except re.error:
                return []
        else:
            if case_sensitive:
                pattern = re.compile(re.escape(query))
            else:
                pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        # Buscar en archivos
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # Filtrar por extensión
                if file_extensions and ext not in file_extensions:
                    continue
                
                if self._should_ignore(filepath):
                    continue
                
                # Buscar en archivo
                matches = self._search_in_file(filepath, pattern)
                results.extend(matches)
                
                if len(results) >= max_results:
                    return results[:max_results]
        
        return results
    
    def search_function(self, function_name: str, file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca definiciones de funciones por nombre.
        
        Args:
            function_name: Nombre de la función a buscar
            file_extensions: Extensiones de archivo donde buscar
            
        Returns:
            Lista de definiciones encontradas
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go']
        
        results = []
        
        for ext in file_extensions:
            pattern = self._get_function_pattern(ext)
            if not pattern:
                continue
            
            # Buscar archivos con esta extensión
            files = self._get_files_by_extension(ext)
            
            for filepath in files:
                content = self._read_file(filepath)
                if not content:
                    continue
                
                # Buscar definiciones
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    if match.group(1) == function_name:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        results.append({
                            'file': os.path.relpath(filepath, self.root_path),
                            'line': line_num,
                            'function_name': function_name,
                            'definition': match.group(0).strip(),
                            'language': self._detect_language(ext)
                        })
        
        return results
    
    def search_class(self, class_name: str, file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca definiciones de clases por nombre.
        
        Args:
            class_name: Nombre de la clase a buscar
            file_extensions: Extensiones de archivo donde buscar
            
        Returns:
            Lista de definiciones encontradas
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c']
        
        results = []
        
        for ext in file_extensions:
            pattern = self._get_class_pattern(ext)
            if not pattern:
                continue
            
            files = self._get_files_by_extension(ext)
            
            for filepath in files:
                content = self._read_file(filepath)
                if not content:
                    continue
                
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    # El grupo 1 o 2 contiene el nombre de la clase
                    matched_name = match.group(1) if match.lastindex >= 1 else match.group(0)
                    matched_name = re.search(r'class\s+(\w+)', matched_name)
                    
                    if matched_name and matched_name.group(1) == class_name:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        results.append({
                            'file': os.path.relpath(filepath, self.root_path),
                            'line': line_num,
                            'class_name': class_name,
                            'definition': match.group(0).strip(),
                            'language': self._detect_language(ext)
                        })
        
        return results
    
    def search_variable(self, var_name: str, scope: str = 'global',
                       file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca definiciones y asignaciones de variables.
        
        Args:
            var_name: Nombre de la variable
            scope: 'global', 'local', o 'all'
            file_extensions: Extensiones donde buscar
            
        Returns:
            Lista de asignaciones encontradas
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts']
        
        results = []
        
        for ext in file_extensions:
            pattern = self._get_variable_pattern(ext, var_name, scope)
            if not pattern:
                continue
            
            files = self._get_files_by_extension(ext)
            
            for filepath in files:
                content = self._read_file(filepath)
                if not content:
                    continue
                
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    results.append({
                        'file': os.path.relpath(filepath, self.root_path),
                        'line': line_num,
                        'variable_name': var_name,
                        'assignment': match.group(0).strip(),
                        'language': self._detect_language(ext)
                    })
        
        return results
    
    def search_imports(self, module_name: str, file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca imports de un módulo específico.
        
        Args:
            module_name: Nombre del módulo a buscar
            file_extensions: Extensiones donde buscar
            
        Returns:
            Lista de archivos que importan el módulo
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java']
        
        results = []
        
        for ext in file_extensions:
            pattern = self._get_import_pattern(ext, module_name)
            if not pattern:
                continue
            
            files = self._get_files_by_extension(ext)
            
            for filepath in files:
                content = self._read_file(filepath)
                if not content:
                    continue
                
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    results.append({
                        'file': os.path.relpath(filepath, self.root_path),
                        'line': line_num,
                        'module': module_name,
                        'import_statement': match.group(0).strip(),
                        'language': self._detect_language(ext)
                    })
        
        return results
    
    def find_similar_code(self, code_snippet: str, threshold: float = 0.7,
                         file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Encuentra código similar a un snippet dado.
        
        Args:
            code_snippet: Fragmento de código a buscar
            threshold: Umbral de similitud (0.0 a 1.0)
            file_extensions: Extensiones donde buscar
            
        Returns:
            Lista de fragmentos similares encontrados
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java']
        
        results = []
        snippet_tokens = self._tokenize_code(code_snippet)
        
        for ext in file_extensions:
            files = self._get_files_by_extension(ext)
            
            for filepath in files:
                content = self._read_file(filepath)
                if not content:
                    continue
                
                # Dividir en ventanas del tamaño del snippet
                lines = content.splitlines()
                snippet_lines = len(code_snippet.splitlines())
                
                for i in range(len(lines) - snippet_lines + 1):
                    window = '\n'.join(lines[i:i+snippet_lines])
                    window_tokens = self._tokenize_code(window)
                    
                    similarity = self._calculate_similarity(snippet_tokens, window_tokens)
                    
                    if similarity >= threshold:
                        results.append({
                            'file': os.path.relpath(filepath, self.root_path),
                            'start_line': i + 1,
                            'end_line': i + snippet_lines,
                            'code': window,
                            'similarity': similarity
                        })
        
        # Ordenar por similitud
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def search_comments(self, query: str, file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca texto en comentarios de código.
        
        Args:
            query: Texto a buscar en comentarios
            file_extensions: Extensiones donde buscar
            
        Returns:
            Lista de comentarios que contienen el texto
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c']
        
        results = []
        
        for ext in file_extensions:
            files = self._get_files_by_extension(ext)
            
            for filepath in files:
                content = self._read_file(filepath)
                if not content:
                    continue
                
                comments = self._extract_comments(content, ext)
                
                for comment in comments:
                    if query.lower() in comment['text'].lower():
                        results.append({
                            'file': os.path.relpath(filepath, self.root_path),
                            'line': comment['line'],
                            'comment': comment['text'],
                            'type': comment['type'],
                            'language': self._detect_language(ext)
                        })
        
        return results
    
    def search_todo_comments(self, file_extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca comentarios TODO, FIXME, HACK, etc.
        
        Args:
            file_extensions: Extensiones donde buscar
            
        Returns:
            Lista de comentarios de acción encontrados
        """
        markers = ['TODO', 'FIXME', 'HACK', 'NOTE', 'BUG', 'XXX']
        pattern = '|'.join(markers)
        
        return self.search_comments(f'({pattern})', file_extensions)
    
    def get_code_context(self, filepath: str, line_number: int, 
                        context_lines: int = 5) -> Dict:
        """
        Obtiene el contexto de código alrededor de una línea específica.
        
        Args:
            filepath: Ruta relativa del archivo
            line_number: Número de línea
            context_lines: Líneas de contexto antes y después
            
        Returns:
            Diccionario con el contexto
        """
        full_path = os.path.join(self.root_path, filepath)
        
        if not os.path.exists(full_path):
            return {}
        
        content = self._read_file(full_path)
        if not content:
            return {}
        
        lines = content.splitlines()
        
        if line_number < 1 or line_number > len(lines):
            return {}
        
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context = {
            'file': filepath,
            'target_line': line_number,
            'target_content': lines[line_number - 1],
            'context_start': start + 1,
            'context_end': end,
            'context_lines': lines[start:end],
            'full_context': '\n'.join(f"{i+start+1}: {line}" for i, line in enumerate(lines[start:end]))
        }
        
        return context
    
    def _search_in_file(self, filepath: str, pattern: re.Pattern) -> List[Dict]:
        """Busca un patrón en un archivo."""
        results = []
        
        content = self._read_file(filepath)
        if not content:
            return results
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            matches = pattern.finditer(line)
            for match in matches:
                context = self._get_line_context(lines, i - 1, 2)
                
                results.append({
                    'file': os.path.relpath(filepath, self.root_path),
                    'line': i,
                    'column': match.start() + 1,
                    'match': match.group(0),
                    'line_content': line,
                    'context': context
                })
        
        return results
    
    def _read_file(self, filepath: str) -> Optional[str]:
        """Lee el contenido de un archivo con caché."""
        if filepath in self.file_cache:
            return self.file_cache[filepath]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.file_cache[filepath] = content
                return content
        except Exception:
            return None
    
    def _get_line_context(self, lines: List[str], line_idx: int, context: int) -> List[str]:
        """Obtiene líneas de contexto alrededor de una línea."""
        start = max(0, line_idx - context)
        end = min(len(lines), line_idx + context + 1)
        return [line.rstrip() for line in lines[start:end]]
    
    def _get_files_by_extension(self, extension: str) -> List[str]:
        """Obtiene todos los archivos con una extensión específica."""
        files = []
        
        for root, dirs, filenames in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for filename in filenames:
                if filename.endswith(extension):
                    filepath = os.path.join(root, filename)
                    if not self._should_ignore(filepath):
                        files.append(filepath)
        
        return files
    
    def _get_function_pattern(self, extension: str) -> Optional[str]:
        """Obtiene el patrón regex para buscar funciones según el lenguaje."""
        patterns = {
            '.py': r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            '.js': r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(|^\s*const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>',
            '.ts': r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(|^\s*const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>',
            '.java': r'^\s*(public|private|protected)?\s+\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            '.cpp': r'^\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            '.c': r'^\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            '.go': r'^\s*func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        }
        return patterns.get(extension)
    
    def _get_class_pattern(self, extension: str) -> Optional[str]:
        """Obtiene el patrón regex para buscar clases según el lenguaje."""
        patterns = {
            '.py': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]',
            '.js': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[{]',
            '.ts': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[{]',
            '.java': r'^\s*(public|private)?\s+class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            '.cpp': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            '.c': r'^\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        }
        return patterns.get(extension)
    
    def _get_variable_pattern(self, extension: str, var_name: str, scope: str) -> Optional[str]:
        """Obtiene el patrón regex para buscar variables."""
        if extension == '.py':
            if scope == 'global':
                return rf'^{var_name}\s*='
            else:
                return rf'\b{var_name}\s*='
        elif extension in ['.js', '.ts']:
            if scope == 'global':
                return rf'^(const|let|var)\s+{var_name}\s*='
            else:
                return rf'(const|let|var)\s+{var_name}\s*='
        
        return None
    
    def _get_import_pattern(self, extension: str, module_name: str) -> Optional[str]:
        """Obtiene el patrón regex para buscar imports."""
        patterns = {
            '.py': rf'^\s*(import\s+{module_name}|from\s+{module_name}\s+import)',
            '.js': rf'import\s+.*\s+from\s+[\'\"]{module_name}[\'\"]|require\([\'\"]{ module_name}[\'\"]\)',
            '.ts': rf'import\s+.*\s+from\s+[\'\"]{module_name}[\'\"]',
            '.java': rf'import\s+{module_name}'
        }
        return patterns.get(extension)
    
    def _tokenize_code(self, code: str) -> List[str]:
        """Tokeniza código para comparación."""
        # Remover comentarios y strings
        code = re.sub(r'#.*', '', code, flags=re.MULTILINE)  # Python comments
        code = re.sub(r'//.*', '', code, flags=re.MULTILINE)  # JS/Java comments
        code = re.sub(r'["\'].*?["\']', '', code)  # Strings
        
        # Extraer tokens (palabras y símbolos)
        tokens = re.findall(r'\b\w+\b|[^\w\s]', code)
        return [t.lower() for t in tokens if t.strip()]
    
    def _calculate_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Calcula similitud entre dos listas de tokens."""
        if not tokens1 or not tokens2:
            return 0.0
        
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_comments(self, content: str, extension: str) -> List[Dict]:
        """Extrae comentarios del código."""
        comments = []
        lines = content.splitlines()
        
        if extension == '.py':
            # Comentarios de línea
            for i, line in enumerate(lines, 1):
                match = re.search(r'#\s*(.*)', line)
                if match:
                    comments.append({
                        'line': i,
                        'text': match.group(1),
                        'type': 'line'
                    })
            
            # Docstrings
            in_docstring = False
            docstring_start = 0
            for i, line in enumerate(lines, 1):
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_start = i
                    else:
                        in_docstring = False
                        comments.append({
                            'line': docstring_start,
                            'text': '\n'.join(lines[docstring_start-1:i]),
                            'type': 'docstring'
                        })
        
        elif extension in ['.js', '.ts', '.java', '.cpp', '.c']:
            # Comentarios de línea //
            for i, line in enumerate(lines, 1):
                match = re.search(r'//\s*(.*)', line)
                if match:
                    comments.append({
                        'line': i,
                        'text': match.group(1),
                        'type': 'line'
                    })
            
            # Comentarios de bloque /* */
            in_block = False
            block_start = 0
            for i, line in enumerate(lines, 1):
                if '/*' in line and not in_block:
                    in_block = True
                    block_start = i
                if '*/' in line and in_block:
                    in_block = False
                    comments.append({
                        'line': block_start,
                        'text': '\n'.join(lines[block_start-1:i]),
                        'type': 'block'
                    })
        
        return comments
    
    def _detect_language(self, extension: str) -> str:
        """Detecta el lenguaje por extensión."""
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust'
        }
        return lang_map.get(extension, 'Unknown')
    
    def _load_ignore_patterns(self) -> set:
        """Carga patrones de archivos a ignorar."""
        return {
            '__pycache__', '.git', 'node_modules', '.venv',
            'venv', 'dist', 'build', '.pytest_cache', '.idea',
            '.vscode', '.DS_Store'
        }
    
    def _should_ignore(self, path: str) -> bool:
        """Determina si un path debe ser ignorado."""
        basename = os.path.basename(path)
        return basename in self.ignore_patterns