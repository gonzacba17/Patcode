"""
Módulo de utilidades para PatCode.
Proporciona herramientas auxiliares como formateo, logging, colores, etc.
"""

from .colors import Colors, colorize, print_colored
from .formatters import (
    format_code,
    format_file_path,
    format_error,
    format_success,
    format_table,
    truncate_text
)
from .diff_viewer import DiffViewer, show_diff
from .logger import Logger, get_logger
from .validators import (
    validate_path,
    validate_command,
    sanitize_input,
    is_safe_path
)

__all__ = [
    # Colors
    'Colors',
    'colorize',
    'print_colored',
    
    # Formatters
    'format_code',
    'format_file_path',
    'format_error',
    'format_success',
    'format_table',
    'truncate_text',
    
    # Diff viewer
    'DiffViewer',
    'show_diff',
    
    # Logger
    'Logger',
    'get_logger',
    
    # Validators
    'validate_path',
    'validate_command',
    'sanitize_input',
    'is_safe_path',
]

__version__ = '1.0.0'