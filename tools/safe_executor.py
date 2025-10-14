"""
Sistema de ejecución segura de comandos y código.
Proporciona sandbox y validación para operaciones potencialmente peligrosas.
"""

import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration: float


class SafeExecutor:
    def __init__(self):
        self.allowed_commands = settings.security.allowed_commands
        self.blocked_commands = settings.security.blocked_commands
        self.max_timeout = 60
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Valida que un comando sea seguro para ejecutar.
        
        Returns:
            (is_valid, error_message)
        """
        if not command or not command.strip():
            return False, "Comando vacío"
        
        cmd_parts = command.strip().split()
        base_cmd = cmd_parts[0]
        
        for blocked in self.blocked_commands:
            if blocked in command.lower():
                return False, f"Comando bloqueado por seguridad: {blocked}"
        
        if base_cmd not in self.allowed_commands and base_cmd not in ['git']:
            return False, f"Comando no permitido: {base_cmd}"
        
        dangerous_patterns = ['rm -rf /', 'format', '> /dev/', 'dd if=', 'mkfs']
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return False, f"Patrón peligroso detectado: {pattern}"
        
        return True, ""
    
    def run_command(
        self, 
        command: str, 
        cwd: Optional[Path] = None,
        timeout: int = 30,
        capture_output: bool = True
    ) -> ExecutionResult:
        """
        Ejecuta un comando de forma segura.
        
        Args:
            command: Comando a ejecutar
            cwd: Directorio de trabajo
            timeout: Timeout en segundos
            capture_output: Si capturar stdout/stderr
        
        Returns:
            ExecutionResult con resultado de la ejecución
        """
        import time
        
        is_valid, error = self.validate_command(command)
        if not is_valid:
            logger.warning(f"Comando rechazado: {command} - {error}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=error,
                exit_code=-1,
                duration=0.0
            )
        
        cwd = cwd or Path.cwd()
        timeout = min(timeout, self.max_timeout)
        
        try:
            logger.info(f"Ejecutando: {command} (timeout: {timeout}s)")
            start_time = time.time()
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            logger.info(f"Comando completado en {duration:.2f}s (exit code: {result.returncode})")
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                exit_code=result.returncode,
                duration=duration
            )
        
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando: {command}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Timeout después de {timeout}s",
                exit_code=-1,
                duration=timeout
            )
        
        except Exception as e:
            logger.exception(f"Error ejecutando: {command}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration=0.0
            )
    
    def run_in_sandbox(
        self,
        code: str,
        language: str = 'python',
        timeout: int = 10
    ) -> ExecutionResult:
        """
        Ejecuta código en un archivo temporal aislado.
        
        Args:
            code: Código a ejecutar
            language: Lenguaje (python, javascript, bash)
            timeout: Timeout en segundos
        
        Returns:
            ExecutionResult con resultado
        """
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'bash': '.sh'
        }
        
        runners = {
            'python': 'python3',
            'javascript': 'node',
            'bash': 'bash'
        }
        
        if language not in extensions:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Lenguaje no soportado: {language}",
                exit_code=-1,
                duration=0.0
            )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file = Path(tmpdir) / f"script{extensions[language]}"
            temp_file.write_text(code)
            
            command = f"{runners[language]} {temp_file}"
            
            return self.run_command(
                command,
                cwd=Path(tmpdir),
                timeout=timeout
            )
    
    def run_tests(
        self,
        path: Optional[Path] = None,
        framework: str = 'pytest'
    ) -> ExecutionResult:
        """
        Ejecuta tests del proyecto de forma segura.
        
        Args:
            path: Ruta a los tests (None = todo el proyecto)
            framework: Framework de testing (pytest, jest, etc)
        
        Returns:
            ExecutionResult con resultados de tests
        """
        commands = {
            'pytest': f"pytest {path or '.'} -v --tb=short",
            'unittest': f"python3 -m unittest discover {path or '.'}",
            'jest': f"npm test -- {path or ''}",
            'vitest': f"npm run test -- {path or ''}"
        }
        
        if framework not in commands:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Framework no soportado: {framework}",
                exit_code=-1,
                duration=0.0
            )
        
        command = commands[framework]
        logger.info(f"Ejecutando tests: {command}")
        
        return self.run_command(command, timeout=60)
    
    def format_code(
        self,
        path: Path,
        tool: str = 'auto'
    ) -> ExecutionResult:
        """
        Formatea código usando herramientas estándar.
        
        Args:
            path: Archivo o directorio a formatear
            tool: Herramienta (auto, black, prettier, rustfmt)
        
        Returns:
            ExecutionResult con resultado del formateo
        """
        if tool == 'auto':
            suffix = Path(path).suffix
            tool_map = {
                '.py': 'black',
                '.js': 'prettier',
                '.jsx': 'prettier',
                '.ts': 'prettier',
                '.tsx': 'prettier',
                '.rs': 'rustfmt'
            }
            tool = tool_map.get(suffix, 'none')
        
        commands = {
            'black': f"black {path}",
            'prettier': f"prettier --write {path}",
            'rustfmt': f"rustfmt {path}",
            'autopep8': f"autopep8 --in-place {path}"
        }
        
        if tool not in commands:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Herramienta no disponible: {tool}",
                exit_code=-1,
                duration=0.0
            )
        
        return self.run_command(commands[tool], timeout=30)
    
    def lint_code(
        self,
        path: Path,
        tool: str = 'auto'
    ) -> ExecutionResult:
        """
        Ejecuta linter en código.
        
        Args:
            path: Archivo o directorio
            tool: Linter (auto, flake8, eslint, clippy)
        
        Returns:
            ExecutionResult con warnings/errores
        """
        if tool == 'auto':
            suffix = Path(path).suffix
            tool_map = {
                '.py': 'flake8',
                '.js': 'eslint',
                '.jsx': 'eslint',
                '.ts': 'eslint',
                '.tsx': 'eslint',
                '.rs': 'clippy'
            }
            tool = tool_map.get(suffix, 'none')
        
        commands = {
            'flake8': f"flake8 {path}",
            'pylint': f"pylint {path}",
            'eslint': f"eslint {path}",
            'clippy': f"cargo clippy -- -D warnings"
        }
        
        if tool not in commands:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Linter no disponible: {tool}",
                exit_code=-1,
                duration=0.0
            )
        
        return self.run_command(commands[tool], timeout=30)
