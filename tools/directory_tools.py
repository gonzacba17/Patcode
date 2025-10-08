"""
tools/directory_tools.py
Herramientas para navegar y manipular directorios
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from .base_tool import BaseTool


class ListDirectoryTool(BaseTool):
    """Lista archivos y directorios en una ruta"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Lista el contenido de un directorio"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Ruta del directorio a listar (. para el actual)",
                    "default": "."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Listar recursivamente subdirectorios",
                    "default": False
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Incluir archivos ocultos",
                    "default": False
                }
            },
            "required": []
        }
    
    def execute(self, directory: str = ".", recursive: bool = False, 
                include_hidden: bool = False, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(directory)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Directorio no encontrado: {directory}"
                }
            
            if not full_path.is_dir():
                return {
                    "success": False,
                    "error": f"La ruta no es un directorio: {directory}"
                }
            
            items = self._list_items(full_path, recursive, include_hidden)
            
            return {
                "success": True,
                "result": {
                    "directory": str(full_path),
                    "total_items": len(items),
                    "items": items
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listando directorio: {str(e)}"
            }
    
    def _list_items(self, path: Path, recursive: bool, include_hidden: bool) -> List[Dict[str, Any]]:
        """Lista items del directorio"""
        items = []
        
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for item in path.glob(pattern):
                # Filtrar ocultos si es necesario
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                items.append({
                    "name": item.name,
                    "path": str(item.relative_to(path)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
        
        except Exception:
            pass
        
        return sorted(items, key=lambda x: (x["type"] != "directory", x["name"]))
    
    def _resolve_path(self, directory: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(directory)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class FindFilesTool(BaseTool):
    """Busca archivos por patrón o nombre"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Busca archivos por patrón (glob) en un directorio"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Patrón glob (ej: '*.py', '**/*.js')"
                },
                "directory": {
                    "type": "string",
                    "description": "Directorio donde buscar",
                    "default": "."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Máximo número de resultados",
                    "default": 100
                }
            },
            "required": ["pattern"]
        }
    
    def execute(self, pattern: str, directory: str = ".", 
                max_results: int = 100, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(directory)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Directorio no encontrado: {directory}"
                }
            
            # Buscar archivos
            matches = []
            for item in full_path.glob(pattern):
                if item.is_file():
                    matches.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.workspace_root)),
                        "size": item.stat().st_size
                    })
                    
                    if len(matches) >= max_results:
                        break
            
            return {
                "success": True,
                "result": {
                    "pattern": pattern,
                    "directory": str(full_path),
                    "total_found": len(matches),
                    "matches": matches
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error buscando archivos: {str(e)}"
            }
    
    def _resolve_path(self, directory: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(directory)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class GetTreeTool(BaseTool):
    """Genera un árbol de directorios visual"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Genera una representación en árbol de la estructura de directorios"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directorio raíz del árbol",
                    "default": "."
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Profundidad máxima del árbol",
                    "default": 3
                },
                "ignore_patterns": {
                    "type": "array",
                    "description": "Patrones a ignorar (ej: ['node_modules', '.git'])",
                    "default": [".git", "__pycache__", "node_modules", ".venv"]
                }
            },
            "required": []
        }
    
    def execute(self, directory: str = ".", max_depth: int = 3, 
                ignore_patterns: List[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            if ignore_patterns is None:
                ignore_patterns = [".git", "__pycache__", "node_modules", ".venv"]
            
            full_path = self._resolve_path(directory)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Directorio no encontrado: {directory}"
                }
            
            tree_lines = []
            self._build_tree(full_path, "", tree_lines, 0, max_depth, ignore_patterns)
            tree_str = "\n".join(tree_lines)
            
            return {
                "success": True,
                "result": {
                    "directory": str(full_path),
                    "tree": tree_str
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generando árbol: {str(e)}"
            }
    
    def _build_tree(self, path: Path, prefix: str, lines: List[str], 
                    depth: int, max_depth: int, ignore_patterns: List[str]):
        """Construye el árbol recursivamente"""
        if depth > max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for i, item in enumerate(items):
                # Ignorar patrones
                if any(pattern in item.name for pattern in ignore_patterns):
                    continue
                
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir():
                    extension = "    " if is_last else "│   "
                    self._build_tree(item, prefix + extension, lines, 
                                   depth + 1, max_depth, ignore_patterns)
        
        except PermissionError:
            pass
    
    def _resolve_path(self, directory: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(directory)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()