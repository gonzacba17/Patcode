"""
tools/search_tools.py
Herramientas para buscar en código
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_tool import BaseTool


class GrepTool(BaseTool):
    """Busca texto o patrones en archivos"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Busca texto o expresiones regulares en archivos"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Texto o regex a buscar"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Patrón de archivos donde buscar (ej: '*.py')",
                    "default": "**/*"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Búsqueda sensible a mayúsculas",
                    "default": True
                },
                "regex": {
                    "type": "boolean",
                    "description": "Usar expresión regular",
                    "default": False
                },
                "max_results": {
                    "type": "integer",
                    "description": "Máximo número de coincidencias",
                    "default": 50
                }
            },
            "required": ["pattern"]
        }
    
    def execute(self, pattern: str, file_pattern: str = "**/*", 
                case_sensitive: bool = True, regex: bool = False,
                max_results: int = 50, **kwargs) -> Dict[str, Any]:
        try:
            matches = []
            
            # Preparar patrón de búsqueda
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    compiled_pattern = re.compile(pattern, flags)
                except re.error as e:
                    return {
                        "success": False,
                        "error": f"Regex inválido: {str(e)}"
                    }
            else:
                search_pattern = pattern if case_sensitive else pattern.lower()
            
            # Buscar en archivos
            for file_path in self.workspace_root.glob(file_pattern):
                if not file_path.is_file():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            # Buscar coincidencia
                            found = False
                            if regex:
                                found = compiled_pattern.search(line)
                            else:
                                search_line = line if case_sensitive else line.lower()
                                found = search_pattern in search_line
                            
                            if found:
                                matches.append({
                                    "file": str(file_path.relative_to(self.workspace_root)),
                                    "line": line_num,
                                    "content": line.rstrip()
                                })
                                
                                if len(matches) >= max_results:
                                    break
                
                except (UnicodeDecodeError, PermissionError):
                    continue
                
                if len(matches) >= max_results:
                    break
            
            return {
                "success": True,
                "result": {
                    "pattern": pattern,
                    "total_matches": len(matches),
                    "matches": matches
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en búsqueda: {str(e)}"
            }


class FindDefinitionTool(BaseTool):
    """Encuentra definiciones de funciones/clases"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Busca definiciones de funciones, clases o métodos"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre de la función/clase a buscar"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Patrón de archivos (ej: '*.py', '*.js')",
                    "default": "**/*.py"
                },
                "definition_type": {
                    "type": "string",
                    "description": "Tipo de definición (function, class, any)",
                    "default": "any"
                }
            },
            "required": ["name"]
        }
    
    def execute(self, name: str, file_pattern: str = "**/*.py", 
                definition_type: str = "any", **kwargs) -> Dict[str, Any]:
        try:
            definitions = []
            
            # Patrones de búsqueda según tipo
            patterns = []
            if definition_type in ["function", "any"]:
                patterns.append(re.compile(rf"^\s*def\s+{re.escape(name)}\s*\("))
            if definition_type in ["class", "any"]:
                patterns.append(re.compile(rf"^\s*class\s+{re.escape(name)}\s*[\(:]"))
            
            # Buscar en archivos
            for file_path in self.workspace_root.glob(file_pattern):
                if not file_path.is_file():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in patterns:
                                if pattern.search(line):
                                    # Obtener contexto (líneas siguientes)
                                    context = []
                                    for i in range(line_num - 1, min(line_num + 5, len(lines))):
                                        context.append(lines[i].rstrip())
                                    
                                    definitions.append({
                                        "file": str(file_path.relative_to(self.workspace_root)),
                                        "line": line_num,
                                        "definition": line.strip(),
                                        "context": "\n".join(context)
                                    })
                
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            return {
                "success": True,
                "result": {
                    "name": name,
                    "total_found": len(definitions),
                    "definitions": definitions
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error buscando definición: {str(e)}"
            }


class FindReferencesTool(BaseTool):
    """Encuentra referencias/usos de una función o variable"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Busca dónde se usa una función, clase o variable"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Nombre del identificador a buscar"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Patrón de archivos",
                    "default": "**/*.py"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Máximo número de referencias",
                    "default": 30
                }
            },
            "required": ["identifier"]
        }
    
    def execute(self, identifier: str, file_pattern: str = "**/*.py", 
                max_results: int = 30, **kwargs) -> Dict[str, Any]:
        try:
            references = []
            
            # Patrón para buscar uso del identificador
            pattern = re.compile(rf"\b{re.escape(identifier)}\b")
            
            for file_path in self.workspace_root.glob(file_pattern):
                if not file_path.is_file():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                references.append({
                                    "file": str(file_path.relative_to(self.workspace_root)),
                                    "line": line_num,
                                    "content": line.strip()
                                })
                                
                                if len(references) >= max_results:
                                    break
                
                except (UnicodeDecodeError, PermissionError):
                    continue
                
                if len(references) >= max_results:
                    break
            
            return {
                "success": True,
                "result": {
                    "identifier": identifier,
                    "total_references": len(references),
                    "references": references
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error buscando referencias: {str(e)}"
            }