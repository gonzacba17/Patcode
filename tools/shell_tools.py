"""
tools/shell_tools.py
Herramientas para ejecutar comandos de shell
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_tool import BaseTool


class RunCommandTool(BaseTool):
    """Ejecuta un comando de shell"""
    
    def __init__(self, workspace_root: str = ".", allowed_commands: Optional[List[str]] = None):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Ejecuta un comando de shell de forma segura"
        
        # Comandos permitidos por seguridad
        self.allowed_commands = allowed_commands or [
            "python", "python3", "pip", "pip3",
            "node", "npm", "npx",
            "git",
            "ls", "dir", "pwd", "cd",
            "cat", "echo",
            "pytest", "jest", "cargo", "go"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Comando a ejecutar (ej: 'python script.py', 'npm test')"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout en segundos",
                    "default": 30
                },
                "capture_output": {
                    "type": "boolean",
                    "description": "Capturar stdout y stderr",
                    "default": True
                }
            },
            "required": ["command"]
        }
    
    def execute(self, command: str, timeout: int = 30, 
                capture_output: bool = True, **kwargs) -> Dict[str, Any]:
        try:
            # Validar comando
            cmd_parts = command.strip().split()
            if not cmd_parts:
                return {
                    "success": False,
                    "error": "Comando vacío"
                }
            
            base_cmd = cmd_parts[0]
            
            # Verificar si está permitido
            if not self._is_allowed(base_cmd):
                return {
                    "success": False,
                    "error": f"Comando no permitido: {base_cmd}. Comandos permitidos: {', '.join(self.allowed_commands)}"
                }
            
            # Ejecutar comando
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "result": {
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout if capture_output else None,
                    "stderr": result.stderr if capture_output else None,
                    "working_directory": str(self.workspace_root)
                }
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Comando excedió el timeout de {timeout} segundos"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error ejecutando comando: {str(e)}"
            }
    
    def _is_allowed(self, command: str) -> bool:
        """Verifica si el comando está permitido"""
        return any(command.startswith(allowed) or command == allowed 
                  for allowed in self.allowed_commands)


class RunPythonScriptTool(BaseTool):
    """Ejecuta un script de Python"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Ejecuta un script de Python y captura su salida"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "description": "Ruta del script Python a ejecutar"
                },
                "args": {
                    "type": "array",
                    "description": "Argumentos para el script",
                    "default": []
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout en segundos",
                    "default": 30
                }
            },
            "required": ["script_path"]
        }
    
    def execute(self, script_path: str, args: List[str] = None, 
                timeout: int = 30, **kwargs) -> Dict[str, Any]:
        try:
            if args is None:
                args = []
            
            full_path = self._resolve_path(script_path)
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Script no encontrado: {script_path}"
                }
            
            # Construir comando
            cmd = ["python", str(full_path)] + args
            
            # Ejecutar
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "result": {
                    "script": str(full_path),
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script excedió el timeout de {timeout} segundos"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error ejecutando script: {str(e)}"
            }
    
    def _resolve_path(self, script_path: str) -> Path:
        """Resuelve ruta relativa al workspace"""
        path = Path(script_path)
        if not path.is_absolute():
            path = self.workspace_root / path
        return path.resolve()


class RunTestsTool(BaseTool):
    """Ejecuta tests del proyecto"""
    
    def __init__(self, workspace_root: str = "."):
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Ejecuta tests usando pytest, unittest u otros frameworks"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_path": {
                    "type": "string",
                    "description": "Ruta del test o directorio de tests",
                    "default": "tests/"
                },
                "framework": {
                    "type": "string",
                    "description": "Framework de testing (pytest, unittest, jest)",
                    "default": "pytest"
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Modo verbose",
                    "default": True
                }
            },
            "required": []
        }
    
    def execute(self, test_path: str = "tests/", framework: str = "pytest", 
                verbose: bool = True, **kwargs) -> Dict[str, Any]:
        try:
            # Construir comando según framework
            if framework == "pytest":
                cmd = ["pytest", test_path]
                if verbose:
                    cmd.append("-v")
            elif framework == "unittest":
                cmd = ["python", "-m", "unittest", "discover", "-s", test_path]
                if verbose:
                    cmd.append("-v")
            elif framework == "jest":
                cmd = ["npm", "test"]
            else:
                return {
                    "success": False,
                    "error": f"Framework no soportado: {framework}"
                }
            
            # Ejecutar tests
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "result": {
                    "framework": framework,
                    "test_path": test_path,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "passed": result.returncode == 0
                }
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests excedieron el timeout de 60 segundos"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error ejecutando tests: {str(e)}"
            }