"""
Visualizador de diferencias entre archivos y código
"""

import difflib
from .colors import Colors, colorize
from .formatters import format_diff_line


def show_diff(old_content, new_content, old_label="Original", new_label="Modificado"):
    """
    Muestra las diferencias entre dos contenidos
    
    Args:
        old_content (str): Contenido original
        new_content (str): Contenido nuevo
        old_label (str): Etiqueta para el contenido original
        new_label (str): Etiqueta para el contenido nuevo
    
    Returns:
        str: Diff formateado
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_label,
        tofile=new_label,
        lineterm=''
    )
    
    formatted_diff = []
    
    # Encabezado
    header = colorize("╔" + "═" * 78 + "╗", Colors.CYAN, Colors.BOLD)
    formatted_diff.append(header)
    formatted_diff.append(colorize(f"║ DIFF: {old_label} → {new_label}".ljust(79) + "║", 
                                   Colors.CYAN, Colors.BOLD))
    formatted_diff.append(colorize("╠" + "═" * 78 + "╣", Colors.CYAN, Colors.BOLD))
    
    # Procesar diff
    for line in diff:
        line = line.rstrip()
        
        if line.startswith('---') or line.startswith('+++'):
            formatted_diff.append(colorize(f"║ {line.ljust(77)}║", Colors.YELLOW, Colors.BOLD))
        elif line.startswith('@@'):
            formatted_diff.append(colorize(f"║ {line.ljust(77)}║", Colors.CYAN))
        elif line.startswith('+'):
            formatted_diff.append(colorize(f"║ {line.ljust(77)}║", Colors.GREEN))
        elif line.startswith('-'):
            formatted_diff.append(colorize(f"║ {line.ljust(77)}║", Colors.RED))
        else:
            formatted_diff.append(colorize(f"║ {line.ljust(77)}║", Colors.WHITE))
    
    # Pie
    footer = colorize("╚" + "═" * 78 + "╝", Colors.CYAN, Colors.BOLD)
    formatted_diff.append(footer)
    
    return '\n'.join(formatted_diff)


def show_side_by_side_diff(old_content, new_content, old_label="Original", 
                           new_label="Modificado", width=40):
    """
    Muestra diferencias lado a lado
    
    Args:
        old_content (str): Contenido original
        new_content (str): Contenido nuevo
        old_label (str): Etiqueta para el contenido original
        new_label (str): Etiqueta para el contenido nuevo
        width (int): Ancho de cada columna
    
    Returns:
        str: Diff formateado lado a lado
    """
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    max_lines = max(len(old_lines), len(new_lines))
    
    # Pad con líneas vacías
    old_lines += [''] * (max_lines - len(old_lines))
    new_lines += [''] * (max_lines - len(new_lines))
    
    formatted = []
    
    # Encabezado
    header = colorize(old_label.center(width), Colors.YELLOW, Colors.BOLD) + " │ " + \
             colorize(new_label.center(width), Colors.GREEN, Colors.BOLD)
    formatted.append(header)
    formatted.append("─" * width + "─┼─" + "─" * width)
    
    # Líneas
    for old_line, new_line in zip(old_lines, new_lines):
        old_display = old_line[:width].ljust(width)
        new_display = new_line[:width].ljust(width)
        
        if old_line != new_line:
            if old_line:
                old_display = colorize(old_display, Colors.RED)
            if new_line:
                new_display = colorize(new_display, Colors.GREEN)
        else:
            old_display = colorize(old_display, Colors.DIM)
            new_display = colorize(new_display, Colors.DIM)
        
        formatted.append(f"{old_display} │ {new_display}")
    
    return '\n'.join(formatted)


def compute_diff_stats(old_content, new_content):
    """
    Calcula estadísticas de las diferencias
    
    Args:
        old_content (str): Contenido original
        new_content (str): Contenido nuevo
    
    Returns:
        dict: Estadísticas (lines_added, lines_removed, lines_changed)
    """
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
    
    added = 0
    removed = 0
    
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            added += 1
        elif line.startswith('-') and not line.startswith('---'):
            removed += 1
    
    return {
        'lines_added': added,
        'lines_removed': removed,
        'lines_changed': added + removed,
        'old_lines': len(old_lines),
        'new_lines': len(new_lines)
    }


def show_diff_stats(stats):
    """
    Muestra estadísticas de diferencias de forma visual
    
    Args:
        stats (dict): Diccionario con estadísticas
    
    Returns:
        str: Estadísticas formateadas
    """
    lines = []
    
    lines.append(colorize("📊 Estadísticas de cambios:", Colors.CYAN, Colors.BOLD))
    lines.append("")
    
    added = stats.get('lines_added', 0)
    removed = stats.get('lines_removed', 0)
    
    lines.append(colorize(f"  + {added} líneas agregadas", Colors.GREEN))
    lines.append(colorize(f"  - {removed} líneas eliminadas", Colors.RED))
    lines.append(colorize(f"  ~ {added + removed} líneas modificadas", Colors.YELLOW))
    lines.append("")
    
    old_lines = stats.get('old_lines', 0)
    new_lines = stats.get('new_lines', 0)
    
    lines.append(colorize(f"  Original: {old_lines} líneas", Colors.DIM))
    lines.append(colorize(f"  Nuevo: {new_lines} líneas", Colors.DIM))
    
    return '\n'.join(lines)


def highlight_changes(old_text, new_text):
    """
    Resalta cambios a nivel de caracteres en dos textos
    
    Args:
        old_text (str): Texto original
        new_text (str): Texto nuevo
    
    Returns:
        tuple: (old_highlighted, new_highlighted)
    """
    import difflib
    
    s = difflib.SequenceMatcher(None, old_text, new_text)
    
    old_highlighted = []
    new_highlighted = []
    
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            old_highlighted.append(old_text[i1:i2])
            new_highlighted.append(new_text[j1:j2])
        elif tag == 'delete':
            old_highlighted.append(colorize(old_text[i1:i2], Colors.RED, Colors.REVERSE))
        elif tag == 'insert':
            new_highlighted.append(colorize(new_text[j1:j2], Colors.GREEN, Colors.REVERSE))
        elif tag == 'replace':
            old_highlighted.append(colorize(old_text[i1:i2], Colors.RED, Colors.REVERSE))
            new_highlighted.append(colorize(new_text[j1:j2], Colors.GREEN, Colors.REVERSE))
    
    return ''.join(old_highlighted), ''.join(new_highlighted)


def generate_patch(old_content, new_content, filename="file"):
    """
    Genera un parche en formato unified diff
    
    Args:
        old_content (str): Contenido original
        new_content (str): Contenido nuevo
        filename (str): Nombre del archivo
    
    Returns:
        str: Parche en formato diff
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm='\n'
    )
    
    return ''.join(diff)


def apply_suggestions(original_code, suggestions):
    """
    Aplica sugerencias de cambio al código
    
    Args:
        original_code (str): Código original
        suggestions (list): Lista de sugerencias con formato:
            [{'line': int, 'old': str, 'new': str}, ...]
    
    Returns:
        str: Código modificado
    """
    lines = original_code.splitlines()
    
    # Ordenar sugerencias por número de línea (descendente para no afectar índices)
    suggestions = sorted(suggestions, key=lambda x: x.get('line', 0), reverse=True)
    
    for suggestion in suggestions:
        line_num = suggestion.get('line', 0) - 1  # Convertir a índice base 0
        old_text = suggestion.get('old', '')
        new_text = suggestion.get('new', '')
        
        if 0 <= line_num < len(lines):
            if old_text in lines[line_num]:
                lines[line_num] = lines[line_num].replace(old_text, new_text)
    
    return '\n'.join(lines)


def get_context_around_change(content, line_number, context_lines=3):
    """
    Obtiene el contexto alrededor de una línea cambiada
    
    Args:
        content (str): Contenido del archivo
        line_number (int): Número de línea (base 1)
        context_lines (int): Cantidad de líneas de contexto
    
    Returns:
        str: Contexto formateado
    """
    lines = content.splitlines()
    total_lines = len(lines)
    
    start = max(0, line_number - context_lines - 1)
    end = min(total_lines, line_number + context_lines)
    
    context = []
    
    for i in range(start, end):
        line_num = i + 1
        prefix = ">>> " if line_num == line_number else "    "
        
        if line_num == line_number:
            line_text = colorize(f"{prefix}{line_num:4d} | {lines[i]}", 
                               Colors.YELLOW, Colors.BOLD)
        else:
            line_text = colorize(f"{prefix}{line_num:4d} | {lines[i]}", Colors.DIM)
        
        context.append(line_text)
    
    return '\n'.join(context)


def compare_files(file1_path, file2_path):
    """
    Compara dos archivos y muestra las diferencias
    
    Args:
        file1_path (str): Ruta del primer archivo
        file2_path (str): Ruta del segundo archivo
    
    Returns:
        str: Diferencias formateadas
    """
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1:
            content1 = f1.read()
        
        with open(file2_path, 'r', encoding='utf-8') as f2:
            content2 = f2.read()
        
        return show_diff(content1, content2, file1_path, file2_path)
    
    except FileNotFoundError as e:
        return colorize(f"Error: Archivo no encontrado - {e}", Colors.RED, Colors.BOLD)
    except Exception as e:
        return colorize(f"Error al comparar archivos: {e}", Colors.RED, Colors.BOLD)