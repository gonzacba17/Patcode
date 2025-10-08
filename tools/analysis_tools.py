"""
tools/analysis_tools.py
Herramientas para análisis estático de código
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_tool import BaseTool


class SyntaxCheckTool(BaseTool):
    """Verifica sintaxis de código Python"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Verifica si hay errores de sintaxis en archivos Python"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Archivo Python a analizar"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            # Leer y parsear código
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            try:
                ast.parse(code)
                return {
                    "success": True,
                    "result": {
                        "file": str(full_path),
                        "valid": True,
                        "message": "Sintaxis correcta"
                    }
                }
            except SyntaxError as e:
                return {
                    "success": True,
                    "result": {
                        "file": str(full_path),
                        "valid": False,
                        "error": {
                            "message": str(e),
                            "line": e.lineno,
                            "offset": e.offset,
                            "text": e.text
                        }
                    }
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analizando archivo: {str(e)}"
            }
    
    def _resolve_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class CodeMetricsTool(BaseTool):
    """Calcula métricas de código"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Calcula métricas como líneas de código, funciones, clases, etc."
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Archivo Python a analizar"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Parsear AST
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {
                    "success": False,
                    "error": "Error de sintaxis en el archivo"
                }
            
            # Calcular métricas
            metrics = self._analyze_ast(tree, code)
            metrics["file"] = str(full_path)
            
            return {
                "success": True,
                "result": metrics
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error calculando métricas: {str(e)}"
            }
    
    def _analyze_ast(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Analiza el AST y extrae métricas"""
        lines = code.split('\n')
        
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": len(node.args.args)
                })
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": len(methods)
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node.lineno)
        
        # Contar líneas
        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        blank_lines = total_lines - code_lines - comment_lines
        
        return {
            "lines": {
                "total": total_lines,
                "code": code_lines,
                "comments": comment_lines,
                "blank": blank_lines
            },
            "functions": {
                "count": len(functions),
                "details": functions[:10]  # Primeras 10
            },
            "classes": {
                "count": len(classes),
                "details": classes
            },
            "imports": len(set(imports))
        }
    
    def _resolve_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class FindTODOTool(BaseTool):
    """Encuentra comentarios TODO, FIXME, etc."""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Busca comentarios TODO, FIXME, HACK, NOTE en el código"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_pattern": {
                    "type": "string",
                    "description": "Patrón de archivos a buscar",
                    "default": "**/*.py"
                },
                "tags": {
                    "type": "array",
                    "description": "Tags a buscar",
                    "default": ["TODO", "FIXME", "HACK", "NOTE", "XXX"]
                }
            },
            "required": []
        }
    
    def execute(self, file_pattern: str = "**/*.py", 
                tags: List[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            if tags is None:
                tags = ["TODO", "FIXME", "HACK", "NOTE", "XXX"]
            
            todos = []
            
            # Crear patrón regex para buscar tags
            tag_pattern = re.compile(
                r'#\s*(' + '|'.join(tags) + r')[:\s]+(.+)',
                re.IGNORECASE
            )
            
            # Buscar en archivos
            for file_path in self.workspace_root.glob(file_pattern):
                if not file_path.is_file():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            match = tag_pattern.search(line)
                            if match:
                                todos.append({
                                    "file": str(file_path.relative_to(self.workspace_root)),
                                    "line": line_num,
                                    "tag": match.group(1).upper(),
                                    "message": match.group(2).strip(),
                                    "content": line.strip()
                                })
                
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            # Agrupar por tag
            by_tag = {}
            for todo in todos:
                tag = todo["tag"]
                if tag not in by_tag:
                    by_tag[tag] = []
                by_tag[tag].append(todo)
            
            return {
                "success": True,
                "result": {
                    "total": len(todos),
                    "by_tag": {tag: len(items) for tag, items in by_tag.items()},
                    "items": todos
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error buscando TODOs: {str(e)}"
            }


class ComplexityAnalysisTool(BaseTool):
    """Analiza complejidad ciclomática del código"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Calcula la complejidad ciclomática de funciones Python"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Archivo Python a analizar"
                },
                "threshold": {
                    "type": "integer",
                    "description": "Umbral de complejidad para resaltar",
                    "default": 10
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, threshold: int = 10, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {
                    "success": False,
                    "error": "Error de sintaxis en el archivo"
                }
            
            # Analizar complejidad
            results = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    results.append({
                        "name": node.name,
                        "line": node.lineno,
                        "complexity": complexity,
                        "high_complexity": complexity > threshold
                    })
            
            # Ordenar por complejidad
            results.sort(key=lambda x: x["complexity"], reverse=True)
            
            return {
                "success": True,
                "result": {
                    "file": str(full_path),
                    "threshold": threshold,
                    "functions": results,
                    "high_complexity_count": sum(1 for r in results if r["high_complexity"])
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analizando complejidad: {str(e)}"
            }
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcula complejidad ciclomática simplificada"""
        complexity = 1  # Base
        
        for child in ast.walk(node):
            # Incrementar por cada punto de decisión
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # And/Or aumentan complejidad
                complexity += len(child.values) - 1
        
        return complexity
    
    def _resolve_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class ImportAnalysisTool(BaseTool):
    """Analiza imports y dependencias"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Analiza imports y detecta dependencias no utilizadas"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Archivo Python a analizar"
                }
            },
            "required": ["file_path"]
        }
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {
                    "success": False,
                    "error": "Error de sintaxis en el archivo"
                }
            
            # Extraer imports
            imports = []
            imported_names = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports.append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                        imported_names.add(name.split('.')[0])
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports.append({
                            "type": "from_import",
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                        imported_names.add(name)
            
            # Detectar usos (simplificado)
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
            
            # Identificar imports posiblemente no usados
            possibly_unused = []
            for imp in imports:
                check_name = imp.get('alias') or imp.get('name') or imp.get('module').split('.')[0]
                if check_name not in used_names:
                    possibly_unused.append(imp)
            
            return {
                "success": True,
                "result": {
                    "file": str(full_path),
                    "total_imports": len(imports),
                    "imports": imports,
                    "possibly_unused": possibly_unused,
                    "unused_count": len(possibly_unused)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analizando imports: {str(e)}"
            }
    
    def _resolve_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()