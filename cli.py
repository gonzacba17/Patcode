"""
PatCode - CLI con Click y RichTerminalUI
Interfaz moderna con comandos estructurados y visuales avanzados
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ui.rich_terminal import RichTerminalUI
from agents.pat_agent import PatAgent
from config import settings
from config.model_selector import get_model_selector
from utils.response_cache import ResponseCache
from exceptions import PatCodeError, OllamaConnectionError
from tools.project_analyzer import ProjectAnalyzer
from tools.plugin_system import get_plugin_manager
from rich.panel import Panel

ui = RichTerminalUI()
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.5.0", prog_name="PatCode")
def cli(ctx):
    """🤖 PatCode - Asistente de programación local con IA"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command()
@click.option('--fast', is_flag=True, help='Usa modelo ligero (llama3.2:1b)')
@click.option('--deep', is_flag=True, help='Usa modelo completo (codellama:13b)')
@click.option('--auto', is_flag=True, help='Selección automática de modelo')
@click.option('--model', type=str, help='Especifica modelo manualmente')
@click.option('--no-cache', is_flag=True, help='Desactiva cache')
def chat(fast, deep, auto, model, no_cache):
    """Modo conversacional interactivo"""
    
    selector = get_model_selector()
    
    if auto:
        settings.ollama.model = selector.recommend_model(use_case='general')
        ui.display_info(f"🤖 Modelo auto-seleccionado: {settings.ollama.model}")
    elif fast:
        settings.ollama.model = 'llama3.2:1b'
    elif deep:
        compatible = selector.list_compatible_models()
        deep_models = ['codellama:13b', 'codellama:7b', 'mistral:7b']
        for m in deep_models:
            if m in compatible:
                settings.ollama.model = m
                break
    elif model:
        settings.ollama.model = model
    
    model_info = selector.get_model_info(settings.ollama.model)
    if model_info:
        speed_rec = selector.get_speed_recommendation(settings.ollama.model)
        ui.display_model_info(
            model=settings.ollama.model,
            speed=speed_rec,
            ram=f"{model_info.ram_min}-{model_info.ram_recommended}GB"
        )
    
    ui.print_welcome(version="0.5.0")
    console.print()
    
    try:
        with console.status("[bold yellow]Inicializando...[/bold yellow]"):
            agent = PatAgent()
            
            if no_cache:
                agent.cache = None
                ui.display_warning("Cache desactivado para esta sesión")
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
                    "/cache": "Estadísticas de cache",
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
                ui.print_welcome(version="0.5.0")
                continue
            
            if user_input.lower() in ['/stats', 'stats']:
                stats = agent.get_stats()
                ui.display_stats(stats)
                
                if agent.cache:
                    cache_stats = agent.cache.get_stats()
                    ui.display_info(
                        f"💾 Cache Performance:\n"
                        f"Hit Rate: {cache_stats['hit_rate']}\n"
                        f"Total Queries: {cache_stats['total_queries']}\n"
                        f"Size: {cache_stats['cache_size']}"
                    )
                continue
            
            if user_input.lower() == '/cache':
                if agent.cache:
                    cache_stats = agent.cache.get_stats()
                    ui.display_stats(cache_stats)
                else:
                    ui.display_warning("Cache desactivado")
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
@click.argument('action', type=click.Choice(['clear', 'stats', 'clean']))
def cache(action):
    """Gestiona el cache de respuestas"""
    from utils.response_cache import ResponseCache
    
    cache = ResponseCache()
    
    if action == 'stats':
        stats = cache.get_stats()
        ui.display_stats(stats)
    
    elif action == 'clear':
        if ui.confirm_action("⚠️  ¿Limpiar todo el cache?"):
            deleted = cache.clear_all()
            ui.display_success(f"Cache limpiado: {deleted} archivos eliminados")
    
    elif action == 'clean':
        deleted = cache.clear_expired()
        ui.display_success(f"Cache expirado limpiado: {deleted} archivos")


@cli.command()
def models():
    """Lista modelos compatibles y recomendaciones"""
    selector = get_model_selector()
    
    table = Table(title="🤖 Modelos Disponibles", show_header=True)
    table.add_column("Modelo", style="cyan")
    table.add_column("Velocidad", justify="center")
    table.add_column("RAM Min", justify="right")
    table.add_column("RAM Rec", justify="right")
    table.add_column("Casos de Uso", style="dim")
    table.add_column("Compatible", justify="center")
    
    compatible_models = selector.list_compatible_models()
    
    for model_name, profile in selector.MODELS.items():
        is_compatible = "✅" if model_name in compatible_models else "❌"
        
        table.add_row(
            profile.name,
            profile.speed,
            f"{profile.ram_min}GB",
            f"{profile.ram_recommended}GB",
            ", ".join(profile.use_cases[:2]),
            is_compatible
        )
    
    console.print(table)
    console.print()
    
    ui.display_info(
        f"💻 RAM Disponible: {selector.system_info['available_ram_gb']:.1f}GB\n"
        f"🚀 Recomendado para General: {selector.recommend_model('general')}\n"
        f"⚡ Recomendado para Rápido: {selector.recommend_model('quick_questions')}\n"
        f"🔬 Recomendado para Análisis: {selector.recommend_model('refactor')}"
    )


