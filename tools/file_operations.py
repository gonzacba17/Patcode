"""
File Operations Tool - FASE 1: Core del Sistema PatCode

Herramienta para manipular archivos de forma segura con validaciones y manejo de errores robusto.
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class FileOperationsTool:
    """
    Herramienta para operaciones seguras de archivos.
    
    Proporciona funciones para leer, escribir, editar y listar archivos
    dentro de un workspace seguro.
    """
    
    def __init__(self, workspace_root: str):
        """
        Inicializa el sistema de operaciones de archivos.
        
        Args:
            workspace_root: Directorio raíz del proyecto (seguridad)
        """
        self.workspace_root = Path(workspace_root).resolve()
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {workspace_root}")
    
    def _validate_path(self, path: str) -> Path:
        """
        Valida que el path esté dentro del workspace (seguridad).
        
        Args:
            path: Ruta a validar
            
        Returns:
            Path objeto validado
            
        Raises:
            ValueError: Si el path está fuera del workspace
        """
        full_path = (self.workspace_root / path).resolve()
        
        if not str(full_path).startswith(str(self.workspace_root)):
            raise ValueError(f"Path {path} is outside workspace")
        
        return full_path
    
    def read_file(self, path: str) -> Dict:
        """
        Lee un archivo y retorna su contenido.
        
        Args:
            path: Ruta relativa del archivo
            
        Returns:
            {
                "success": bool,
                "content": str,
                "error": Optional[str]
            }
        """
        try:
            full_path = self._validate_path(path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "content": "",
                    "error": f"File not found: {path}"
                }
            
            if not full_path.is_file():
                return {
                    "success": False,
                    "content": "",
                    "error": f"Path is not a file: {path}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "error": None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "content": "",
                "error": str(e)
            }
        except UnicodeDecodeError:
            return {
                "success": False,
                "content": "",
                "error": f"Cannot decode file (binary?): {path}"
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": f"Error reading file: {str(e)}"
            }
    
    def write_file(self, path: str, content: str) -> Dict:
        """
        Crea o sobrescribe un archivo.
        Crea directorios si no existen.
        
        Args:
            path: Ruta relativa del archivo
            content: Contenido a escribir
            
        Returns:
            {
                "success": bool,
                "message": str,
                "error": Optional[str]
            }
        """
        try:
            full_path = self._validate_path(path)
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"File written successfully: {path}",
                "error": None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": "",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": "",
                "error": f"Error writing file: {str(e)}"
            }
    
    def edit_file(self, path: str, line_start: int, line_end: int, 
                  new_content: str) -> Dict:
        """
        Edita líneas específicas de un archivo (1-indexed).
        
        Args:
            path: Ruta relativa del archivo
            line_start: Línea inicial (1-indexed, inclusive)
            line_end: Línea final (1-indexed, inclusive)
            new_content: Nuevo contenido para reemplazar
            
        Returns:
            {
                "success": bool,
                "message": str,
                "error": Optional[str]
            }
            
        Example:
            edit_file("main.py", 10, 12, "    print('new code')\\n")
            # Reemplaza líneas 10-12 con el nuevo contenido
        """
        try:
            read_result = self.read_file(path)
            if not read_result["success"]:
                return {
                    "success": False,
                    "message": "",
                    "error": read_result["error"]
                }
            
            lines = read_result["content"].splitlines(keepends=True)
            total_lines = len(lines)
            
            if line_start < 1 or line_end < 1:
                return {
                    "success": False,
                    "message": "",
                    "error": "Line numbers must be >= 1"
                }
            
            if line_start > total_lines or line_end > total_lines:
                return {
                    "success": False,
                    "message": "",
                    "error": f"Line numbers out of range (file has {total_lines} lines)"
                }
            
            if line_start > line_end:
                return {
                    "success": False,
                    "message": "",
                    "error": "line_start must be <= line_end"
                }
            
            new_lines = lines[:line_start-1] + [new_content] + lines[line_end:]
            new_file_content = ''.join(new_lines)
            
            write_result = self.write_file(path, new_file_content)
            
            if write_result["success"]:
                return {
                    "success": True,
                    "message": f"Edited lines {line_start}-{line_end} in {path}",
                    "error": None
                }
            else:
                return write_result
            
        except Exception as e:
            return {
                "success": False,
                "message": "",
                "error": f"Error editing file: {str(e)}"
            }
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict:
        """
        Lista archivos que coinciden con el patrón.
        
        Args:
            directory: Directorio relativo a listar
            pattern: Patrón de archivos (ej: "*.py", "test_*.py")
            
        Returns:
            {
                "success": bool,
                "files": List[str],  # Paths relativos
                "error": Optional[str]
            }
        """
        try:
            full_dir = self._validate_path(directory)
            
            if not full_dir.exists():
                return {
                    "success": False,
                    "files": [],
                    "error": f"Directory not found: {directory}"
                }
            
            if not full_dir.is_dir():
                return {
                    "success": False,
                    "files": [],
                    "error": f"Path is not a directory: {directory}"
                }
            
            files = []
            for item in full_dir.iterdir():
                if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                    relative_path = item.relative_to(self.workspace_root)
                    files.append(str(relative_path))
            
            return {
                "success": True,
                "files": sorted(files),
                "error": None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "files": [],
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "files": [],
                "error": f"Error listing files: {str(e)}"
            }
    
    def create_directory(self, path: str) -> Dict:
        """
        Crea un directorio (y padres si es necesario).
        
        Args:
            path: Ruta relativa del directorio
            
        Returns:
            {
                "success": bool,
                "message": str,
                "error": Optional[str]
            }
        """
        try:
            full_path = self._validate_path(path)
            
            full_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "message": f"Directory created: {path}",
                "error": None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": "",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": "",
                "error": f"Error creating directory: {str(e)}"
            }
    
    def get_file_info(self, path: str) -> Dict:
        """
        Retorna metadata del archivo.
        
        Args:
            path: Ruta relativa del archivo
            
        Returns:
            {
                "success": bool,
                "exists": bool,
                "size": int,
                "lines": int,
                "extension": str,
                "error": Optional[str]
            }
        """
        try:
            full_path = self._validate_path(path)
            
            if not full_path.exists():
                return {
                    "success": True,
                    "exists": False,
                    "size": 0,
                    "lines": 0,
                    "extension": "",
                    "error": None
                }
            
            stat = full_path.stat()
            
            lines = 0
            if full_path.is_file():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = sum(1 for _ in f)
                except:
                    lines = -1
            
            return {
                "success": True,
                "exists": True,
                "size": stat.st_size,
                "lines": lines,
                "extension": full_path.suffix,
                "error": None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "exists": False,
                "size": 0,
                "lines": 0,
                "extension": "",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "exists": False,
                "size": 0,
                "lines": 0,
                "extension": "",
                "error": f"Error getting file info: {str(e)}"
            }
