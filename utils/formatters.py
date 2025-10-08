"""
utils/formatters.py
Utilidades para formatear texto y rutas
"""

import os
from pathlib import Path
from typing import Optional


def format_file_path(file_path: str, base_path: Optional[str] = None, max_length: int = 50) -> str:
    """
    Formatea una ruta de archivo para mostrarla de forma legible
    
    Args:
        file_path: Ruta del archivo
        base_path: Ruta base para hacer paths relativos
        max_length: Longitud máxima del path (None para sin límite)
        
    Returns:
        Ruta formateada
    """
    path = Path(file_path)
    
    # Convertir a ruta relativa si se proporciona base_path
    if base_path:
        try:
            base = Path(base_path)
            path = path.relative_to(base)
        except ValueError:
            pass  # No se puede hacer relativo, usar path absoluto
    
    # Convertir a string
    path_str = str(path)
    
    # Normalizar separadores para el OS actual
    path_str = path_str.replace('/', os.sep).replace('\\', os.sep)
    
    # Acortar si excede max_length
    if max_length and len(path_str) > max_length:
        # Mantener inicio y fin
        half = (max_length - 3) // 2
        path_str = path_str[:half] + "..." + path_str[-half:]
    
    return path_str


def format_file_size(size_bytes: int) -> str:
    """
    Formatea un tamaño de archivo en bytes a formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        String formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Formatea una duración en segundos a formato legible
    
    Args:
        seconds: Duración en segundos
        
    Returns:
        String formateado (ej: "1m 30s")
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto largo
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_code_block(code: str, language: str = "") -> str:
    """
    Formatea un bloque de código con delimitadores
    
    Args:
        code: Código a formatear
        language: Lenguaje del código
        
    Returns:
        Código formateado
    """
    return f"```{language}\n{code}\n```"


def format_list(items: list, bullet: str = "•") -> str:
    """
    Formatea una lista con bullets
    
    Args:
        items: Lista de items
        bullet: Carácter de bullet
        
    Returns:
        Lista formateada
    """
    return "\n".join(f"{bullet} {item}" for item in items)


def indent_text(text: str, spaces: int = 2) -> str:
    """
    Indenta cada línea de un texto
    
    Args:
        text: Texto a indentar
        spaces: Número de espacios
        
    Returns:
        Texto indentado
    """
    indent = " " * spaces
    return "\n".join(indent + line for line in text.split("\n"))


def format_code(code: str, language: str = "python") -> str:
    """
    Formatea código con resaltado básico
    
    Args:
        code: Código a formatear
        language: Lenguaje del código
        
    Returns:
        Código formateado
    """
    # Por ahora, solo agregar bloques de código markdown
    return f"```{language}\n{code}\n```"


def format_json(data: dict, indent: int = 2) -> str:
    """
    Formatea un diccionario como JSON
    
    Args:
        data: Diccionario a formatear
        indent: Espacios de indentación
        
    Returns:
        JSON formateado
    """
    import json
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_table(headers: list, rows: list) -> str:
    """
    Formatea datos en tabla ASCII
    
    Args:
        headers: Lista de encabezados
        rows: Lista de listas con datos
        
    Returns:
        Tabla formateada
    """
    if not headers or not rows:
        return ""
    
    # Calcular anchos de columnas
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Crear separador
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    
    # Crear encabezado
    header_row = "|" + "|".join(f" {str(h):{w}} " for h, w in zip(headers, col_widths)) + "|"
    
    # Crear filas
    data_rows = []
    for row in rows:
        data_row = "|" + "|".join(f" {str(cell):{w}} " for cell, w in zip(row, col_widths)) + "|"
        data_rows.append(data_row)
    
    # Unir todo
    result = [separator, header_row, separator]
    result.extend(data_rows)
    result.append(separator)
    
    return "\n".join(result)