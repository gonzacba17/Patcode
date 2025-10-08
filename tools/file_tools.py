"""
tools/file_tools.py
Herramientas para leer y escribir archivos
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from .base_tool import BaseTool


class ReadFileTool(BaseTool):
    """Lee el contenido de un archivo"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Lee el contenido completo de un archivo de texto"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Ruta del archivo a leer (relativa o absoluta)"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            # Verificar que existe
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            # Verificar que es archivo
            if not full_path.is_file():
                return {
                    "success": False,
                    "error": f"La ruta no es un archivo: {file_path}"
                }
            
            # Leer contenido
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "result": {
                    "file_path": str(full_path),
                    "content": content,
                    "lines": len(content.splitlines()),
                    "size": len(content)
                }
            }
        
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"No se puede leer el archivo (no es texto UTF-8): {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error leyendo archivo: {str(e)}"
            }
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class WriteFileTool(BaseTool):
    """Escribe contenido en un archivo"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Escribe o sobrescribe un archivo con nuevo contenido"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Ruta del archivo a escribir"
                },
                "content": {
                    "type": "string",
                    "description": "Contenido a escribir en el archivo"
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Crear directorios si no existen",
                    "default": True
                }
            },
            "required": ["file_path", "content"]
        }
    
    def execute(self, file_path: str, content: str, create_dirs: bool = True, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            # Crear directorios si es necesario
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "result": {
                    "file_path": str(full_path),
                    "bytes_written": len(content.encode('utf-8')),
                    "lines_written": len(content.splitlines())
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error escribiendo archivo: {str(e)}"
            }
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class AppendFileTool(BaseTool):
    """Agrega contenido al final de un archivo"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Agrega contenido al final de un archivo existente"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Ruta del archivo"
                },
                "content": {
                    "type": "string",
                    "description": "Contenido a agregar"
                }
            },
            "required": ["file_path", "content"]
        }
    
    def execute(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            # Verificar que existe
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            # Agregar contenido
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "result": {
                    "file_path": str(full_path),
                    "bytes_appended": len(content.encode('utf-8'))
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error agregando a archivo: {str(e)}"
            }
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()