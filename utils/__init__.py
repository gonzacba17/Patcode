"""
Paquete de utilidades para Patocode
"""

# Imports seguros - solo importar lo que existe
try:
    from .validators import (
        validate_file_path,
        validate_directory_path,
        validate_command,
        validate_model_name,
        validate_url,
        validate_port,
        validate_file_extension,
        validate_json_string,
        validate_config,
        sanitize_input
    )
except ImportError as e:
    print(f"Advertencia: No se pudieron importar algunos validadores: {e}")

try:
    from .formatters import format_code
except ImportError as e:
    print(f"Advertencia: No se pudieron importar algunos formateadores: {e}")

try:
    from .colors import Colors, colorize
except ImportError as e:
    print(f"Advertencia: No se pudieron importar colores: {e}")

# NO importar funciones que no existen
# Comentadas hasta que se implementen:
# from .formatters import format_file_path, format_error, format_table, truncate_text

__all__ = [
    # Validators
    'validate_file_path',
    'validate_directory_path',
    'validate_command',
    'validate_model_name',
    'validate_url',
    'validate_port',
    'validate_file_extension',
    'validate_json_string',
    'validate_config',
    'sanitize_input',
    # Formatters (solo lo que existe)
    'format_code',
    # Colors
    'Colors',
    'colorize',
]