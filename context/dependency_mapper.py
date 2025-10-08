"""
Mapeador de dependencias.
Analiza y mapea las dependencias entre archivos, módulos y paquetes.
"""

import os
import re
import json
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict


class DependencyMapper:
    """Mapea dependencias entre archivos y módulos del proyecto."""
    
    def __init__(self, root_path: str = "."):
        """
        Inicializa el mapeador de dependencias.
        
        Args:
            root_path: Ruta raíz del proyecto
        """
        self.root_path = os.path.abspath(root_path)
        self.dependency_graph = defaultdict(set)  # archivo -> {archivos que depende}
        self.reverse_graph = defaultdict(set)     # archivo -> {archivos que dependen de él}
        self.external_deps = set()                # Dependencias externas
        self._analyzed = False
    
    def analyze_dependencies(self) -> Dict:
        """
        Analiza todas las dependencias del proyecto.
        
        Returns:
            Diccionario con el grafo completo de dependencias
        """
        # Resetear grafos
        self.dependency_graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
        self.external_deps = set()
        
        # Analizar todos los archivos de código
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in ['.py', '.js', '.ts', '.java'] and not self._should_ignore(filepath):
                    rel_path = os.path.relpath(filepath, self.root_path)
                    self._analyze_file_dependencies(rel_path, ext)
        
        self._analyzed = True
        
        return {
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()},
            "reverse_graph": {k: list(v) for k, v in self.reverse_graph.items()},
            "external_dependencies": list(self.external_deps)
        }
    
    def get_dependencies(self, filepath: str) -> List[str]:
        """
        Obtiene las dependencias de un archivo específico.
        
        Args:
            filepath: Ruta relativa del archivo
            
        Returns:
            Lista de archivos de los que depende
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        return list(self.dependency_graph.get(filepath, set()))
    
    def get_dependents(self, filepath: str) -> List[str]:
        """
        Obtiene los archivos que dependen de un archivo específico.
        
        Args:
            filepath: Ruta relativa del archivo
            
        Returns:
            Lista de archivos que dependen de este
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        return list(self.reverse_graph.get(filepath, set()))
    
    def get_dependency_chain(self, filepath: str, max_depth: int = 5) -> List[List[str]]:
        """
        Obtiene todas las cadenas de dependencias de un archivo.
        
        Args:
            filepath: Ruta relativa del archivo
            max_depth: Profundidad máxima de búsqueda
            
        Returns:
            Lista de cadenas de dependencias
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        chains = []
        visited = set()
        
        def dfs(current: str, chain: List[str], depth: int):
            if depth > max_depth or current in visited:
                return
            
            visited.add(current)
            chain.append(current)
            
            deps = self.dependency_graph.get(current, set())
            if not deps:
                chains.append(chain.copy())
            else:
                for dep in deps:
                    dfs(dep, chain.copy(), depth + 1)
        
        dfs(filepath, [], 0)
        return chains
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Encuentra dependencias circulares en el proyecto.
        
        Returns:
            Lista de ciclos encontrados
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Encontramos un ciclo
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph.keys():
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def get_external_dependencies(self) -> Dict[str, List[str]]:
        """
        Obtiene las dependencias externas agrupadas por tipo.
        
        Returns:
            Diccionario con dependencias externas categorizadas
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        categorized = {
            "standard_library": [],
            "third_party": [],
            "local": []
        }
        
        # Categorizar dependencias Python
        stdlib_modules = {
            'os', 'sys', 're', 'json', 'datetime', 'collections',
            'itertools', 'functools', 'pathlib', 'typing', 'io',
            'math', 'random', 'time', 'subprocess', 'urllib'
        }
        
        for dep in self.external_deps:
            base_module = dep.split('.')[0]
            
            if base_module in stdlib_modules:
                categorized["standard_library"].append(dep)
            elif '.' in dep or '/' in dep:
                categorized["local"].append(dep)
            else:
                categorized["third_party"].append(dep)
        
        return categorized
    
    def get_dependency_stats(self) -> Dict:
        """
        Calcula estadísticas sobre las dependencias.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        total_files = len(self.dependency_graph)
        total_deps = sum(len(deps) for deps in self.dependency_graph.values())
        
        # Archivos más dependidos
        most_depended = sorted(
            self.reverse_graph.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        # Archivos con más dependencias
        most_dependencies = sorted(
            self.dependency_graph.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        return {
            "total_files": total_files,
            "total_dependencies": total_deps,
            "avg_dependencies_per_file": total_deps / total_files if total_files > 0 else 0,
            "most_depended_files": [(f, len(deps)) for f, deps in most_depended],
            "files_with_most_deps": [(f, len(deps)) for f, deps in most_dependencies],
            "external_dependencies_count": len(self.external_deps),
            "circular_dependencies": len(self.find_circular_dependencies())
        }
    
    def generate_dependency_tree(self, filepath: str, max_depth: int = 3) -> str:
        """
        Genera una representación visual del árbol de dependencias.
        
        Args:
            filepath: Ruta relativa del archivo raíz
            max_depth: Profundidad máxima del árbol
            
        Returns:
            String con representación visual
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        lines = []
        lines.append(f"📦 {filepath}")
        
        visited = set()
        self._build_tree_lines(filepath, "", lines, visited, max_depth, 0)
        
        return "\n".join(lines)
    
    def export_to_dot(self, output_file: str = "dependencies.dot"):
        """
        Exporta el grafo de dependencias en formato DOT (Graphviz).
        
        Args:
            output_file: Nombre del archivo de salida
        """
        if not self._analyzed:
            self.analyze_dependencies()
        
        dot_content = ["digraph Dependencies {"]
        dot_content.append("  rankdir=LR;")
        dot_content.append("  node [shape=box];")
        dot_content.append("")
        
        # Añadir nodos y aristas
        for source, targets in self.dependency_graph.items():
            source_label = source.replace('/', '_').replace('.', '_')
            
            for target in targets:
                target_label = target.replace('/', '_').replace('.', '_')
                dot_content.append(f'  "{source_label}" -> "{target_label}";')
        
        dot_content.append("}")
        
        output_path = os.path.join(self.root_path, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(dot_content))
        
        return output_path
    
    def _analyze_file_dependencies(self, filepath: str, extension: str):
        """Analiza las dependencias de un archivo específico."""
        full_path = os.path.join(self.root_path, filepath)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if extension == '.py':
                deps = self._extract_python_imports(content, filepath)
            elif extension in ['.js', '.ts']:
                deps = self._extract_javascript_imports(content, filepath)
            elif extension == '.java':
                deps = self._extract_java_imports(content, filepath)
            else:
                deps = []
            
            # Agregar al grafo
            for dep in deps:
                self.dependency_graph[filepath].add(dep['target'])
                
                if dep['is_local']:
                    self.reverse_graph[dep['target']].add(filepath)
                else:
                    self.external_deps.add(dep['target'])
        
        except Exception:
            pass
    
    def _extract_python_imports(self, content: str, filepath: str) -> List[Dict]:
        """Extrae imports de código Python."""
        dependencies = []
        lines = content.splitlines()
        
        for line in lines:
            stripped = line.strip()
            
            # import module
            if stripped.startswith('import '):
                parts = stripped.split()
                if len(parts) >= 2:
                    module = parts[1].split(',')[0].strip()
                    
                    # Determinar si es local o externo
                    local_path = self._resolve_python_import(module, filepath)
                    
                    dependencies.append({
                        'target': local_path if local_path else module,
                        'is_local': local_path is not None,
                        'import_statement': stripped
                    })
            
            # from module import ...
            elif stripped.startswith('from '):
                parts = stripped.split()
                if len(parts) >= 4 and parts[2] == 'import':
                    module = parts[1]
                    
                    local_path = self._resolve_python_import(module, filepath)
                    
                    dependencies.append({
                        'target': local_path if local_path else module,
                        'is_local': local_path is not None,
                        'import_statement': stripped
                    })
        
        return dependencies
    
    def _extract_javascript_imports(self, content: str, filepath: str) -> List[Dict]:
        """Extrae imports de código JavaScript/TypeScript."""
        dependencies = []
        lines = content.splitlines()
        
        import_pattern = r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
        require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
        
        for line in lines:
            # import ... from '...'
            match = re.search(import_pattern, line)
            if match:
                module = match.group(1)
                
                local_path = self._resolve_javascript_import(module, filepath)
                
                dependencies.append({
                    'target': local_path if local_path else module,
                    'is_local': local_path is not None,
                    'import_statement': line.strip()
                })
            
            # require('...')
            match = re.search(require_pattern, line)
            if match:
                module = match.group(1)
                
                local_path = self._resolve_javascript_import(module, filepath)
                
                dependencies.append({
                    'target': local_path if local_path else module,
                    'is_local': local_path is not None,
                    'import_statement': line.strip()
                })
        
        return dependencies
    
    def _extract_java_imports(self, content: str, filepath: str) -> List[Dict]:
        """Extrae imports de código Java."""
        dependencies = []
        lines = content.splitlines()
        
        import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
        
        for line in lines:
            match = re.search(import_pattern, line)
            if match:
                full_import = match.group(1)
                
                # En Java, imports son generalmente externos
                # excepto si coinciden con el paquete del proyecto
                is_local = self._is_local_java_import(full_import)
                
                dependencies.append({
                    'target': full_import,
                    'is_local': is_local,
                    'import_statement': line.strip()
                })
        
        return dependencies
    
    def _resolve_python_import(self, module: str, from_file: str) -> Optional[str]:
        """Resuelve un import Python a su archivo correspondiente."""
        # Import relativo
        if module.startswith('.'):
            current_dir = os.path.dirname(from_file)
            
            # Contar puntos para subir directorios
            level = 0
            while module.startswith('.'):
                level += 1
                module = module[1:]
            
            # Subir directorios
            parts = Path(current_dir).parts
            if level - 1 < len(parts):
                target_dir = os.path.join(*parts[:len(parts)-(level-1)]) if level > 1 else current_dir
            else:
                return None
            
            # Construir ruta
            module_path = module.replace('.', '/')
            possible_paths = [
                os.path.join(target_dir, module_path + '.py'),
                os.path.join(target_dir, module_path, '__init__.py')
            ]
            
            for path in possible_paths:
                if os.path.exists(os.path.join(self.root_path, path)):
                    return path
        
        # Import absoluto local
        else:
            module_path = module.replace('.', '/')
            possible_paths = [
                module_path + '.py',
                os.path.join(module_path, '__init__.py')
            ]
            
            for path in possible_paths:
                if os.path.exists(os.path.join(self.root_path, path)):
                    return path
        
        return None
    
    def _resolve_javascript_import(self, module: str, from_file: str) -> Optional[str]:
        """Resuelve un import JavaScript/TypeScript a su archivo."""
        # Import relativo
        if module.startswith('./') or module.startswith('../'):
            current_dir = os.path.dirname(from_file)
            target_path = os.path.normpath(os.path.join(current_dir, module))
            
            # Probar extensiones comunes
            extensions = ['', '.js', '.ts', '.jsx', '.tsx', '/index.js', '/index.ts']
            
            for ext in extensions:
                full_path = target_path + ext
                if os.path.exists(os.path.join(self.root_path, full_path)):
                    return full_path
        
        return None
    
    def _is_local_java_import(self, import_path: str) -> bool:
        """Determina si un import Java es local al proyecto."""
        # Buscar si existe un archivo .java correspondiente
        file_path = import_path.replace('.', '/') + '.java'
        return os.path.exists(os.path.join(self.root_path, file_path))
    
    def _build_tree_lines(self, filepath: str, prefix: str, lines: List[str],
                         visited: Set[str], max_depth: int, current_depth: int):
        """Construye líneas del árbol de dependencias recursivamente."""
        if current_depth >= max_depth or filepath in visited:
            return
        
        visited.add(filepath)
        
        deps = list(self.dependency_graph.get(filepath, set()))
        
        for i, dep in enumerate(deps):
            is_last = i == len(deps) - 1
            current_prefix = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "
            
            lines.append(prefix + current_prefix + dep)
            
            self._build_tree_lines(
                dep,
                prefix + extension,
                lines,
                visited,
                max_depth,
                current_depth + 1
            )
    
    def _should_ignore(self, path: str) -> bool:
        """Determina si un path debe ser ignorado."""
        ignore_patterns = {
            '__pycache__', '.git', 'node_modules', '.venv',
            'venv', 'dist', 'build', '.pytest_cache'
        }
        
        basename = os.path.basename(path)
        return basename in ignore_patterns