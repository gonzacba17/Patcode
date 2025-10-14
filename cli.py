"""
PatCode - CLI con Click
Interfaz moderna con comandos estructurados
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from agents.pat_agent import PatAgent
from config import settings
from exceptions import PatCodeError, OllamaConnectionError

console = Console()


@click.group()
@click.version_option(version="0.3.0", prog_name="PatCode")
def cli():
    """🤖 PatCode - Asistente de programación local con IA"""
    pass


@cli.command()
@click.option('--fast', is_flag=True, help='Modo rápido (modelo ligero)')
@click.option('--deep', is_flag=True, help='Modo profundo (modelo completo)')
@click.option('--model', type=str, help='Modelo específico a usar')
def chat(fast, deep, model):
    """Inicia conversación interactiva con Pat"""
    
    if model:
        settings.ollama.model = model
    elif fast:
        settings.ollama.model = "llama3.2:1b"
    elif deep:
        settings.ollama.model = "codellama:13b"
    
    console.print(f"[dim]Usando modelo: {settings.ollama.model}[/dim]\n")
    
    try:
        with console.status("[bold yellow]Inicializando...[/bold yellow]"):
            agent = PatAgent()
        
        welcome = f"""
[bold cyan]🤖 PatCode v0.3.0[/bold cyan]

[bold]Comandos rápidos:[/bold]
  /help     - Ver ayuda completa
  /clear    - Limpiar historial
  /stats    - Ver estadísticas
  /quit     - Salir

