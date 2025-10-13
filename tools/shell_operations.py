# ============================================================================
# tools/shell_operations.py - VERSIÓN CORREGIDA
# ============================================================================

import subprocess
import shlex
from typing import Tuple, Optional, List
import os


class ShellOperations:
    """
    Herramientas para ejecutar comandos de shell de forma segura.
    Incluye timeout, validación y captura de output.
    """
    
    # Comandos peligrosos bloqueados
    BLOCKED_COMMANDS = {
        'rm -rf /', 'format', 'del /f', 'mkfs',
        'dd if=/dev/zero', ':(){ :|:& };:', 'chmod -R 777 /'
    }
    
    # Comandos permitidos explícitamente
    SAFE_COMMANDS = {
        'pytest', 'python', 'pip', 'git', 'ls', 'cat',
        'grep', 'find', 'echo', 'cd', 'pwd', 'node',
        'npm', 'yarn', 'make', 'cargo', 'go', 'rustc',
        'dir', 'type'  # Windows
    }
    
    def __init__(self, working_dir: str = "."):
        """
        Inicializa el sistema de operaciones de shell.
        
        Args:
            working_dir: Directorio de trabajo por defecto
        """
        self.working_dir = os.path.abspath(working_dir)
    
    def _is_safe_command(self, command: str) -> Tuple[bool, str]:
        """
        Verifica si un comando es seguro de ejecutar.
        
        Args:
            command: Comando a verificar
            
        Returns:
            Tuple (is_safe, message)
        """
        # Verificar comandos bloqueados
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command.lower():
                return False, f"Comando bloqueado por seguridad: {blocked}"
        
        # Extraer comando base
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Comando vacío"
            
            base_command = parts[0]
            
            # Verificar si está en comandos seguros
            if any(safe in base_command for safe in self.SAFE_COMMANDS):
                return True, "Comando permitido"
            
            # Por defecto, pedir confirmación para comandos desconocidos
            return False, f"Comando '{base_command}' requiere confirmación manual"
            
        except Exception as e:
            return False, f"Error al parsear comando: {str(e)}"
    
    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 30,
        capture_output: bool = True
    ) -> Tuple[str, str, int]:
        """
        Ejecuta un comando de shell.
        
        Args:
            command: Comando a ejecutar
            cwd: Directorio de trabajo (None = usar working_dir)
            timeout: Timeout en segundos
            capture_output: Si True, captura stdout/stderr
            
        Returns:
            Tuple (stdout, stderr, return_code)
        """
        # Verificar seguridad
        is_safe, message = self._is_safe_command(command)
        if not is_safe:
            return "", f"BLOCKED: {message}", -1
        
        # Directorio de trabajo
        work_dir = cwd if cwd else self.working_dir
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            return result.stdout, result.stderr, result.returncode
            
        except subprocess.TimeoutExpired:
            return "", f"Comando excedió timeout de {timeout}s", -1
        except Exception as e:
            return "", f"Error al ejecutar comando: {str(e)}", -1
    
    def run_python_script(self, script_path: str, args: List[str] = None) -> Tuple[str, str, int]:
        """
        Ejecuta un script de Python.
        
        Args:
            script_path: Ruta al script
            args: Argumentos adicionales
            
        Returns:
            Tuple (stdout, stderr, return_code)
        """
        args = args or []
        command = f"python {script_path} {' '.join(args)}"
        return self.run_command(command)
    
    def run_tests(self, test_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Ejecuta tests con pytest.
        
        Args:
            test_path: Ruta específica de tests (None = todos)
            
        Returns:
            Tuple (success, output)
        """
        command = f"pytest {test_path}" if test_path else "pytest"
        stdout, stderr, code = self.run_command(command, timeout=60)
        
        output = stdout + stderr
        success = code == 0
        
        return success, output
    
    def check_syntax(self, file_path: str) -> Tuple[bool, str]:
        """
        Verifica la sintaxis de un archivo Python.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Tuple (is_valid, message)
        """
        command = f"python -m py_compile {file_path}"
        stdout, stderr, code = self.run_command(command)
        
        if code == 0:
            return True, "Sintaxis correcta"
        else:
            return False, stderr