# tools/shell_operations.py
import subprocess
from typing import Tuple

class ShellOperations:
    """Herramientas para ejecutar comandos de terminal"""
    
    @staticmethod
    def run_command(command: str, cwd: str = None) -> Tuple[str, str, int]:
        """
        Ejecuta un comando de shell
        Returns: (stdout, stderr, return_code)
        """
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    
    @staticmethod
    def run_test(test_path: str = None) -> Tuple[bool, str]:
        """Ejecuta tests y retorna resultados"""
        cmd = f"pytest {test_path}" if test_path else "pytest"
        stdout, stderr, code = ShellOperations.run_command(cmd)
        return code == 0, stdout + stderr