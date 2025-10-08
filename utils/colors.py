"""
utils/colors.py
Utilidades para colorear texto en terminal
"""

import sys


class Colors:
    """Códigos ANSI para colores en terminal"""
    
    # Colores básicos
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Colores de texto
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
    
    # Colores de fondo
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    @staticmethod
    def is_supported() -> bool:
        """Verifica si la terminal soporta colores"""
        # En Windows, verificar si se habilitó el soporte ANSI
        if sys.platform == "win32":
            try:
                import os
                # Intentar habilitar colores en Windows
                os.system('')
                return True
            except:
                return False
        return True


def colorize(text: str, color: str = Colors.RESET, bold: bool = False) -> str:
    """
    Colorea un texto
    
    Args:
        text: Texto a colorear
        color: Color a aplicar (usar Colors.*)
        bold: Si debe estar en negrita
        
    Returns:
        Texto coloreado con códigos ANSI
    """
    if not Colors.is_supported():
        return text
    
    result = ""
    if bold:
        result += Colors.BOLD
    result += color + text + Colors.RESET
    return result


def print_colored(text: str, color: str = Colors.RESET, bold: bool = False, end: str = '\n'):
    """
    Imprime texto coloreado
    
    Args:
        text: Texto a imprimir
        color: Color a aplicar
        bold: Si debe estar en negrita
        end: Carácter de fin de línea
    """
    print(colorize(text, color, bold), end=end)


# Funciones de conveniencia
def print_success(text: str):
    """Imprime texto de éxito en verde"""
    print_colored(f"✅ {text}", Colors.GREEN)


def print_error(text: str):
    """Imprime texto de error en rojo"""
    print_colored(f"❌ {text}", Colors.RED, bold=True)


def print_warning(text: str):
    """Imprime advertencia en amarillo"""
    print_colored(f"⚠️  {text}", Colors.YELLOW)


def print_info(text: str):
    """Imprime información en cyan"""
    print_colored(f"ℹ️  {text}", Colors.CYAN)


# Habilitar colores en Windows
if sys.platform == "win32":
    try:
        import os
        os.system('')  # Habilita secuencias ANSI en Windows 10+
    except:
        pass