@cli.command()
def info():
    """Muestra información del sistema"""
    
    try:
        import requests
        response = requests.get(f"{settings.ollama.base_url}/api/tags", timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            table = Table(title="🤖 Modelos Instalados en Ollama", show_header=True)
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
            f"Versión PatCode: 0.5.0\n"
            f"Memoria máxima: {settings.memory.max_size} mensajes\n"
            f"Contexto activo: {settings.memory.max_active_messages} mensajes"
        )
    
    except Exception as e:
        ui.display_error(f"Error al obtener info: {e}")


@cli.group()
def plugin():
    """Gestiona y ejecuta plugins"""
    pass


@plugin.command(name='list')
def plugin_list():
    """Lista todos los plugins disponibles"""
    manager = get_plugin_manager()
    
    plugins = manager.list_plugins()
    
    if not plugins:
        ui.display_warning("No hay plugins instalados")
        return
    
    table = Table(title="🔌 Plugins Disponibles", show_header=True)
    table.add_column("Nombre", style="cyan")
    table.add_column("Versión", justify="center")
    table.add_column("Descripción", style="dim")
    table.add_column("Autor", style="green")
    
    for plugin_info in plugins:
        table.add_row(
            plugin_info['name'],
            plugin_info['version'],
            plugin_info['description'][:50] + '...' if len(plugin_info['description']) > 50 else plugin_info['description'],
            plugin_info['author']
        )
    
    console.print(table)
    console.print()
    
    if manager.failed_plugins:
        ui.display_warning(
            f"⚠️  {len(manager.failed_plugins)} plugins fallaron al cargar:\n" +
            '\n'.join([f"  • {name}: {error}" for name, error in manager.failed_plugins.items()])
        )


@plugin.command(name='info')
@click.argument('plugin_name')
def plugin_info(plugin_name):
    """Muestra información detallada de un plugin"""
    manager = get_plugin_manager()
    
    plugin_obj = manager.get_plugin(plugin_name)
    
    if not plugin_obj:
        ui.display_error(f"Plugin '{plugin_name}' no encontrado")
        sys.exit(1)
    
    info = f"""[bold cyan]{plugin_obj.name}[/bold cyan] v{plugin_obj.version}

[bold]Descripción:[/bold]
{plugin_obj.description}

[bold]Autor:[/bold] {plugin_obj.author}

[bold]Dependencias:[/bold]
{', '.join(plugin_obj.dependencies) if plugin_obj.dependencies else 'Ninguna'}
"""
    
    console.print(Panel(info, border_style="cyan"))


@plugin.command(name='run')
@click.argument('plugin_name')
@click.option('--action', default=None, help='Acción específica del plugin')
@click.option('--file', type=click.Path(), help='Archivo de entrada')
@click.option('--output', type=click.Path(), help='Directorio de salida')
@click.option('--save', is_flag=True, help='Guardar resultado en disco')
@click.pass_context
def plugin_run(ctx, plugin_name, action, file, output, save):
    """Ejecuta un plugin"""
    manager = get_plugin_manager()
    
    plugin_obj = manager.get_plugin(plugin_name)
    if not plugin_obj:
        ui.display_error(f"Plugin '{plugin_name}' no encontrado")
        ui.display_info("Usa 'patcode plugin list' para ver plugins disponibles")
        sys.exit(1)
    
    ui.display_info(f"Ejecutando plugin: {plugin_name} v{plugin_obj.version}")
    
    try:
        agent = PatAgent()
    except Exception as e:
        ui.display_error(f"Error inicializando agente: {e}")
        sys.exit(1)
    
    context = {
        'agent': agent,
        'files': list(agent.file_manager.loaded_files.values()),
        'user_input': '',
        'config': settings,
        'current_dir': Path.cwd(),
        'args': {
            'action': action,
            'file': file,
            'output': output,
            'save': save
        }
    }
    
    with ui.progress_context(f"Ejecutando {plugin_name}...") as progress:
        task = progress.add_task("[cyan]Procesando...", total=100)
        progress.update(task, advance=50)
        
        result = manager.execute_plugin(plugin_name, context)
        
        progress.update(task, advance=50)
    
    if result['success']:
        ui.display_success(result['result'])
        
        if 'data' in result and 'content' in result['data']:
            console.print()
            if isinstance(result['data']['content'], str):
                if result['data']['content'].startswith('```'):
                    ui.display_markdown(result['data']['content'])
                else:
                    ui.display_code(
                        result['data']['content'], 
                        language='dockerfile' if 'Dockerfile' in result['result'] else 'yaml'
                    )
    else:
        ui.display_error(result.get('error', 'Error desconocido'))
        sys.exit(1)


