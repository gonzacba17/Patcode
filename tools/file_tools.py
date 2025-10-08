"""
tools/file_tools.py
Herramientas para leer, escribir y listar archivos
"""

import os
from pathlib import Path
from typing import Dict, Any


class ReadFileTool:
    """Lee el contenido de un archivo"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Lee el contenido completo de un archivo de texto"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Ruta del archivo a leer"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la lectura del archivo
        
        Args:
            file_path: Ruta del archivo a leer
            
        Returns:
            Dict con success, result o error
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            if not full_path.is_file():
                return {
                    "success": False,
                    "error": f"La ruta no es un archivo: {file_path}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "result": {
                    "file_path": str(full_path),
                    "content": content,
                    "lines": len(content.splitlines())
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


class WriteFileTool:
    """Escribe contenido en un archivo"""
    
    def __init__(self, workspace_root: str = "."):
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
                    "description": "Contenido a escribir"
                }
            },
            "required": ["file_path", "content"]
        }
    
    def execute(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la escritura del archivo
        
        Args:
            file_path: Ruta del archivo
            content: Contenido a escribir
            
        Returns:
            Dict con success, result o error
        """
        try:
            full_path = self._resolve_path(file_path)
            
            # Crear directorios si no existen
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "result": {
                    "file_path": str(full_path),
                    "bytes_written": len(content.encode('utf-8'))
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


class ListDirectoryTool:
    """Lista archivos y directorios"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Lista el contenido de un directorio"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Ruta del directorio a listar",
                    "default": "."
                }
            },
            "required": []
        }
    
    def execute(self, directory: str = ".", **kwargs) -> Dict[str, Any]:
        """
        Ejecuta el listado del directorio
        
        Args:
            directory: Ruta del directorio
            
        Returns:
            Dict con success, result o error
        """
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
            
            items = []
            for item in full_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            # Ordenar: directorios primero, luego alfabéticamente
            items.sort(key=lambda x: (x["type"] != "directory", x["name"]))
            
            return {
                "success": True,
                "result": {
                    "directory": str(full_path),
                    "items": items,
                    "total": len(items)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listando directorio: {str(e)}"
            }
    
    def _resolve_path(self, directory: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(directory)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()