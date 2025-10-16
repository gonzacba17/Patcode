"""
Sistema de validación de seguridad para comandos y archivos.
Protege contra comandos destructivos y operaciones peligrosas.
"""
import re
from typing import Tuple, List, Set
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SafetyChecker:
    """
    Valida comandos shell y operaciones de archivo para prevenir
    acciones destructivas o maliciosas.
    """
    
    DANGEROUS_COMMANDS: Set[str] = {
        'rm -rf /',
        'rm -rf *',
        'rm -rf ~',
        'dd if=',
        'mkfs',
        'format',
        '> /dev/sda',
        'chmod 777',
        'chmod -R 777',
        'chown root',
        'sudo su',
        'sudo -i',
        ':(){:|:&};:',
    }
    
    DANGEROUS_PATTERNS: List[str] = [
        r'rm\s+-rf\s+[/~]',
        r':\(\)\{.*\};:',
        r'dd\s+if=.*of=/dev/',
        r'eval\s*\(',
        r'mkfs\.',
        r'fdisk\s+/dev/',
        r'parted\s+/dev/',
        r'wget.*\|.*bash',
        r'curl.*\|.*sh',
        r'chmod\s+-R\s+777',
        r'>/dev/sd[a-z]',
    ]
    
    SUSPICIOUS_KEYWORDS: Set[str] = {
        'wget', 'curl', 'nc', 'netcat', 'telnet',
        'format', 'mkfs', 'fdisk', 'parted',
        'sudo', 'su', 'doas',
    }
    
    ALLOWED_EXTENSIONS: Set[str] = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.rb', '.php', '.go', '.rs',
        '.swift', '.kt', '.scala', '.r',
        '.html', '.css', '.scss', '.sass', '.less',
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.toml', '.ini', '.conf', '.config',
        '.xml', '.sql', '.sh', '.bash',
        '.env', '.gitignore', '.dockerignore',
    }
    
    BINARY_EXTENSIONS: Set[str] = {
        '.exe', '.dll', '.so', '.dylib',
        '.bin', '.dat', '.pyc', '.pyo',
        '.class', '.jar', '.war',
    }
    
    CRITICAL_FILES: Set[str] = {
        '.env',
        '.git/config',
        '.ssh/id_rsa',
        '.ssh/id_ed25519',
        '/etc/passwd',
        '/etc/shadow',
        '/etc/sudoers',
    }
    
    def __init__(self):
        """Inicializa el validador de seguridad"""
        self.user_approved_commands: List[str] = []
        self.blocked_count = 0
        self.allowed_count = 0
        logger.info("SafetyChecker inicializado")
    
    def check_command(self, command: str) -> Tuple[bool, str]:
        """
        Valida si un comando es seguro para ejecutar.
        
        Args:
            command: Comando a validar
        
        Returns:
            Tupla (es_seguro, mensaje)
        """
        command_lower = command.lower().strip()
        
        if command in self.user_approved_commands:
            logger.info(f"Comando pre-aprobado: {command[:50]}")
            self.allowed_count += 1
            return True, "Comando pre-aprobado por el usuario"
        
        for dangerous_cmd in self.DANGEROUS_COMMANDS:
            if dangerous_cmd in command_lower:
                logger.warning(f"Comando peligroso bloqueado: {command[:50]}")
                self.blocked_count += 1
                return False, f"Comando prohibido detectado: '{dangerous_cmd}'"
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(f"Patrón peligroso detectado: {command[:50]}")
                self.blocked_count += 1
                return False, f"Patrón peligroso detectado en el comando"
        
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in command_lower:
                logger.info(f"Comando sospechoso requiere aprobación: {command[:50]}")
                return False, f"Comando contiene palabra clave sospechosa: '{keyword}'. Requiere aprobación manual."
        
        self.allowed_count += 1
        logger.debug(f"Comando validado: {command[:50]}")
        return True, "Comando validado correctamente"
    
    def check_file_operation(self, filepath: Path, operation: str) -> Tuple[bool, str]:
        """
        Valida si una operación sobre un archivo es segura.
        
        Args:
            filepath: Ruta del archivo
            operation: Tipo de operación ('read', 'write', 'delete')
        
        Returns:
            Tupla (es_segura, mensaje)
        """
        try:
            filepath = filepath.resolve()
        except Exception as e:
            logger.error(f"Error al resolver ruta: {e}")
            return False, f"Ruta de archivo inválida: {e}"
        
        if not filepath.exists() and operation == 'read':
            return False, "El archivo no existe"
        
        file_str = str(filepath)
        for critical in self.CRITICAL_FILES:
            if critical in file_str:
                logger.warning(f"Intento de {operation} en archivo crítico: {filepath}")
                return False, f"Operación en archivo crítico requiere confirmación explícita: {filepath.name}"
        
        if filepath.suffix.lower() in self.BINARY_EXTENSIONS:
            logger.warning(f"Intento de {operation} archivo binario: {filepath}")
            return False, f"Operación en archivos binarios no permitida: {filepath.suffix}"
        
        if operation in ['write', 'delete']:
            if filepath.suffix.lower() not in self.ALLOWED_EXTENSIONS and filepath.suffix:
                logger.warning(f"Extensión no permitida para {operation}: {filepath.suffix}")
                return False, f"Extensión de archivo no permitida para {operation}: {filepath.suffix}"
        
        try:
            cwd = Path.cwd()
            filepath.relative_to(cwd)
        except ValueError:
            logger.warning(f"Operación fuera del directorio del proyecto: {filepath}")
            return False, "Operación solo permitida dentro del directorio del proyecto"
        
        logger.debug(f"Operación {operation} validada para: {filepath}")
        return True, "Operación validada"
    
    def add_approved_command(self, command: str) -> None:
        """
        Agrega un comando a la lista de aprobados.
        
        Args:
            command: Comando a aprobar
        """
        if command not in self.user_approved_commands:
            self.user_approved_commands.append(command)
            logger.info(f"Comando agregado a lista de aprobados: {command[:50]}")
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas de validaciones.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'blocked_count': self.blocked_count,
            'allowed_count': self.allowed_count,
            'approved_commands': len(self.user_approved_commands)
        }
    
    def clear_approved_commands(self) -> None:
        """Limpia la lista de comandos aprobados"""
        self.user_approved_commands.clear()
        logger.info("Lista de comandos aprobados limpiada")