[dim]Escribe tu pregunta o usa /help[/dim]
        """
        console.print(Panel(welcome, border_style="cyan"))
        
        while True:
            try:
                prompt_text = Prompt.ask("\n[bold green]Tú[/bold green]")
                
                if prompt_text.startswith('/'):
                    if prompt_text in ['/quit', '/exit']:
                        break
                    elif prompt_text == '/help':
                        from main import print_welcome
                        print_welcome()
                        continue
                    elif prompt_text == '/clear':
                        agent.clear_history()
                        console.print("[green]✓ Historial limpiado[/green]")
                        continue
                    elif prompt_text == '/stats':
                        stats = agent.get_stats()
                        table = Table(title="📊 Estadísticas")
                        table.add_column("Métrica", style="cyan")
                        table.add_column("Valor", style="green")
                        table.add_row("Mensajes activos", str(stats.get('active_messages', 0)))
                        table.add_row("Total mensajes", str(stats['total_messages']))
                        table.add_row("Archivos", str(stats['loaded_files']))
                        console.print(table)
                        continue
                
                with console.status("[bold yellow]🤔 Pensando...[/bold yellow]"):
                    answer = agent.ask(prompt_text)
                
                console.print(f"\n[bold cyan]Pat:[/bold cyan]")
                console.print(Markdown(answer))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Saliendo...[/yellow]")
                break
            except PatCodeError as e:
                console.print(f"[red]Error: {e}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error fatal: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--deep', is_flag=True, help='Análisis profundo con IA')
@click.option('--format', type=click.Choice(['table', 'json', 'markdown']), default='table')
def analyze(path, deep, format):
    """Analiza estructura y calidad de código del proyecto"""
    
    console.print(f"[yellow]🔍 Analizando proyecto en: {path}[/yellow]\n")
    
    try:
        from tools.project_analyzer import ProjectAnalyzer
        
        with console.status("[bold yellow]Escaneando y analizando...[/bold yellow]"):
            analyzer = ProjectAnalyzer()
            report = analyzer.analyze_project(path)
        
        if format == 'markdown':
            console.print(Markdown(analyzer.format_report(report)))
        
        elif format == 'json':
            import json
            data = {
                'path': str(report.path),
                'total_files': report.total_files,
                'total_lines': report.total_lines,
                'languages': report.languages,
                'structure_score': report.structure_score,
                'quality_score': report.quality_score,
                'test_coverage': report.test_coverage,
                'suggestions': report.suggestions
            }
            console.print_json(data=data)
        
        else:
            table = Table(title=f"📊 Análisis de {Path(path).name}")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            
            table.add_row("Archivos", str(report.total_files))
            table.add_row("Líneas de código", f"{report.total_lines:,}")
            table.add_row("Tamaño total", f"{report.total_size_bytes/1024:.1f} KB")
            
            console.print(table)
            
            lang_table = Table(title="📚 Lenguajes")
            lang_table.add_column("Lenguaje", style="cyan")
            lang_table.add_column("Archivos", justify="right", style="green")
            
            for lang, count in sorted(report.languages.items(), key=lambda x: x[1], reverse=True):
                lang_table.add_row(lang, str(count))
            
            console.print("\n")
            console.print(lang_table)
            
            score_table = Table(title="⭐ Scores de Calidad")
            score_table.add_column("Categoría", style="cyan")
            score_table.add_column("Score", justify="right", style="green")
            
            score_table.add_row("Estructura", f"{report.structure_score:.1f}/10")
            score_table.add_row("Calidad", f"{report.quality_score:.1f}/10")
            if report.test_coverage:
                score_table.add_row("Cobertura Tests", f"{report.test_coverage:.1f}%")
            
            console.print("\n")
            console.print(score_table)
            
            if report.suggestions:
                console.print("\n[bold cyan]💡 Sugerencias de Mejora:[/bold cyan]")
                for i, suggestion in enumerate(report.suggestions, 1):
                    console.print(f"  {i}. {suggestion}")
        
        if deep:
            console.print("\n[yellow]Análisis profundo con IA...[/yellow]")
            with console.status("[bold yellow]Analizando con IA...[/bold yellow]"):
                agent = PatAgent()
                agent.file_manager.load_project_files(path, max_files=10)
                analysis = agent.ask(
                    f"Basado en el análisis: estructura {report.structure_score}/10, "
                    f"calidad {report.quality_score}/10. "
                    "Dame 3-5 recomendaciones específicas para mejorar este proyecto."
                )
            console.print("\n[bold cyan]Análisis IA:[/bold cyan]")
            console.print(Markdown(analysis))
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--model', type=str, help='Modelo a usar')
def explain(file_path, model):
    """Explica qué hace un archivo de código"""
    
    if model:
        settings.ollama.model = model
    
    try:
        with console.status(f"[yellow]Analizando {file_path}...[/yellow]"):
            agent = PatAgent()
            agent.file_manager.load_file(file_path)
            explanation = agent.ask(f"Explica qué hace el archivo {file_path} de forma clara y concisa")
        
        console.print(f"\n[bold cyan]Explicación de {Path(file_path).name}:[/bold cyan]\n")
        console.print(Markdown(explanation))
    
    except FileNotFoundError:
        console.print(f"[red]Archivo no encontrado: {file_path}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def refactor(file_path):
    """Sugiere mejoras para un archivo"""
    
    try:
        with console.status(f"[yellow]Analizando {file_path}...[/yellow]"):
            agent = PatAgent()
            agent.file_manager.load_file(file_path)
            suggestions = agent.ask(
                f"Analiza {file_path} y sugiere 3-5 mejoras de refactoring. "
                "Sé específico y práctico."
            )
        
        console.print(f"\n[bold cyan]Sugerencias para {Path(file_path).name}:[/bold cyan]\n")
        console.print(Markdown(suggestions))
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--framework', type=str, help='Framework de testing (pytest, unittest, jest)')
def test(file_path, framework):
    """Genera tests para un archivo"""
    
    framework = framework or 'pytest'
    
    try:
        with console.status(f"[yellow]Generando tests...[/yellow]"):
            agent = PatAgent()
            agent.file_manager.load_file(file_path)
            tests = agent.ask(
                f"Genera tests con {framework} para {file_path}. "
                f"Incluye casos comunes y edge cases. Solo código, sin explicaciones."
            )
        
        console.print(f"\n[bold cyan]Tests para {Path(file_path).name}:[/bold cyan]\n")
        
        from rich.syntax import Syntax
        syntax = Syntax(tests, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
        
        save = Prompt.ask("\n¿Guardar en archivo?", choices=["s", "n"], default="n")
        if save == "s":
            test_file = Path(file_path).parent / f"test_{Path(file_path).name}"
            test_file.write_text(tests)
            console.print(f"[green]✓ Guardado en {test_file}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def info():
    """Muestra información del sistema"""
    
    table = Table(title="ℹ️ Información de PatCode")
    table.add_column("Configuración", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Modelo", settings.ollama.model)
    table.add_row("Ollama URL", settings.ollama.base_url)
    table.add_row("Timeout", f"{settings.ollama.timeout}s")
    table.add_row("Memoria máxima", f"{settings.memory.max_size} mensajes")
    table.add_row("Contexto activo", f"{settings.memory.max_active_messages} mensajes")
    table.add_row("Archivado", str(settings.memory.archive_directory))
    
    console.print(table)
    
    try:
        import requests
        response = requests.get(f"{settings.ollama.base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            console.print("\n[green]✓ Ollama está corriendo[/green]")
        else:
            console.print("\n[yellow]⚠ Ollama responde pero con errores[/yellow]")
    except:
        console.print("\n[red]✗ Ollama no está disponible[/red]")
        console.print("[dim]Ejecuta: ollama serve[/dim]")


if __name__ == '__main__':
    cli()
