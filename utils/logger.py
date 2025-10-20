"""
Sistema de logging profesional con colores, rotación de archivos y logs estructurados.
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any
from config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Formatter con colores ANSI para terminal"""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """Formatter para logs estructurados en JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno,
            'module': record.module
        }
        
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logger(name: str, structured: bool = False) -> logging.Logger:
    """
    Configura logger con salida a consola (colores), archivo (rotación) y logs estructurados.
    
    Args:
        name: Nombre del logger (usa __name__)
        structured: Si True, usa logs estructurados en JSON para archivo
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, settings.logging.level))
    
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    logger.addHandler(console)
    
    if settings.logging.file:
        log_path = Path(settings.logging.filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
            ))
        
        logger.addHandler(file_handler)
    
    return logger


def log_metric(logger: logging.Logger, metric_name: str, value: Any, metadata: Dict[str, Any] = None):
    """
    Log de métrica estructurada.
    
    Args:
        logger: Logger a usar
        metric_name: Nombre de la métrica
        value: Valor de la métrica
        metadata: Metadatos adicionales
    """
    extra_data = {
        'metric': metric_name,
        'value': value,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if metadata:
        extra_data.update(metadata)
    
    logger.info(f"METRIC: {metric_name}={value}", extra={'extra_data': extra_data})


class Logger:
    """Logger personalizado para PatCode (legacy)"""
    
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
        self.logger = setup_logger(name)
    
    def _setup_handlers(self):
        pass
    
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