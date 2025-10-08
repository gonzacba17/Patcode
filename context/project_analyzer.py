"""
Analizador de estructura de proyectos.
Escanea y analiza la estructura completa del proyecto de código.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime


class ProjectAnalyzer:
    """Analiza la estructura y contenido de un proyecto de código."""
    
    def __init__(self, root_path: str = "."):
        """
        Inicializa el analizador de proyectos.
        
        Args:
            root_path: Ruta raíz del proyecto a analizar
        """
        self.root_path = os.path.abspath(root_path)
        self.ignore_patterns = self._load_ignore_patterns()
        self.analysis_cache = {}
        
    def analyze_project(self) -> Dict:
        """
        Analiza el proyecto completo y retorna información estructurada.
        
        Returns:
            Diccionario con análisis completo del proyecto
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "root_path": self.root_path,
            "project_name": os.path.basename(self.root_path),
            "structure": self._analyze_structure(),
            "languages": self._detect_languages(),
            "statistics": self._calculate_statistics(),
            "entry_points": self._find_entry_points(),
            "config_files": self._find_config_files(),
        }
        
        self.analysis_cache = analysis
        return analysis
    
    def get_file_tree(self, max_depth: int = 5, show_hidden: bool = False) -> str:
        """
        Genera una representación visual del árbol de archivos.
        
        Args:
            max_depth: Profundidad máxima del árbol
            show_hidden: Mostrar archivos/carpetas ocultos
            
        Returns:
            String con representación visual del árbol
        """
        lines = []
        project_name = os.path.basename(self.root_path)
        lines.append(f"{project_name}/")
        
        self._build_tree_lines(
            self.root_path, 
            prefix="", 
            lines=lines, 
            max_depth=max_depth,
            current_depth=0,
            show_hidden=show_hidden
        )
        
        return "\n".join(lines)
    
    def get_project_summary(self) -> str:
        """
        Genera un resumen en texto del proyecto.
        
        Returns:
            String con resumen formateado
        """
        if not self.analysis_cache:
            self.analyze_project()
        
        analysis = self.analysis_cache
        stats = analysis["statistics"]
        langs = analysis["languages"]
        
        summary = []
        summary.append(f"📁 Proyecto: {analysis['project_name']}")
        summary.append(f"📍 Ruta: {analysis['root_path']}")
        summary.append(f"\n📊 Estadísticas:")
        summary.append(f"  • Archivos totales: {stats['total_files']}")
        summary.append(f"  • Archivos de código: {stats['code_files']}")
        summary.append(f"  • Líneas de código: {stats['total_lines']:,}")
        summary.append(f"  • Directorios: {stats['total_directories']}")
        
        if langs:
            summary.append(f"\n💻 Lenguajes detectados:")
            for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary.append(f"  • {lang}: {count} archivo(s)")
        
        if analysis["entry_points"]:
            summary.append(f"\n🚀 Puntos de entrada:")
            for ep in analysis["entry_points"][:3]:
                summary.append(f"  • {ep}")
        
        return "\n".join(summary)
    
    def find_files(self, pattern: str, extension: Optional[str] = None) -> List[str]:
        """
        Busca archivos por patrón o extensión.
        
        Args:
            pattern: Patrón a buscar en el nombre del archivo
            extension: Extensión específica (ej: '.py', '.js')
            
        Returns:
            Lista de rutas relativas de archivos encontrados
        """
        results = []
        
        for root, dirs, files in os.walk(self.root_path):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                if self._should_ignore(filepath):
                    continue
                
                # Verificar patrón
                if pattern.lower() in file.lower():
                    # Verificar extensión si se especificó
                    if extension is None or file.endswith(extension):
                        rel_path = os.path.relpath(filepath, self.root_path)
                        results.append(rel_path)
        
        return results
    
    def get_files_by_extension(self, extension: str) -> List[str]:
        """
        Obtiene todos los archivos con una extensión específica.
        
        Args:
            extension: Extensión del archivo (ej: '.py', '.js')
            
        Returns:
            Lista de rutas relativas
        """
        return self.find_files("", extension=extension)
    
    def read_file(self, relative_path: str) -> Optional[str]:
        """
        Lee el contenido de un archivo del proyecto.
        
        Args:
            relative_path: Ruta relativa desde la raíz del proyecto
            
        Returns:
            Contenido del archivo o None si hay error
        """
        full_path = os.path.join(self.root_path, relative_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def get_file_info(self, relative_path: str) -> Optional[Dict]:
        """
        Obtiene información detallada de un archivo.
        
        Args:
            relative_path: Ruta relativa del archivo
            
        Returns:
            Diccionario con información del archivo
        """
        full_path = os.path.join(self.root_path, relative_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            stats = os.stat(full_path)
            content = self.read_file(relative_path)
            
            info = {
                "path": relative_path,
                "name": os.path.basename(relative_path),
                "extension": os.path.splitext(relative_path)[1],
                "size_bytes": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "is_binary": self._is_binary(full_path)
            }
            
            if content and not info["is_binary"]:
                info["lines"] = len(content.splitlines())
                info["language"] = self._detect_file_language(relative_path)
            
            return info
            
        except Exception as e:
            return {"path": relative_path, "error": str(e)}
    
    def _analyze_structure(self) -> Dict:
        """Analiza la estructura de directorios y archivos."""
        structure = {
            "directories": [],
            "files": [],
            "tree": {}
        }
        
        for root, dirs, files in os.walk(self.root_path):
            # Filtrar ignorados
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
            
            rel_root = os.path.relpath(root, self.root_path)
            
            for dir_name in dirs:
                dir_path = os.path.join(rel_root, dir_name) if rel_root != '.' else dir_name
                structure["directories"].append(dir_path)
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if not self._should_ignore(file_path):
                    rel_path = os.path.relpath(file_path, self.root_path)
                    structure["files"].append(rel_path)
        
        return structure
    
    def _detect_languages(self) -> Dict[str, int]:
        """Detecta lenguajes de programación en el proyecto."""
        languages = {}
        
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.cs': 'C#',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.sql': 'SQL',
            '.sh': 'Shell',
        }
        
        if not self.analysis_cache or "structure" not in self.analysis_cache:
            structure = self._analyze_structure()
        else:
            structure = self.analysis_cache["structure"]
        
        for filepath in structure["files"]:
            ext = os.path.splitext(filepath)[1].lower()
            if ext in extension_map:
                lang = extension_map[ext]
                languages[lang] = languages.get(lang, 0) + 1
        
        return languages
    
    def _calculate_statistics(self) -> Dict:
        """Calcula estadísticas del proyecto."""
        stats = {
            "total_files": 0,
            "code_files": 0,
            "total_lines": 0,
            "total_directories": 0,
            "total_size_bytes": 0
        }
        
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', 
            '.c', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs'
        }
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
            stats["total_directories"] += len(dirs)
            
            for file in files:
                filepath = os.path.join(root, file)
                
                if self._should_ignore(filepath):
                    continue
                
                stats["total_files"] += 1
                
                try:
                    stats["total_size_bytes"] += os.path.getsize(filepath)
                    
                    ext = os.path.splitext(file)[1].lower()
                    if ext in code_extensions:
                        stats["code_files"] += 1
                        
                        # Contar líneas
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                lines = len(f.readlines())
                                stats["total_lines"] += lines
                        except Exception:
                            pass
                except Exception:
                    pass
        
        return stats
    
    def _find_entry_points(self) -> List[str]:
        """Encuentra posibles puntos de entrada del proyecto."""
        entry_points = []
        
        common_entries = [
            'main.py', 'app.py', 'index.js', 'index.ts', 
            'server.py', 'run.py', '__main__.py'
        ]
        
        for entry in common_entries:
            files = self.find_files(entry)
            entry_points.extend(files)
        
        return entry_points
    
    def _find_config_files(self) -> List[str]:
        """Encuentra archivos de configuración."""
        config_patterns = [
            'config', 'settings', 'setup', 'package.json',
            'requirements.txt', 'Cargo.toml', 'go.mod',
            'pom.xml', 'build.gradle', '.env'
        ]
        
        config_files = []
        for pattern in config_patterns:
            files = self.find_files(pattern)
            config_files.extend(files)
        
        return config_files
    
    def _build_tree_lines(self, path: str, prefix: str, lines: List[str],
                         max_depth: int, current_depth: int, show_hidden: bool):
        """Construye líneas del árbol de archivos recursivamente."""
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(os.listdir(path))
            
            # Filtrar ignorados y ocultos
            filtered_items = []
            for item in items:
                item_path = os.path.join(path, item)
                
                if self._should_ignore(item_path):
                    continue
                
                if not show_hidden and item.startswith('.'):
                    continue
                
                filtered_items.append(item)
            
            for i, item in enumerate(filtered_items):
                item_path = os.path.join(path, item)
                is_last = i == len(filtered_items) - 1
                
                # Prefijos del árbol
                current = "└── " if is_last else "├── "
                extension = "    " if is_last else "│   "
                
                # Añadir indicador de directorio
                display_name = f"{item}/" if os.path.isdir(item_path) else item
                lines.append(prefix + current + display_name)
                
                # Recursión para directorios
                if os.path.isdir(item_path):
                    self._build_tree_lines(
                        item_path,
                        prefix + extension,
                        lines,
                        max_depth,
                        current_depth + 1,
                        show_hidden
                    )
        
        except PermissionError:
            pass
    
    def _load_ignore_patterns(self) -> Set[str]:
        """Carga patrones de archivos a ignorar."""
        patterns = {
            # Directorios comunes
            '__pycache__', '.git', '.svn', '.hg', 'node_modules',
            '.venv', 'venv', 'env', 'ENV', 'dist', 'build',
            '.pytest_cache', '.mypy_cache', '.tox', 'htmlcov',
            '.idea', '.vscode', '.DS_Store', 'coverage',
            '.eggs', '*.egg-info', '.cache', '.coverage',
            
            # Archivos compilados
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll',
            '*.class', '*.o', '*.obj'
        }
        
        # Leer .gitignore si existe
        gitignore_path = os.path.join(self.root_path, '.gitignore')
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.add(line.rstrip('/'))
            except Exception:
                pass
        
        return patterns
    
    def _should_ignore(self, path: str) -> bool:
        """Determina si un path debe ser ignorado."""
        basename = os.path.basename(path)
        
        # Verificar nombre exacto
        if basename in self.ignore_patterns:
            return True
        
        # Verificar patrones con wildcard
        for pattern in self.ignore_patterns:
            if '*' in pattern:
                pattern_ext = pattern.replace('*', '')
                if basename.endswith(pattern_ext):
                    return True
            elif pattern.startswith('.') and basename.endswith(pattern):
                return True
        
        # Verificar componentes del path
        parts = Path(path).parts
        for part in parts:
            if part in self.ignore_patterns:
                return True
        
        return False
    
    def _is_binary(self, filepath: str) -> bool:
        """Determina si un archivo es binario."""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except Exception:
            return True
    
    def _detect_file_language(self, filepath: str) -> str:
        """Detecta el lenguaje de un archivo por extensión."""
        ext = os.path.splitext(filepath)[1].lower()
        
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.md': 'Markdown',
        }
        
        return lang_map.get(ext, 'Unknown')