"""
Shell Executor - FASE 2: Sistema Multi-LLM y Shell Executor

Ejecutor de comandos shell con seguridad, whitelist y logging.
"""

import subprocess
import os
import time
import logging
import platform
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Resultado de ejecutar un comando."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str
    duration: float


class ShellExecutor:
    """
    Tool para ejecutar comandos de shell de forma segura.
    
    Características:
    - Whitelist de comandos permitidos
    - Timeout para prevenir comandos colgados
    - Captura de stdout/stderr
    - Working directory configurable
    - Logging de todos los comandos ejecutados
    """
    
    ALLOWED_COMMANDS = {
        "pytest", "npm", "yarn", "jest", "vitest", "cargo",
        "pip", "poetry", "pipenv", "pnpm",
        "git",
        "make", "cmake", "mvn", "gradle",
        "black", "flake8", "mypy", "eslint", "prettier", "ruff",
        "node", "python", "python3",
        "docker", "docker-compose",
        "ls", "cat", "grep", "find", "tree", "pwd", "echo"
    }
    
    DANGEROUS_COMMANDS = {
        "rm", "rmdir", "del", "format", "dd", "mkfs",
        "shutdown", "reboot", "kill", "killall",
        "chmod", "chown", "sudo", "su",
        "curl", "wget"
    }
    
    def __init__(
        self,
        working_dir: str = ".",
        timeout: int = 300,
        allow_shell: bool = False
    ):
        """
        Inicializa el ejecutor de shell.
        
        Args:
            working_dir: Directorio de trabajo
            timeout: Timeout default en segundos
            allow_shell: Permitir shell=True (peligroso)
        """
        self.working_dir = os.path.abspath(working_dir)
        self.timeout = timeout
        self.allow_shell = allow_shell
        self.command_history: List[Dict[str, Any]] = []
        self.is_windows = platform.system() == "Windows"
        
        logger.info(f"ShellExecutor initialized: {self.working_dir}")
        logger.debug(f"Platform: {platform.system()}")
    
    def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Ejecuta un comando de shell.
        
        Args:
            command: Comando a ejecutar (ej: "pytest tests/")
            timeout: Timeout en segundos (usa self.timeout si es None)
            env: Variables de entorno adicionales
            
        Returns:
            CommandResult con el resultado
            
        Raises:
            ValueError: Si el comando no está permitido
            subprocess.TimeoutExpired: Si el comando excede el timeout
        """
        parts = command.split()
        base_command = parts[0] if parts else ""
        
        if base_command in self.DANGEROUS_COMMANDS:
            raise ValueError(f"❌ Dangerous command not allowed: {base_command}")
        
        if base_command not in self.ALLOWED_COMMANDS:
            raise ValueError(
                f"❌ Command not allowed: {base_command}\n"
                f"Allowed commands: {', '.join(sorted(self.ALLOWED_COMMANDS))}"
            )
        
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        
        exec_timeout = timeout or self.timeout
        
        logger.info(f"🔧 Executing: {command}")
        logger.info(f"📁 Working dir: {self.working_dir}")
        
        start_time = time.time()
        
        try:
            if self.is_windows:
                result = subprocess.run(
                    command,
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True,
                    timeout=exec_timeout,
                    env=exec_env,
                    shell=True
                )
            else:
                result = subprocess.run(
                    parts,
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True,
                    timeout=exec_timeout,
                    env=exec_env,
                    shell=self.allow_shell
                )
            
            duration = time.time() - start_time
            
            cmd_result = CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                command=command,
                duration=duration
            )
            
            if cmd_result.success:
                logger.info(f"✅ Command successful ({duration:.2f}s)")
            else:
                logger.warning(f"❌ Command failed with code {result.returncode}")
                if result.stderr:
                    logger.warning(f"stderr: {result.stderr[:500]}")
            
            self.command_history.append({
                "command": command,
                "timestamp": time.time(),
                "success": cmd_result.success,
                "duration": duration,
                "exit_code": result.returncode
            })
            
            return cmd_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"⏱️ Command timeout after {exec_timeout}s")
            
            cmd_result = CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {exec_timeout}s",
                exit_code=-1,
                command=command,
                duration=duration
            )
            
            self.command_history.append({
                "command": command,
                "timestamp": time.time(),
                "success": False,
                "duration": duration,
                "exit_code": -1
            })
            
            return cmd_result
        
        except FileNotFoundError as e:
            duration = time.time() - start_time
            logger.error(f"💥 Command not found: {command}")
            
            cmd_result = CommandResult(
                success=False,
                stdout="",
                stderr=f"Command not found: {str(e)}",
                exit_code=-1,
                command=command,
                duration=duration
            )
            
            self.command_history.append({
                "command": command,
                "timestamp": time.time(),
                "success": False,
                "duration": duration,
                "exit_code": -1
            })
            
            return cmd_result
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"💥 Error executing command: {e}")
            
            cmd_result = CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                command=command,
                duration=duration
            )
            
            self.command_history.append({
                "command": command,
                "timestamp": time.time(),
                "success": False,
                "duration": duration,
                "exit_code": -1
            })
            
            return cmd_result
    
    def execute_multiple(
        self,
        commands: List[str],
        stop_on_error: bool = True
    ) -> List[CommandResult]:
        """
        Ejecuta múltiples comandos en secuencia.
        
        Args:
            commands: Lista de comandos a ejecutar
            stop_on_error: Si True, detiene en el primer error
            
        Returns:
            Lista de CommandResult
        """
        results = []
        
        for cmd in commands:
            try:
                result = self.execute(cmd)
                results.append(result)
                
                if not result.success and stop_on_error:
                    logger.warning(f"⏹️ Stopping execution due to error in: {cmd}")
                    break
                    
            except Exception as e:
                logger.error(f"Error in command '{cmd}': {e}")
                if stop_on_error:
                    break
        
        return results
    
    def can_execute(self, command: str) -> Tuple[bool, str]:
        """
        Verifica si un comando se puede ejecutar.
        
        Args:
            command: Comando a verificar
            
        Returns:
            (can_execute: bool, reason: str)
        """
        parts = command.split()
        if not parts:
            return False, "Empty command"
        
        base_command = parts[0]
        
        if base_command in self.DANGEROUS_COMMANDS:
            return False, f"Dangerous command: {base_command}"
        
        if base_command not in self.ALLOWED_COMMANDS:
            return False, f"Command not in whitelist: {base_command}"
        
        return True, "OK"
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna los últimos N comandos ejecutados.
        
        Args:
            limit: Número de comandos a retornar
            
        Returns:
            Lista de diccionarios con info de comandos
        """
        return self.command_history[-limit:]
    
    def clear_history(self) -> None:
        """Limpia el historial de comandos."""
        self.command_history.clear()
        logger.info("Command history cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ejecución.
        
        Returns:
            Dict con estadísticas
        """
        total = len(self.command_history)
        successful = sum(1 for cmd in self.command_history if cmd["success"])
        failed = total - successful
        
        avg_duration = 0.0
        if total > 0:
            avg_duration = sum(cmd["duration"] for cmd in self.command_history) / total
        
        return {
            "total_commands": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_duration_seconds": avg_duration
        }