@plugin.command(name='reload')
@click.argument('plugin_name')
def plugin_reload(plugin_name):
    """Recarga un plugin"""
    manager = get_plugin_manager()
    
    try:
        manager.reload_plugin(plugin_name)
        ui.display_success(f"Plugin '{plugin_name}' recargado")
    except Exception as e:
        ui.display_error(f"Error recargando plugin: {e}")
        sys.exit(1)


@cli.command()
@click.argument('action', type=click.Choice(['status', 'diff', 'commit', 'log', 'suggest']))
@click.option('--message', '-m', help='Mensaje de commit')
@click.option('--limit', default=10, help='Límite de commits para log')
def git(action, message, limit):
    """
    Asistente Git (shortcut para git_helper plugin)
    
    Actions:
      status   - Git status con análisis
      diff     - Git diff con estadísticas
      commit   - Crear commit
      log      - Ver últimos commits
      suggest  - Sugerir mensaje de commit semántico
    """
    manager = get_plugin_manager()
    
    try:
        agent = PatAgent()
    except Exception as e:
        ui.display_error(f"Error: {e}")
        sys.exit(1)
    
    context = {
        'agent': agent,
        'files': [],
        'user_input': '',
        'config': settings,
        'current_dir': Path.cwd(),
        'args': {
            'action': 'suggest_commit' if action == 'suggest' else action,
            'message': message,
            'limit': limit
        }
    }
    
    with ui.progress_context(f"Ejecutando git {action}...") as progress:
        task = progress.add_task("[cyan]Procesando...", total=100)
        progress.update(task, advance=50)
        
        result = manager.execute_plugin('git_helper', context)
        
        progress.update(task, advance=50)
    
    if result['success']:
        if action == 'diff' and 'data' in result:
            ui.display_code(result['data'].get('diff', ''), language='diff')
        else:
            ui.display_success(result['result'])
    else:
        ui.display_error(result.get('error', 'Error desconocido'))


@cli.command()
@click.argument('action', type=click.Choice(['dockerfile', 'compose', 'dockerignore', 'all']))
@click.option('--language', help='Lenguaje del proyecto (auto-detecta si no se especifica)')
@click.option('--framework', help='Framework usado (ej: fastapi, flask, express)')
@click.option('--save', is_flag=True, help='Guardar archivos generados')
def docker(action, language, framework, save):
    """
    Generador Docker (shortcut para docker_helper plugin)
    
    Actions:
      dockerfile    - Genera Dockerfile optimizado
      compose       - Genera docker-compose.yml
      dockerignore  - Genera .dockerignore
      all           - Genera todos los archivos
    """
    manager = get_plugin_manager()
    
    try:
        agent = PatAgent()
    except Exception as e:
        ui.display_error(f"Error: {e}")
        sys.exit(1)
    
    context = {
        'agent': agent,
        'files': [],
        'user_input': '',
        'config': settings,
        'current_dir': Path.cwd(),
        'args': {
            'action': action,
            'language': language,
            'framework': framework,
            'save': save
        }
    }
    
    with ui.progress_context(f"Generando {action}...") as progress:
        task = progress.add_task("[cyan]Generando...", total=100)
        progress.update(task, advance=50)
        
        result = manager.execute_plugin('docker_helper', context)
        
        progress.update(task, advance=50)
    
    if result['success']:
        ui.display_success(result['result'])
        
        if 'data' in result and 'content' in result['data']:
            console.print()
            ui.display_code(result['data']['content'], language='dockerfile')
    else:
        ui.display_error(result.get('error', 'Error desconocido'))


@cli.command()
@click.argument('action', type=click.Choice(['docstrings', 'readme', 'api', 'all']))
@click.option('--file', type=click.Path(), help='Archivo para generar docstrings')
@click.option('--output', default='docs/', help='Directorio de salida')
@click.option('--save', is_flag=True, help='Guardar documentación generada')
def docs(action, file, output, save):
    """
    Generador de documentación (shortcut para docs_generator plugin)
    
    Actions:
      docstrings - Genera docstrings faltantes
      readme     - Genera/actualiza README.md
      api        - Genera documentación API
      all        - Genera toda la documentación
    """
    manager = get_plugin_manager()
    
    try:
        agent = PatAgent()
    except Exception as e:
        ui.display_error(f"Error: {e}")
        sys.exit(1)
    
    context = {
        'agent': agent,
        'files': [],
        'user_input': '',
        'config': settings,
        'current_dir': Path.cwd(),
        'args': {
            'action': action,
            'file': file,
            'output': output,
            'save': save
        }
    }
    
    with ui.progress_context(f"Generando {action}...") as progress:
        task = progress.add_task("[cyan]Generando documentación...", total=100)
        progress.update(task, advance=30)
        
        result = manager.execute_plugin('docs_generator', context)
        
        progress.update(task, advance=70)
    
    if result['success']:
        ui.display_success(result['result'])
        
        if 'data' in result and 'suggestions' in result['data']:
            console.print()
            ui.display_markdown(result['data']['suggestions'])
    else:
        ui.display_error(result.get('error', 'Error desconocido'))


if __name__ == '__main__':
    cli()
