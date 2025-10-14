"""
PatCode - CLI con Click y RichTerminalUI
Interfaz moderna con comandos estructurados y visuales avanzados
"""

import click
import sys
from pathlib import Path
from rich.console import Console

from ui.rich_terminal import RichTerminalUI
from agents.pat_agent import PatAgent
from config import settings
from exceptions import PatCodeError, OllamaConnectionError
from tools.project_analyzer import ProjectAnalyzer

ui = RichTerminalUI()
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.3.1", prog_name="PatCode")
def cli(ctx):
    """🤖 PatCode - Asistente de programación local con IA"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command()
@click.option('--fast', is_flag=True, help='Usa modelo ligero (llama3.2:1b)')
@click.option('--deep', is_flag=True, help='Usa modelo completo (codellama:13b)')
@click.option('--model', type=str, help='Especifica modelo manualmente')
def chat(fast, deep, model):
    """Modo conversacional interactivo"""
    
    if model:
        settings.ollama.model = model
    elif fast:
        settings.ollama.model = 'llama3.2:1b'
    elif deep:
        settings.ollama.model = 'codellama:13b'
    
    ui.print_welcome(version="0.3.1")
    
    ui.display_model_info(
        model=settings.ollama.model,
        speed="Rápido" if fast else ("Profundo" if deep else "Balanceado"),
        ram="4GB" if fast else ("16GB" if deep else "8GB")
    )
    console.print()
    
    try:
        with console.status("[bold yellow]Inicializando...[/bold yellow]"):
            agent = PatAgent()
    except Exception as e:
        ui.display_error(f"Error al inicializar agente: {e}")
        sys.exit(1)
    
    while True:
        try:
            user_input = ui.prompt_user()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['/quit', 'exit', 'quit']:
                if ui.confirm_action("¿Seguro que quieres salir?"):
                    ui.display_success("¡Hasta luego!")
                    break
                continue
            
            if user_input.lower() in ['/help', 'help']:
                commands = {
                    "analyze <ruta>": "Analiza proyecto completo",
                    "explain <archivo>": "Explica código de archivo",
                    "refactor <archivo>": "Sugiere mejoras",
                    "test <archivo>": "Genera tests",
                    "/load <archivo>": "Carga archivo al contexto",
                    "/files": "Lista archivos cargados",
                    "/stats": "Estadísticas del agente",
                    "/clear": "Limpia historial",
                    "/help": "Muestra esta ayuda",
                    "/quit": "Sale de PatCode"
                }
                ui.display_help(commands)
                continue
            
            if user_input.lower() in ['/clear', 'clear']:
                agent.clear_history()
                ui.clear_screen()
                ui.display_success("Historial limpiado")
                ui.print_welcome(version="0.3.1")
                continue
            
            if user_input.lower() in ['/stats', 'stats']:
                stats = agent.get_stats()
                ui.display_stats(stats)
                continue
            
            if user_input.lower() == '/files':
                files = list(agent.file_manager.loaded_files.keys())
                if files:
                    ui.display_file_tree([Path(f) for f in files])
                else:
                    ui.display_info("No hay archivos cargados")
                continue
            
            if user_input.lower().startswith('/load '):
                file_path = user_input[6:].strip()
                try:
                    agent.file_manager.load_file(file_path)
                    ui.display_success(f"Archivo cargado: {file_path}")
                except FileNotFoundError:
                    ui.display_error(f"Archivo no encontrado: {file_path}")
                except Exception as e:
                    ui.display_error(f"Error al cargar: {e}")
                continue
            
            with ui.progress_context() as progress:
                task = progress.add_task("[cyan]Pensando...", total=100)
                progress.update(task, advance=50)
                
                response = agent.ask(user_input)
                
                progress.update(task, advance=50)
            
            console.print()
            ui.display_response(response)
            console.print()
        
        except KeyboardInterrupt:
            console.print("\n")
            if ui.confirm_action("¿Quieres salir?"):
                break
            continue
        
        except Exception as e:
            ui.display_error(f"Error: {e}")
            continue


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--deep', is_flag=True, help='Análisis profundo con IA')
@click.option('--format', type=click.Choice(['table', 'json', 'markdown']), 
              default='table', help='Formato de salida')
def analyze(path, deep, format):
    """Analiza estructura y calidad de código del proyecto"""
    
    ui.display_info(f"Analizando proyecto en: {path}")
    
    try:
        analyzer = ProjectAnalyzer()
        
        with ui.progress_context("Analizando proyecto...") as progress:
            task = progress.add_task("[cyan]Escaneando archivos...", total=100)
            progress.update(task, advance=30)
            
            report = analyzer.analyze_project(path)
            
            progress.update(task, advance=70)
        
        if format == 'table':
            report_dict = {
                'path': str(report.path),
                'scores': {
                    'estructura': report.structure_score,
                    'calidad': report.quality_score,
                },
                'suggestions': report.suggestions
            }
            ui.display_analysis_report(report_dict)
            
            from rich.table import Table
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
        
        elif format == 'markdown':
            ui.display_markdown(analyzer.format_report(report))
        
        if deep:
            ui.display_info("Análisis profundo con IA...")
            
            with ui.progress_context("Generando análisis con IA...") as progress:
                task = progress.add_task("[cyan]Analizando...", total=100)
                progress.update(task, advance=50)
                
                agent = PatAgent()
                agent.file_manager.load_project_files(path, max_files=10)
                analysis = agent.ask(
                    f"Basado en el análisis: estructura {report.structure_score}/10, "
                    f"calidad {report.quality_score}/10. "
                    "Dame 3-5 recomendaciones específicas para mejorar este proyecto."
                )
                
                progress.update(task, advance=50)
            
            console.print("\n")
            ui.display_response(analysis)
        
        ui.display_success("Análisis completado")
    
    except Exception as e:
        ui.display_error(f"Error durante análisis: {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--model', type=str, help='Modelo a usar')
def explain(file, model):
    """Explica el código de un archivo"""
    
    if model:
        settings.ollama.model = model
    
    try:
        file_path = Path(file)
        agent = PatAgent()
        agent.file_manager.load_file(file_path)
        
        ui.display_info(f"Explicando: {file_path.name}")
        
        with ui.progress_context("Generando explicación...") as progress:
            task = progress.add_task("[cyan]Analizando código...", total=100)
            progress.update(task, advance=50)
            
            response = agent.ask(f"Explica detalladamente el código de {file_path.name}")
            
            progress.update(task, advance=50)
        
        code = file_path.read_text()
        language = file_path.suffix[1:] if file_path.suffix else 'text'
        ui.display_code(code, language=language, title=file_path.name)
        console.print()
        
        ui.display_response(response)
    
    except FileNotFoundError:
        ui.display_error(f"Archivo no encontrado: {file}")
        sys.exit(1)
    except Exception as e:
        ui.display_error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--apply', is_flag=True, help='Aplica cambios automáticamente')
def refactor(file, apply):
    """Sugiere mejoras para un archivo"""
    
    agent = PatAgent()
    
    try:
        file_path = Path(file)
        agent.file_manager.load_file(file_path)
        
        ui.display_info(f"Analizando: {file_path.name}")
        
        with ui.progress_context("Generando sugerencias...") as progress:
            task = progress.add_task("[cyan]Refactorizando...", total=100)
            progress.update(task, advance=50)
            
            response = agent.ask(
                f"Sugiere mejoras y refactorings para {file_path.name}. "
                f"Muestra el código mejorado."
            )
            
            progress.update(task, advance=50)
        
        ui.display_response(response)
        
        if apply:
            if ui.confirm_action(f"⚠️  ¿Aplicar cambios a {file_path.name}?"):
                ui.display_warning("Funcionalidad 'apply' en desarrollo")
        
    except Exception as e:
        ui.display_error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), help='Archivo de salida para tests')
@click.option('--framework', type=str, default='pytest', help='Framework de testing')
def test(file, output, framework):
    """Genera tests para un archivo"""
    
    agent = PatAgent()
    
    try:
        file_path = Path(file)
        agent.file_manager.load_file(file_path)
        
        ui.display_info(f"Generando tests para: {file_path.name}")
        
        with ui.progress_context("Generando tests...") as progress:
            task = progress.add_task("[cyan]Creando casos de prueba...", total=100)
            progress.update(task, advance=50)
            
            response = agent.ask(
                f"Genera tests completos con {framework} para {file_path.name}. "
                f"Incluye casos edge, mocks si es necesario, y asserts claros."
            )
            
            progress.update(task, advance=50)
        
        ui.display_response(response)
        
        if output:
            output_path = Path(output)
            if ui.confirm_action(f"Guardar tests en {output_path}?"):
                ui.display_warning("Auto-guardado en desarrollo")
    
    except Exception as e:
        ui.display_error(f"Error: {e}")
        sys.exit(1)


@cli.command()
def info():
    """Muestra información del sistema"""
    
    try:
        import requests
        response = requests.get(f"{settings.ollama.base_url}/api/tags", timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            from rich.table import Table
            table = Table(title="🤖 Modelos Disponibles", show_header=True)
            table.add_column("Modelo", style="cyan")
            table.add_column("Tamaño", justify="right")
            table.add_column("Modificado", style="dim")
            
            for model in models:
                table.add_row(
                    model.get('name', 'N/A'),
                    f"{model.get('size', 0) / 1e9:.1f} GB",
                    model.get('modified_at', 'N/A')[:10]
                )
            
            console.print(table)
            console.print()
        
        ui.display_info(
            f"Modelo actual: {settings.ollama.model}\n"
            f"URL Ollama: {settings.ollama.base_url}\n"
            f"Versión PatCode: 0.3.1\n"
            f"Memoria máxima: {settings.memory.max_size} mensajes\n"
            f"Contexto activo: {settings.memory.max_active_messages} mensajes"
        )
    
    except Exception as e:
        ui.display_error(f"Error al obtener info: {e}")


if __name__ == '__main__':
    cli()
