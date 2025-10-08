"""
tools/git_tools.py
Herramientas para operaciones con Git
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_tool import BaseTool


class GitStatusTool(BaseTool):
    """Obtiene el estado del repositorio Git"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Muestra el estado actual del repositorio Git"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            # Verificar si es un repo git
            if not (self.workspace_root / ".git").exists():
                return {
                    "success": False,
                    "error": "No es un repositorio Git"
                }
            
            # Ejecutar git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr
                }
            
            # Parsear salida
            changes = self._parse_status(result.stdout)
            
            # Obtener branch actual
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True
            )
            current_branch = branch_result.stdout.strip()
            
            return {
                "success": True,
                "result": {
                    "branch": current_branch,
                    "changes": changes,
                    "total_changes": len(changes)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error obteniendo estado Git: {str(e)}"
            }
    
    def _parse_status(self, status_output: str) -> List[Dict[str, str]]:
        """Parsea la salida de git status --porcelain"""
        changes = []
        for line in status_output.split('\n'):
            if not line.strip():
                continue
            
            status_code = line[:2]
            file_path = line[3:]
            
            status_map = {
                'M ': 'modified',
                ' M': 'modified',
                'A ': 'added',
                'D ': 'deleted',
                'R ': 'renamed',
                '??': 'untracked',
                'MM': 'modified'
            }
            
            changes.append({
                "file": file_path,
                "status": status_map.get(status_code, "unknown")
            })
        
        return changes


class GitDiffTool(BaseTool):
    """Muestra diferencias en archivos"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Muestra cambios en archivos del repositorio"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Archivo específico (opcional, si no se especifica muestra todos)"
                },
                "staged": {
                    "type": "boolean",
                    "description": "Mostrar cambios staged",
                    "default": False
                }
            },
            "required": []
        }
    
    def execute(self, file_path: Optional[str] = None, staged: bool = False, **kwargs) -> Dict[str, Any]:
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr
                }
            
            return {
                "success": True,
                "result": {
                    "diff": result.stdout,
                    "file": file_path,
                    "staged": staged
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error obteniendo diff: {str(e)}"
            }


class GitCommitTool(BaseTool):
    """Realiza un commit en Git"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Crea un commit con los cambios staged"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensaje del commit"
                },
                "files": {
                    "type": "array",
                    "description": "Archivos a incluir (si no se especifica, usa los staged)",
                    "default": []
                }
            },
            "required": ["message"]
        }
    
    def execute(self, message: str, files: List[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            # Agregar archivos si se especificaron
            if files:
                for file in files:
                    add_result = subprocess.run(
                        ["git", "add", file],
                        cwd=str(self.workspace_root),
                        capture_output=True,
                        text=True
                    )
                    if add_result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"Error agregando {file}: {add_result.stderr}"
                        }
            
            # Realizar commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr
                }
            
            return {
                "success": True,
                "result": {
                    "message": message,
                    "output": result.stdout
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error haciendo commit: {str(e)}"
            }


class GitLogTool(BaseTool):
    """Muestra el historial de commits"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Muestra los últimos commits del repositorio"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Número de commits a mostrar",
                    "default": 10
                },
                "file_path": {
                    "type": "string",
                    "description": "Historial de un archivo específico (opcional)"
                }
            },
            "required": []
        }
    
    def execute(self, limit: int = 10, file_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            cmd = [
                "git", "log",
                f"-{limit}",
                "--pretty=format:%H|%an|%ae|%ad|%s",
                "--date=iso"
            ]
            
            if file_path:
                cmd.append("--")
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr
                }
            
            # Parsear commits
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
            
            return {
                "success": True,
                "result": {
                    "commits": commits,
                    "total": len(commits)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error obteniendo log: {str(e)}"
            }


class GitBranchTool(BaseTool):
    """Gestiona branches de Git"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Lista, crea o cambia branches"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Acción: list, create, checkout",
                    "default": "list"
                },
                "branch_name": {
                    "type": "string",
                    "description": "Nombre del branch (para create/checkout)"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, action: str = "list", branch_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            if action == "list":
                result = subprocess.run(
                    ["git", "branch", "-a"],
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True
                )
                
                branches = [b.strip().replace('* ', '') for b in result.stdout.split('\n') if b.strip()]
                current = [b.replace('* ', '') for b in result.stdout.split('\n') if b.startswith('*')]
                
                return {
                    "success": True,
                    "result": {
                        "branches": branches,
                        "current": current[0] if current else None
                    }
                }
            
            elif action == "create":
                if not branch_name:
                    return {"success": False, "error": "branch_name requerido para create"}
                
                result = subprocess.run(
                    ["git", "branch", branch_name],
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True
                )
                
                return {
                    "success": result.returncode == 0,
                    "result": {"branch": branch_name, "created": True} if result.returncode == 0 else None,
                    "error": result.stderr if result.returncode != 0 else None
                }
            
            elif action == "checkout":
                if not branch_name:
                    return {"success": False, "error": "branch_name requerido para checkout"}
                
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True
                )
                
                return {
                    "success": result.returncode == 0,
                    "result": {"branch": branch_name, "checked_out": True} if result.returncode == 0 else None,
                    "error": result.stderr if result.returncode != 0 else None
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Acción no válida: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en operación Git: {str(e)}"
            }