"""
Sistema de logging para PatCode
"""

import logging
import os
from datetime import datetime
from .colors import Colors, colorize


class Logger:
    """Logger personalizado para PatCode"""
    
    def __init__(self, name="PatCode", log_dir="logs", log_level=logging.INFO):
        """
        Inicializa el logger
        
        Args:
            name (str): Nombre del logger
            log_dir (str): Directorio para los logs
            log_level: Nivel de logging
        """
        self.name = name
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Crear directorio de logs si no existe
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configurar handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers de archivo y consola"""
        # Handler de archivo
        log_file = os.path.join(
            self.log_dir,
            f"patcode_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        """Log de debug"""
        self.logger.debug(message)
    
    def info(self, message):
        """Log de información"""
        colored_msg = colorize(f"ℹ {message}", Colors.BRIGHT_BLUE)
        self.logger.info(colored_msg)
    
    def success(self, message):
        """Log de éxito"""
        colored_msg = colorize(f"✓ {message}", Colors.BRIGHT_GREEN, Colors.BOLD)
        self.logger.info(colored_msg)
    
    def warning(self, message):
        """Log de advertencia"""
        colored_msg = colorize(f"⚠ {message}", Colors.BRIGHT_YELLOW, Colors.BOLD)
        self.logger.warning(colored_msg)
    
    def error(self, message):
        """Log de error"""
        colored_msg = colorize(f"✗ {message}", Colors.BRIGHT_RED, Colors.BOLD)
        self.logger.error(colored_msg)
    
    def critical(self, message):
        """Log crítico"""
        colored_msg = colorize(f"🔥 {message}", Colors.RED, Colors.BOLD)
        self.logger.critical(colored_msg)
    
    def log_command(self, command):
        """Registra un comando ejecutado"""
        colored_msg = colorize(f"$ {command}", Colors.CYAN)
        self.logger.info(colored_msg)
    
    def log_response(self, response):
        """Registra una respuesta del modelo"""
        self.logger.debug(f"Response: {response[:100]}...")
    
    def log_file_operation(self, operation, file_path):
        """Registra operaciones sobre archivos"""
        msg = colorize(f"📄 {operation}: {file_path}", Colors.MAGENTA)
        self.logger.info(msg)
    
    def separator(self):
        """Imprime un separador visual"""
        separator = colorize("-" * 60, Colors.DIM)
        self.logger.info(separator)


# Instancia global del logger
_global_logger = None


def get_logger():
    """Obtiene la instancia global del logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger