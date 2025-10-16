"""
Formateador de salida para PatCode CLI.
Mejora legibilidad con colores, emojis y formato.
"""
from typing import List, Dict
import shutil
import textwrap
import logging

logger = logging.getLogger(__name__)

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

class OutputFormatter:
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
        self.terminal_width = shutil.get_terminal_size().columns
        logger.info(f"OutputFormatter inicializado (ancho: {self.terminal_width})")
    
    def format_response(self, text: str) -> str:
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(self._color(line, Colors.DIM))
                continue
            
            if in_code_block:
                formatted_lines.append(self._color(line, Colors.CYAN))
                continue
            
            if line.startswith('# '):
                formatted_lines.append(
                    self._color(line, Colors.BOLD + Colors.BRIGHT_CYAN)
                )
            elif line.startswith('## '):
                formatted_lines.append(
                    self._color(line, Colors.BOLD + Colors.BRIGHT_BLUE)
                )
            elif line.startswith('### '):
                formatted_lines.append(
                    self._color(line, Colors.BOLD + Colors.BLUE)
                )
            elif line.strip().startswith(('- ', '* ', '• ')):
                formatted_lines.append(
                    self._color(line, Colors.BRIGHT_WHITE)
                )
            elif '`' in line:
                formatted_lines.append(self._format_inline_code(line))
            elif any(emoji in line for emoji in ['✅', '❌', '⚠️', '📊', '🔍', '💡']):
                formatted_lines.append(self._color(line, Colors.BRIGHT_WHITE))
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        lines = []
        
        header_line = '│ ' + ' │ '.join(
            h.ljust(col_widths[i]) for i, h in enumerate(headers)
        ) + ' │'
        
        separator = '├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤'
        top_border = '┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐'
        bottom_border = '└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘'
        
        lines.append(self._color(top_border, Colors.BRIGHT_BLACK))
        lines.append(self._color(header_line, Colors.BOLD))
        lines.append(self._color(separator, Colors.BRIGHT_BLACK))
        
        for row in rows:
            row_line = '│ ' + ' │ '.join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            ) + ' │'
            lines.append(row_line)
        
        lines.append(self._color(bottom_border, Colors.BRIGHT_BLACK))
        
        return '\n'.join(lines)
    
    def format_code_block(self, code: str, language: str = "python") -> str:
        lines = code.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        width = min(max_width + 4, self.terminal_width - 4)
        
        output = []
        output.append(self._color(f"╭─ {language} " + '─' * (width - len(language) - 4) + '╮', Colors.BRIGHT_BLACK))
        
        for line in lines:
            padded_line = line.ljust(width - 2)
            output.append(self._color('│ ', Colors.BRIGHT_BLACK) + self._color(padded_line, Colors.CYAN) + self._color(' │', Colors.BRIGHT_BLACK))
        
        output.append(self._color('╰' + '─' * (width) + '╯', Colors.BRIGHT_BLACK))
        
        return '\n'.join(output)
    
    def format_info_box(self, title: str, content: str, box_type: str = "info") -> str:
        icons = {
            'info': '💡',
            'success': '✅',
            'warning': '⚠️ ',
            'error': '❌'
        }
        
        colors = {
            'info': Colors.BRIGHT_BLUE,
            'success': Colors.BRIGHT_GREEN,
            'warning': Colors.BRIGHT_YELLOW,
            'error': Colors.BRIGHT_RED
        }
        
        icon = icons.get(box_type, '•')
        color = colors.get(box_type, Colors.WHITE)
        
        max_width = self.terminal_width - 6
        wrapped_lines = []
        for line in content.split('\n'):
            wrapped_lines.extend(textwrap.wrap(line, max_width) or [''])
        
        width = max(len(line) for line in wrapped_lines + [title]) + 4
        
        output = []
        output.append(self._color(f"╭─ {icon} {title} " + '─' * (width - len(title) - 6) + '╮', color))
        
        for line in wrapped_lines:
            padded_line = line.ljust(width - 2)
            output.append(self._color('│ ', color) + padded_line + self._color(' │', color))
        
        output.append(self._color('╰' + '─' * (width) + '╯', color))
        
        return '\n'.join(output)
    
    def format_progress(self, current: int, total: int, label: str = "") -> str:
        bar_width = min(40, self.terminal_width - 20)
        filled = int(bar_width * current / total)
        bar = '█' * filled + '░' * (bar_width - filled)
        percentage = int(100 * current / total)
        
        return f"{label} [{bar}] {percentage}% ({current}/{total})"
    
    def _color(self, text: str, color: str) -> str:
        if not self.use_colors:
            return text
        return f"{color}{text}{Colors.RESET}"
    
    def _format_inline_code(self, line: str) -> str:
        import re
        
        def replace_code(match):
            code = match.group(1)
            return self._color(f"`{code}`", Colors.CYAN)
        
        return re.sub(r'`([^`]+)`', replace_code, line)
    
    def format_error(self, error_msg: str) -> str:
        return self.format_info_box("Error", error_msg, box_type="error")
    
    def format_success(self, success_msg: str) -> str:
        return self.format_info_box("Éxito", success_msg, box_type="success")
    
    def format_warning(self, warning_msg: str) -> str:
        return self.format_info_box("Advertencia", warning_msg, box_type="warning")


formatter = OutputFormatter()
