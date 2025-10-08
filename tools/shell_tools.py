"""
tools/shell_tools.py
Herramientas para ejecutar comandos y buscar archivos
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List


class ExecuteCommandTool:
    """Ejecuta comandos de shell de forma segura"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Ejecuta un comando de shell"
        
        # Comandos permitidos por seguridad
        self.allowed_commands = [
            "python", "python3", "pip", "pip3",
            "node", "npm", "npx",
            "git",
            "ls", "dir", "pwd", "cd", "cat", "echo",
            "pytest", "black", "flake8", "mypy"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Comando a ejecutar"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout en segundos",
                    "default": 30
                }
            },
            "required": ["command"]
        }
    
    def execute(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un comando de shell
        
        Args:
            command: Comando a ejecutar
            timeout: Tiempo máximo de ejecución
            
        Returns:
            Dict con success, result o error
        """
        try:
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
                    "error": f"Comando no permitido: {base_cmd}"
                }
            
            # Ejecutar comando
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "result": {
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
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


class SearchFilesTool:
    """Busca archivos por patrón o nombre"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.description = "Busca archivos por patrón glob"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Patrón de búsqueda (ej: '*.py', '**/*.js')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Máximo número de resultados",
                    "default": 50
                }
            },
            "required": ["pattern"]
        }
    
    def execute(self, pattern: str, max_results: int = 50, **kwargs) -> Dict[str, Any]:
        """
        Busca archivos por patrón
        
        Args:
            pattern: Patrón glob para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Dict con success, result o error
        """
        try:
            matches = []
            
            # Buscar archivos
            for file_path in self.workspace_root.glob(pattern):
                if file_path.is_file():
                    matches.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.workspace_root)),
                        "size": file_path.stat().st_size
                    })
                    
                    if len(matches) >= max_results:
                        break
            
            return {
                "success": True,
                "result": {
                    "pattern": pattern,
                    "matches": matches,
                    "total": len(matches)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error buscando archivos: {str(e)}"
            }