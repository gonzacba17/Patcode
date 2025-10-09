"""
Utilidades para formatear salidas y texto
"""

import os
from typing import List, Tuple


def format_code(code: str, language: str = "python", show_line_numbers: bool = True) -> str:
    """
    Formatea código con resaltado de sintaxis opcional
    
    Args:
        code: Código a formatear
        language: Lenguaje del código
        show_line_numbers: Si mostrar números de línea
        
    Returns:
        Código formateado
    """
    if not code:
        return ""
    
    lines = code.split('\n')
    
    if show_line_numbers:
        max_width = len(str(len(lines)))
        formatted_lines = []
        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(max_width)
            formatted_lines.append(f"{line_num} | {line}")
        return '\n'.join(formatted_lines)
    
    return code


def format_file_path(filepath: str, max_length: int = 50) -> str:
    """
    Formatea una ruta de archivo para visualización
    
    Args:
        filepath: Ruta del archivo
        max_length: Longitud máxima
        
    Returns:
        Ruta formateada
    """
    if len(filepath) <= max_length:
        return filepath
    
    # Acortar la ruta manteniendo el inicio y el final
    parts = filepath.split(os.sep)
    if len(parts) <= 2:
        return filepath
    
    filename = parts[-1]
    remaining = max_length - len(filename) - 5  # 5 para ".../"
    
    start = ""
    for part in parts[:-1]:
        if len(start) + len(part) + 1 < remaining:
            start += part + os.sep
        else:
            break
    
    return f"{start}...{os.sep}{filename}"


def format_error(error_message: str, error_type: str = "ERROR") -> str:
    """
    Formatea un mensaje de error
    
    Args:
        error_message: Mensaje de error
        error_type: Tipo de error
        
    Returns:
        Error formateado
    """
    lines = error_message.strip().split('\n')
    formatted = f"❌ {error_type}: {lines[0]}\n"
    
    if len(lines) > 1:
        for line in lines[1:]:
            formatted += f"   {line}\n"
    
    return formatted.rstrip()


def format_table(headers: List[str], rows: List[List[str]], 
                 max_col_width: int = 30) -> str:
    """
    Formatea datos en una tabla
    
    Args:
        headers: Encabezados de columnas
        rows: Filas de datos
        max_col_width: Ancho máximo de columna
        
    Returns:
        Tabla formateada
    """
    if not headers:
        return ""
    
    # Calcular anchos de columna
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(min(max_width, max_col_width))
    
    # Crear línea separadora
    separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    
    # Formatear encabezados
    header_line = "|"
    for header, width in zip(headers, col_widths):
        header_line += f" {header:<{width}} |"
    
    # Formatear filas
    table = separator + "\n"
    table += header_line + "\n"
    table += separator + "\n"
    
    for row in rows:
        row_line = "|"
        for i, width in enumerate(col_widths):
            cell = str(row[i]) if i < len(row) else ""
            if len(cell) > width:
                cell = cell[:width-3] + "..."
            row_line += f" {cell:<{width}} |"
        table += row_line + "\n"
    
    table += separator
    return table


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto si excede la longitud máxima
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo para indicar truncamiento
        
    Returns:
        Texto truncado
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_response(response: str, wrap_width: int = 80) -> str:
    """
    Formatea una respuesta de texto
    
    Args:
        response: Respuesta a formatear
        wrap_width: Ancho de línea para ajuste
        
    Returns:
        Respuesta formateada
    """
    # Detectar bloques de código
    if "```" in response:
        return format_response_with_code(response)
    
    return response


def format_response_with_code(response: str) -> str:
    """
    Formatea una respuesta que contiene bloques de código
    
    Args:
        response: Respuesta con código
        
    Returns:
        Respuesta formateada con código resaltado
    """
    parts = response.split("```")
    formatted = []
    
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Texto normal
            formatted.append(part)
        else:
            # Bloque de código
            lines = part.split('\n')
            language = lines[0].strip() if lines else ""
            code = '\n'.join(lines[1:]) if len(lines) > 1 else part
            
            formatted.append(f"\n{'─' * 60}")
            if language:
                formatted.append(f"[{language}]")
            formatted.append(format_code(code, language))
            formatted.append(f"{'─' * 60}\n")
    
    return ''.join(formatted)


def format_list(items: List[str], style: str = "bullet") -> str:
    """
    Formatea una lista de items
    
    Args:
        items: Items a formatear
        style: Estilo ('bullet', 'numbered', 'checkbox')
        
    Returns:
        Lista formateada
    """
    if not items:
        return ""
    
    formatted = []
    for i, item in enumerate(items, 1):
        if style == "bullet":
            formatted.append(f"• {item}")
        elif style == "numbered":
            formatted.append(f"{i}. {item}")
        elif style == "checkbox":
            formatted.append(f"☐ {item}")
        else:
            formatted.append(item)
    
    return '\n'.join(formatted)


def format_json(data: dict, indent: int = 2) -> str:
    """
    Formatea un diccionario como JSON legible
    
    Args:
        data: Datos a formatear
        indent: Espacios de indentación
        
    Returns:
        JSON formateado
    """
    import json
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_size(size_bytes: int) -> str:
    """
    Formatea un tamaño en bytes a formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        Tamaño formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


__all__ = [
    'format_code',
    'format_file_path',
    'format_error',
    'format_table',
    'truncate_text',
    'format_response',
    'format_response_with_code',
    'format_list',
    'format_json',
    'format_size',
]