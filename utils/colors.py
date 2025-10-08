"""
Módulo de colores para la terminal
"""

class Colors:
    """Códigos ANSI para colorear texto en terminal"""
    
    # Colores básicos
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Colores brillantes
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Estilos
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    
    # Reset
    RESET = '\033[0m'
    
    # Colores de fondo
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


def colorize(text, color=None, style=None, bg_color=None):
    """
    Colorea un texto para terminal
    
    Args:
        text (str): Texto a colorear
        color (str): Color del texto (ej: Colors.GREEN)
        style (str): Estilo del texto (ej: Colors.BOLD)
        bg_color (str): Color de fondo
    
    Returns:
        str: Texto coloreado
    """
    result = ""
    
    if style:
        result += style
    if bg_color:
        result += bg_color
    if color:
        result += color
    
    result += text + Colors.RESET
    
    return result


def print_success(message):
    """Imprime mensaje de éxito en verde"""
    print(colorize(f"✓ {message}", Colors.BRIGHT_GREEN, Colors.BOLD))


def print_error(message):
    """Imprime mensaje de error en rojo"""
    print(colorize(f"✗ {message}", Colors.BRIGHT_RED, Colors.BOLD))


def print_warning(message):
    """Imprime mensaje de advertencia en amarillo"""
    print(colorize(f"⚠ {message}", Colors.BRIGHT_YELLOW, Colors.BOLD))


def print_info(message):
    """Imprime mensaje informativo en azul"""
    print(colorize(f"ℹ {message}", Colors.BRIGHT_BLUE))


def print_header(message):
    """Imprime encabezado destacado"""
    print(colorize(f"\n{'='*60}", Colors.CYAN))
    print(colorize(f"  {message}", Colors.CYAN, Colors.BOLD))
    print(colorize(f"{'='*60}\n", Colors.CYAN))