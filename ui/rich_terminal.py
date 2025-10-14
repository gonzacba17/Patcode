"""
Interfaz de terminal avanzada con Rich y prompt-toolkit
Proporciona experiencia visual moderna para PatCode
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Confirm, Prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from pathlib import Path
from typing import List, Dict, Any, Optional
import time


class RichTerminalUI:
    """Interfaz de terminal avanzada con Rich"""
    
    def __init__(self):
        self.console = Console()
        self.session = PromptSession(
            history=FileHistory('.patcode_history')
        )
        
        self.commands = WordCompleter([
            'analyze', 'explain', 'refactor', 'test', 'info',
            '/load', '/files', '/unload', '/show', '/project',
            '/analyze', '/clear', '/stats', '/help', '/quit',
            'exit', 'help', 'clear', 'context'
        ], ignore_case=True)
    
    def print_welcome(self, version: str = "0.3.1"):
        """Mensaje de bienvenida con estilo"""
        welcome_panel = Panel(
            f"[bold cyan]PatCode v{version}[/bold cyan]\n"
            "[white]Asistente de programación local con IA[/white]\n\n"
            "[dim]Comandos:[/dim] [green]analyze[/green], [green]explain[/green], "
            "[green]refactor[/green], [green]test[/green]\n"
            "[dim]Ayuda:[/dim] [yellow]/help[/yellow] o [yellow]help[/yellow]",
            title="🤖 Bienvenido",
            border_style="cyan"
        )
        self.console.print(welcome_panel)
        self.console.print()
    
    def prompt_user(self, prompt_text: str = "🤖 PatCode> ") -> str:
        """Prompt con autocompletado e historial"""
        try:
            user_input = self.session.prompt(
                prompt_text,
                completer=self.commands,
                enable_history_search=True,
                vi_mode=False
            )
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            return "/quit"
    
    def display_code(self, code: str, language: str = "python", 
                     title: Optional[str] = None, line_numbers: bool = True):
        """Muestra código con syntax highlighting"""
        syntax = Syntax(
            code, 
            language, 
            theme="monokai",
            line_numbers=line_numbers,
            word_wrap=False
        )
        
        if title:
            panel = Panel(syntax, title=f"📄 {title}", border_style="blue")
            self.console.print(panel)
        else:
            self.console.print(syntax)
    
    def display_markdown(self, text: str):
        """Renderiza markdown con estilo"""
        md = Markdown(text)
        self.console.print(md)
    
    def display_response(self, text: str, style: str = "assistant"):
        """Muestra respuesta del asistente con formato"""
        if style == "assistant":
            if "```" in text:
                self.display_markdown(text)
            else:
                self.console.print(f"[cyan]{text}[/cyan]")
        elif style == "error":
            self.display_error(text)
        elif style == "success":
            self.display_success(text)
        else:
            self.console.print(text)
    
    def display_error(self, message: str, title: str = "Error"):
        """Muestra error con estilo"""
        panel = Panel(
            f"[red]{message}[/red]",
            title=f"❌ {title}",
            border_style="red"
        )
        self.console.print(panel)
    
    def display_warning(self, message: str, title: str = "Advertencia"):
        """Muestra advertencia"""
        panel = Panel(
            f"[yellow]{message}[/yellow]",
            title=f"⚠️  {title}",
            border_style="yellow"
        )
        self.console.print(panel)
    
    def display_success(self, message: str, title: str = "Éxito"):
        """Muestra mensaje de éxito"""
        panel = Panel(
            f"[green]{message}[/green]",
            title=f"✅ {title}",
            border_style="green"
        )
        self.console.print(panel)
    
    def display_info(self, message: str, title: str = "Info"):
        """Muestra información"""
        panel = Panel(
            f"[blue]{message}[/blue]",
            title=f"ℹ️  {title}",
            border_style="blue"
        )
        self.console.print(panel)
    
    def display_analysis_report(self, report: Dict[str, Any]):
        """Renderiza reporte de análisis con tablas y barras"""
        
        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]Análisis de Proyecto[/bold cyan]\n"
            f"[dim]Ruta: {report.get('path', '.')}[/dim]",
            border_style="cyan"
        ))
        self.console.print()
        
        scores_table = Table(title="📊 Puntuaciones", show_header=True)
        scores_table.add_column("Categoría", style="cyan", width=20)
        scores_table.add_column("Score", justify="center", width=10)
        scores_table.add_column("Estado", justify="center", width=10)
        scores_table.add_column("Barra", width=30)
        
        scores = report.get('scores', {})
        for category, score in scores.items():
            status = self._get_status_emoji(score)
            bar = self._create_progress_bar(score, 10)
            scores_table.add_row(
                category.replace('_', ' ').title(),
                f"{score}/10",
                status,
                bar
            )
        
        self.console.print(scores_table)
        self.console.print()
        
        suggestions = report.get('suggestions', [])
        if suggestions:
            self.console.print(Panel(
                "\n".join([f"• {s}" for s in suggestions]),
                title="💡 Sugerencias",
                border_style="yellow"
            ))
            self.console.print()
    
    def display_file_tree(self, files: List[Path], title: str = "Archivos Cargados"):
        """Muestra árbol de archivos"""
        tree = Tree(f"📁 {title}")
        
        for file in files:
            if isinstance(file, Path):
                tree.add(f"📄 {file.name}")
            else:
                tree.add(f"📄 {str(file)}")
        
        self.console.print(tree)
    
    def display_stats(self, stats: Dict[str, Any]):
        """Muestra estadísticas con tabla"""
        table = Table(title="📈 Estadísticas", show_header=True)
        table.add_column("Métrica", style="cyan", width=30)
        table.add_column("Valor", style="green", justify="right", width=20)
        
        for key, value in stats.items():
            formatted_key = key.replace('_', ' ').title()
            
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            elif isinstance(value, int):
                formatted_value = f"{value:,}"
            else:
                formatted_value = str(value)
            
            table.add_row(formatted_key, formatted_value)
        
        self.console.print(table)
    
    def confirm_action(self, message: str) -> bool:
        """Confirmación para acciones destructivas"""
        return Confirm.ask(f"[yellow]{message}[/yellow]")
    
    def prompt_input(self, message: str, default: Optional[str] = None) -> str:
        """Prompt simple con valor por defecto"""
        return Prompt.ask(message, default=default)
    
    def progress_context(self, description: str = "Procesando..."):
        """Context manager para operaciones largas"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
    
    def show_loading(self, message: str = "Cargando..."):
        """Spinner simple para operaciones rápidas"""
        with self.console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
            time.sleep(0.5)
    
    def display_code_diff(self, old_code: str, new_code: str, 
                          language: str = "python"):
        """Muestra diff de código (simplificado)"""
        self.console.print("\n[bold yellow]Código Original:[/bold yellow]")
        self.display_code(old_code, language, line_numbers=True)
        
        self.console.print("\n[bold green]Código Sugerido:[/bold green]")
        self.display_code(new_code, language, line_numbers=True)
    
    def display_help(self, commands: Dict[str, str]):
        """Muestra ayuda con comandos disponibles"""
        table = Table(title="📚 Comandos Disponibles", show_header=True)
        table.add_column("Comando", style="cyan", width=25)
        table.add_column("Descripción", style="white", width=50)
        
        for cmd, description in commands.items():
            table.add_row(cmd, description)
        
        self.console.print(table)
    
    def clear_screen(self):
        """Limpia la pantalla"""
        self.console.clear()
    
    def display_model_info(self, model: str, speed: str, ram: str):
        """Muestra info del modelo seleccionado"""
        info = (
            f"[bold]Modelo:[/bold] {model}\n"
            f"[bold]Velocidad:[/bold] {speed}\n"
            f"[bold]RAM requerida:[/bold] {ram}"
        )
        
        panel = Panel(info, title="🤖 Configuración del Modelo", border_style="blue")
        self.console.print(panel)
    
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
    
    def _get_status_emoji(self, score: float) -> str:
        """Devuelve emoji según score"""
        if score >= 8:
            return "✅"
        elif score >= 6:
            return "⚠️"
        else:
            return "❌"
    
    def _create_progress_bar(self, value: float, max_value: float) -> str:
        """Crea barra de progreso visual"""
        percentage = (value / max_value) * 100
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        if percentage >= 80:
            color = "green"
        elif percentage >= 60:
            color = "yellow"
        else:
            color = "red"
        
        return f"[{color}]{bar}[/{color}]"
