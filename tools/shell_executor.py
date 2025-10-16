"""
Ejecutor de comandos shell con sandbox y validaciones de seguridad.
"""
import subprocess
import shlex
import time
from typing import Tuple, Optional, List, Dict
from pathlib import Path
from datetime import datetime
from tools.safety_checker import SafetyChecker
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ShellExecutor:
    """
    Ejecuta comandos shell de forma segura con validaciones,
    timeouts y registro de historial.
    """
    
    def __init__(self, auto_approve: bool = False):
        """
        Inicializa el ejecutor de comandos.
        
        Args:
            auto_approve: Si True, no pide confirmación (solo para tests)
        """
        self.safety_checker = SafetyChecker()
        self.auto_approve = auto_approve
        self.execution_history: List[Dict] = []
        logger.info(f"ShellExecutor inicializado (auto_approve={auto_approve})")
    
    def execute(
        self,
        command: str,
        cwd: Optional[Path] = None,
        timeout: int = 30,
        capture_output: bool = True
    ) -> Tuple[bool, str, str]:
        """
        Ejecuta un comando shell con validaciones.
        
        Args:
            command: Comando a ejecutar
            cwd: Directorio de trabajo (None = directorio actual)
            timeout: Timeout en segundos
            capture_output: Si capturar stdout/stderr
        
        Returns:
            Tupla (success, stdout, stderr)
        """
        start_time = time.time()
        
        is_safe, safety_msg = self.safety_checker.check_command(command)
        
        if not is_safe:
            logger.warning(f"Comando bloqueado: {command[:50]} - {safety_msg}")
            self._log_execution(command, False, "", safety_msg, 0, cwd)
            return False, "", f"⚠️  Comando bloqueado: {safety_msg}"
        
        if not self.auto_approve and self._requires_confirmation(command):
            logger.info(f"Comando requiere confirmación: {command}")
            if not self._ask_confirmation(command):
                self._log_execution(command, False, "", "Cancelado por usuario", 0, cwd)
                return False, "", "Comando cancelado por el usuario"
        
        try:
            logger.info(f"Ejecutando comando: {command}")
            
            if cwd:
                cwd = Path(cwd).resolve()
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            stdout = result.stdout if capture_output else ""
            stderr = result.stderr if capture_output else ""
            
            if success:
                logger.info(f"Comando exitoso ({duration:.2f}s): {command[:50]}")
            else:
                logger.error(f"Comando falló (rc={result.returncode}): {command[:50]}")
            
            self._log_execution(command, success, stdout, stderr, duration, cwd)
            
            return success, stdout, stderr
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Comando excedió el timeout de {timeout}s"
            logger.error(f"Timeout: {command[:50]}")
            self._log_execution(command, False, "", error_msg, duration, cwd)
            return False, "", f"⏱️  {error_msg}"
        
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Error al ejecutar comando: {str(e)}"
            logger.exception(f"Error ejecutando: {command[:50]}")
            self._log_execution(command, False, "", error_msg, duration, cwd)
            return False, "", f"❌ {error_msg}"
    
    def _requires_confirmation(self, command: str) -> bool:
        """
        Determina si un comando requiere confirmación del usuario.
        
        Args:
            command: Comando a evaluar
        
        Returns:
            True si requiere confirmación
        """
        destructive_keywords = ['rm', 'delete', 'drop', 'truncate', 'format']
        write_keywords = ['>', '>>', 'tee']
        
        command_lower = command.lower()
        
        for keyword in destructive_keywords + write_keywords:
            if keyword in command_lower:
                return True
        
        return False
    
    def _ask_confirmation(self, command: str) -> bool:
        """
        Pide confirmación al usuario para ejecutar un comando.
        
        Args:
            command: Comando a confirmar
        
        Returns:
            True si el usuario confirma
        """
        print(f"\n⚠️  Comando potencialmente destructivo")
        print(f"Comando: {command}")
        response = input("¿Ejecutar este comando? (s/N): ").strip().lower()
        
        confirmed = response in ['s', 'si', 'sí', 'y', 'yes']
        
        if confirmed:
            self.safety_checker.add_approved_command(command)
        
        return confirmed
    
    def _log_execution(
        self,
        command: str,
        success: bool,
        stdout: str,
        stderr: str,
        duration: float,
        cwd: Optional[Path]
    ) -> None:
        """
        Registra una ejecución en el historial.
        
        Args:
            command: Comando ejecutado
            success: Si fue exitoso
            stdout: Salida estándar
            stderr: Salida de error
            duration: Duración en segundos
            cwd: Directorio de trabajo
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': success,
            'stdout': stdout[:500] if stdout else "",
            'stderr': stderr[:500] if stderr else "",
            'duration': duration,
            'cwd': str(cwd) if cwd else str(Path.cwd())
        }
        
        self.execution_history.append(entry)
        
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene el historial de ejecuciones.
        
        Args:
            limit: Número máximo de entradas
        
        Returns:
            Lista de ejecuciones (más recientes primero)
        """
        return list(reversed(self.execution_history[-limit:]))
    
    def clear_history(self) -> None:
        """Limpia el historial de ejecuciones"""
        self.execution_history.clear()
        logger.info("Historial de ejecuciones limpiado")
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas de ejecuciones.
        
        Returns:
            Diccionario con estadísticas
        """
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e['success'])
        failed = total - successful
        
        return {
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'safety_stats': self.safety_checker.get_stats()
        }
