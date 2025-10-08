"""
Formateadores para código y respuestas
"""

import re
from .colors import Colors, colorize


def format_code(code, language="python"):
    """
    Formatea código con resaltado básico
    
    Args:
        code (str): Código a formatear
        language (str): Lenguaje de programación
    
    Returns:
        str: Código formateado
    """
    lines = code.split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines, 1):
        line_num = colorize(f"{i:3d} │ ", Colors.DIM)
        formatted_lines.append(line_num + line)
    
    return '\n'.join(formatted_lines)


def format_response(response, max_width=80):
    """
    Formatea la respuesta del asistente
    
    Args:
        response (str): Respuesta a formatear
        max_width (int): Ancho máximo de línea
    
    Returns:
        str: Respuesta formateada
    """
    # Detectar bloques de código
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', response, re.DOTALL)
    
    formatted = response
    
    for lang, code in code_blocks:
        formatted_code = format_code(code.strip(), lang or "python")
        code_block = f"```{lang or ''}\n{code}```"
        replacement = f"\n{colorize('┌' + '─' * 78 + '┐', Colors.CYAN)}\n"
        replacement += formatted_code
        replacement += f"\n{colorize('└' + '─' * 78 + '┘', Colors.CYAN)}\n"
        formatted = formatted.replace(code_block, replacement)
    
    return formatted


def format_error(error_message):
    """
    Formatea mensajes de error
    
    Args:
        error_message (str): Mensaje de error
    
    Returns:
        str: Error formateado
    """
    border = colorize("╔" + "═" * 78 + "╗", Colors.RED, Colors.BOLD)
    footer = colorize("╚" + "═" * 78 + "╝", Colors.RED, Colors.BOLD)
    
    lines = error_message.split('\n')
    formatted_lines = [border]
    
    for line in lines:
        formatted_line = colorize(f"║ {line.ljust(77)}║", Colors.RED)
        formatted_lines.append(formatted_line)
    
    formatted_lines.append(footer)
    
    return '\n'.join(formatted_lines)


def format_diff_line(line, line_type):
    """
    Formatea una línea de diff
    
    Args:
        line (str): Línea a formatear
        line_type (str): Tipo de línea ('+', '-', ' ')
    
    Returns:
        str: Línea formateada
    """
    if line_type == '+':
        return colorize(f"+ {line}", Colors.GREEN)
    elif line_type == '-':
        return colorize(f"- {line}", Colors.RED)
    else:
        return colorize(f"  {line}", Colors.DIM)


def format_file_tree(tree_dict, prefix="", is_last=True):
    """
    Formatea un árbol de archivos
    
    Args:
        tree_dict (dict): Diccionario con estructura de archivos
        prefix (str): Prefijo para la indentación
        is_last (bool): Si es el último elemento
    
    Returns:
        str: Árbol formateado
    """
    lines = []
    items = list(tree_dict.items())
    
    for i, (name, content) in enumerate(items):
        is_last_item = (i == len(items) - 1)
        connector = "└── " if is_last_item else "├── "
        
        if isinstance(content, dict):
            # Es un directorio
            folder_line = colorize(f"{prefix}{connector}📁 {name}/", Colors.BLUE, Colors.BOLD)
            lines.append(folder_line)
            
            extension = "    " if is_last_item else "│   "
            subtree = format_file_tree(content, prefix + extension, is_last_item)
            lines.append(subtree)
        else:
            # Es un archivo
            file_line = colorize(f"{prefix}{connector}📄 {name}", Colors.WHITE)
            lines.append(file_line)
    
    return '\n'.join(lines)


def format_table(headers, rows):
    """
    Formatea datos en tabla
    
    Args:
        headers (list): Lista de encabezados
        rows (list): Lista de filas
    
    Returns:
        str: Tabla formateada
    """
    # Calcular anchos de columna
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Crear separador
    separator = "┼".join("─" * (w + 2) for w in col_widths)
    top_border = "┌" + separator.replace("┼", "┬") + "┐"
    mid_border = "├" + separator + "┤"
    bottom_border = "└" + separator.replace("┼", "┴") + "┘"
    
    # Formatear encabezados
    header_line = "│"
    for i, h in enumerate(headers):
        header_line += f" {h.ljust(col_widths[i])} │"
    
    # Formatear filas
    formatted_rows = []
    for row in rows:
        row_line = "│"
        for i, cell in enumerate(row):
            row_line += f" {str(cell).ljust(col_widths[i])} │"
        formatted_rows.append(row_line)
    
    # Combinar todo
    table = [
        colorize(top_border, Colors.CYAN),
        colorize(header_line, Colors.CYAN, Colors.BOLD),
        colorize(mid_border, Colors.CYAN)
    ]
    
    for row_line in formatted_rows:
        table.append(colorize(row_line, Colors.WHITE))
    
    table.append(colorize(bottom_border, Colors.CYAN))
    
    return '\n'.join(table)


def truncate_text(text, max_length=100, suffix="..."):
    """
    Trunca texto si es muy largo
    
    Args:
        text (str): Texto a truncar
        max_length (int): Longitud máxima
        suffix (str): Sufijo para indicar truncamiento
    
    Returns:
        str: Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix