# ui/rich_terminal.py
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress
from rich.live import Live

class RichTerminalUI:
    """Interfaz de terminal mejorada con Rich"""
    
    def __init__(self):
        self.console = Console()
    
    def show_plan(self, steps: List[str]):
        """Muestra el plan de manera visual"""
        plan_text = "\n".join([f"[bold cyan]{i+1}.[/] {step}" 
                               for i, step in enumerate(steps)])
        
        self.console.print(Panel(
            plan_text,
            title="📋 Plan de Acción",
            border_style="cyan"
        ))
    
    def show_file_edit(self, file_path: str, diff: str):
        """Muestra un diff de cambios en archivo"""
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
        self.console.print(Panel(
            syntax,
            title=f"✏️ Editando: {file_path}",
            border_style="green"
        ))
    
    def show_command_execution(self, command: str, output: str):
        """Muestra ejecución de comando"""
        self.console.print(f"[bold yellow]$ {command}[/]")
        self.console.print(output)
    
    def ask_confirmation(self, action: str) -> bool:
        """Pide confirmación al usuario"""
        response = self.console.input(f"[yellow]⚠ {action}. ¿Continuar? (y/n): [/]")
        return response.lower() == 'y'