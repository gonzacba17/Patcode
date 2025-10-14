"""
PatCode - CLI Principal

Interfaz de línea de comandos para interactuar con el asistente Pat.
"""

import sys
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table

from agents.pat_agent import PatAgent
from config import settings
from exceptions import (
    PatCodeError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    InvalidPromptError,
    ConfigurationError
)

# Console de Rich para output mejorado
console = Console()

# Logger
logger = logging.getLogger(__name__)

def setup_logging() -> None:
    """
    Configura el sistema de logging basado en settings.
    
    Si settings.logging.file está habilitado, escribe a archivo.
    Siempre muestra WARNING+ en consola.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []

    # Handler de archivo si está habilitado
    if settings.logging.file:
        try:
            # Asegurarse que el directorio exista
            log_path = Path(settings.logging.file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(settings.logging.level)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            console.print(f"[yellow]⚠️  No se pudo crear archivo de log: {e}[/yellow]")

    # Handler de consola (solo WARNING+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # Configurar logger raíz
    logging.basicConfig(
        level=settings.logging.level,
        format=log_format,
        handlers=handlers
    )

def print_welcome() -> None:
    """Muestra el mensaje de bienvenida con información del sistema."""
    welcome_text = f"""
[bold cyan]🤖 PatCode - Asistente de Programación Local[/bold cyan]

[dim]Versión: 0.3.0 | Modelo: {settings.ollama.model}[/dim]

[bold]Comandos disponibles:[/bold]

[yellow]Conversación:[/yellow]
  [cyan]/clear[/cyan]     - Limpiar historial de conversación
  [cyan]/stats[/cyan]     - Ver estadísticas de la sesión
  [cyan]/export[/cyan]    - Exportar historial
  
[yellow]Archivos:[/yellow]
  [cyan]/load <archivo>[/cyan]      - Cargar archivo al contexto
  [cyan]/read <archivo>[/cyan]      - Alias de /load
  [cyan]/show <archivo>[/cyan]      - Mostrar contenido de archivo cargado
  [cyan]/unload <archivo>[/cyan]    - Descargar archivo del contexto
  [cyan]/files[/cyan]                - Listar archivos cargados
  [cyan]/clear_files[/cyan]          - Limpiar todos los archivos
  
[yellow]Proyecto:[/yellow]
  [cyan]/project[/cyan]              - Analizar y cargar proyecto actual
  [cyan]/analyze[/cyan]              - Ver estructura del proyecto
  
[yellow]Sistema:[/yellow]
  [cyan]/help[/cyan]                 - Mostrar esta ayuda
  [cyan]/quit[/cyan] o [cyan]/exit[/cyan]      - Salir de PatCode
  [cyan]Ctrl+C[/cyan]                - Salir (con confirmación)

[dim]Escribe tu pregunta y presiona Enter para comenzar.[/dim]
    """
    
    console.print(Panel(welcome_text, border_style="cyan", padding=(1, 2)))


def handle_special_commands(command: str, agent: PatAgent) -> bool:
    """
    Maneja comandos especiales del sistema.
    
    Args:
        command: Comando ingresado por el usuario
        agent: Instancia del agente
        
    Returns:
        True si debe continuar el loop, False si debe salir
    """
    command = command.strip()
    cmd_lower = command.lower()
    
    # Parsear comando y argumentos
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    # ==================== COMANDOS DE SISTEMA ====================
    
    if cmd in ["/quit", "/exit"]:
        console.print("[yellow]👋 ¡Hasta luego![/yellow]")
        return False
    
    elif cmd == "/help":
        print_welcome()
    
    # ==================== COMANDOS DE CONVERSACIÓN ====================
    
    elif cmd == "/clear":
        try:
            agent.clear_history()
            console.print("[green]✓ Historial limpiado[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error al limpiar: {e}[/red]")
    
    elif cmd == "/stats":
        stats = agent.get_stats()
        
        # Crear tabla de estadísticas
        table = Table(title="📊 Estadísticas de la Sesión", show_header=True)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Total de mensajes", str(stats['total_messages']))
        table.add_row("Mensajes de usuario", str(stats['user_messages']))
        table.add_row("Respuestas de Pat", str(stats['assistant_messages']))
        table.add_row("Modelo LLM", stats['model'])
        table.add_row("─" * 30, "─" * 20)
        table.add_row("Archivos cargados", str(stats['loaded_files']))
        table.add_row("Tamaño archivos", f"{stats['files_size_kb']} KB")
        table.add_row("Uso de contexto", f"{stats['files_usage_percent']}%")
        
        console.print(table)
    
    elif cmd == "/export":
        try:
            export_path = Path(f"./data/exports/history_export.json")
            agent.export_history(export_path)
            console.print(f"[green]✓ Historial exportado a: {export_path}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error al exportar: {e}[/red]")
    
    # ==================== COMANDOS DE ARCHIVOS ====================
    
    elif cmd in ["/load", "/read"]:
        if not args:
            console.print("[yellow]⚠️  Uso: /load <ruta_archivo>[/yellow]")
            console.print("[dim]Ejemplo: /load main.py[/dim]")
            return True
        
        try:
            with console.status(f"[yellow]📁 Cargando {args}...[/yellow]"):
                loaded_file = agent.file_manager.load_file(args)
            
            console.print(f"[green]✓ Archivo cargado: {loaded_file.get_summary()}[/green]")
            
            # Mostrar preview del contenido
            lines = loaded_file.content.splitlines()
            preview_lines = min(10, len(lines))
            console.print(f"\n[dim]Preview (primeras {preview_lines} líneas):[/dim]")
            for i, line in enumerate(lines[:preview_lines], 1):
                console.print(f"[dim]{i:3d} | {line[:80]}[/dim]")
            if len(lines) > preview_lines:
                console.print(f"[dim]... y {len(lines) - preview_lines} líneas más[/dim]")
            
            console.print("\n[dim]Ahora pregunta: '¿Qué hace este código?' o 'Analiza este archivo'[/dim]")
        except FileNotFoundError:
            console.print(f"[red]✗ Archivo no encontrado: {args}[/red]")
        except PatCodeError as e:
            console.print(f"[red]✗ {e}[/red]")
        except Exception as e:
            console.print(f"[red]✗ Error al cargar archivo: {e}[/red]")
    
    elif cmd == "/unload":
        if not args:
            console.print("[yellow]⚠️  Uso: /unload <ruta_archivo>[/yellow]")
            return True
        
        if agent.file_manager.unload_file(args):
            console.print(f"[green]✓ Archivo descargado: {args}[/green]")
        else:
            console.print(f"[yellow]⚠️  Archivo no estaba cargado: {args}[/yellow]")
    
    elif cmd == "/files":
        files = agent.file_manager.list_files()
        
        if not files:
            console.print("[yellow]No hay archivos cargados en el contexto[/yellow]")
            console.print("[dim]Usa /load <archivo> para cargar archivos[/dim]")
        else:
            table = Table(title="📁 Archivos en Contexto", show_header=True)
            table.add_column("#", style="dim")
            table.add_column("Archivo", style="cyan")
            table.add_column("Info", style="green")
            
            for i, file_path in enumerate(files, 1):
                file_obj = agent.file_manager.loaded_files[file_path]
                lines = len(file_obj.content.splitlines())
                size_kb = file_obj.size / 1024
                table.add_row(
                    str(i),
                    file_obj.path.name,
                    f"{lines} líneas | {size_kb:.1f} KB"
                )
            
            console.print(table)
            
            stats = agent.file_manager.get_stats()
            console.print(
                f"\n[dim]Total: {stats['total_files']} archivos | "
                f"{stats['total_size_kb']} KB | "
                f"Uso: {stats['usage_percent']}%[/dim]"
            )
    
    elif cmd == "/clear_files":
        count = agent.file_manager.clear_all()
        if count > 0:
            console.print(f"[green]✓ {count} archivo(s) eliminado(s) del contexto[/green]")
        else:
            console.print("[yellow]No había archivos cargados[/yellow]")
    
    elif cmd == "/show":
        if not args:
            console.print("[yellow]⚠️  Uso: /show <archivo>[/yellow]")
            console.print("[dim]Muestra el contenido de un archivo cargado[/dim]")
            return True
        
        # Buscar archivo cargado
        found = None
        for file_path, loaded_file in agent.file_manager.loaded_files.items():
            if args.lower() in loaded_file.path.name.lower():
                found = loaded_file
                break
        
        if found:
            console.print(Panel(
                f"[cyan]{found.path.name}[/cyan]\n"
                f"[dim]{len(found.content.splitlines())} líneas | {found.size} bytes[/dim]",
                title="📄 Archivo"
            ))
            
            # Mostrar contenido con syntax highlighting
            from rich.syntax import Syntax
            syntax = Syntax(
                found.content[:3000],  # Primeros 3000 caracteres
                found.path.suffix[1:] if found.path.suffix else "text",
                theme="monokai",
                line_numbers=True
            )
            console.print(syntax)
            
            if len(found.content) > 3000:
                console.print(f"[dim]... (mostrando primeros 3000 caracteres de {len(found.content)})[/dim]")
        else:
            console.print(f"[yellow]⚠️  Archivo no encontrado en contexto: {args}[/yellow]")
            console.print("[dim]Usa /files para ver archivos cargados[/dim]")
    
    # ==================== COMANDOS DE PROYECTO ====================
    
    elif cmd == "/analyze_file":
        if not args:
            console.print("[yellow]⚠️  Uso: /analyze_file <nombre_archivo>[/yellow]")
            console.print("[dim]Ejemplo: /analyze_file main.py[/dim]")
            return True
        
        try:
            with console.status(f"[yellow]🔍 Analizando {args}...[/yellow]"):
                analysis = agent.analyze_file(args)
            
            console.print(f"\n[bold cyan]Análisis de {args}:[/bold cyan]")
            console.print(Markdown(analysis))
        except FileNotFoundError as e:
            console.print(f"[red]✗ {e}[/red]")
            console.print("[dim]Primero carga el archivo con: /load {args}[/dim]")
        except Exception as e:
            console.print(f"[red]✗ Error al analizar: {e}[/red]")
    
    elif cmd == "/project":
        try:
            project_path = args if args else "."
            
            with console.status(f"[yellow]🔍 Analizando proyecto en {project_path}...[/yellow]"):
                loaded_files = agent.file_manager.load_project_files(
                    project_path=project_path,
                    max_files=20
                )
            
            if loaded_files:
                console.print(f"[green]✓ Proyecto cargado: {len(loaded_files)} archivos[/green]")
                
                # Mostrar resumen
                table = Table(title="📦 Archivos del Proyecto", show_header=True)
                table.add_column("Archivo", style="cyan")
                table.add_column("Líneas", style="green")
                
                for file in loaded_files[:10]:  # Mostrar solo los primeros 10
                    lines = len(file.content.splitlines())
                    table.add_row(file.path.name, str(lines))
                
                if len(loaded_files) > 10:
                    table.add_row("...", f"y {len(loaded_files) - 10} más")
                
                console.print(table)
                console.print("[dim]Pat ahora conoce tu proyecto. ¡Hazle preguntas![/dim]")
            else:
                console.print("[yellow]⚠️  No se encontraron archivos en el proyecto[/yellow]")
                
        except Exception as e:
            console.print(f"[red]✗ Error al cargar proyecto: {e}[/red]")
    
    elif cmd == "/analyze":
        try:
            project_path = args if args else "."
            
            with console.status(f"[yellow]🔍 Analizando {project_path}...[/yellow]"):
                files = agent.file_manager.analyze_project(
                    project_path=project_path,
                    max_files=100
                )
            
            if files:
                console.print(f"[green]✓ Encontrados {len(files)} archivos[/green]\n")
                
                # Agrupar por extensión
                by_extension = {}
                for file in files:
                    ext = file.suffix or "sin extensión"
                    if ext not in by_extension:
                        by_extension[ext] = []
                    by_extension[ext].append(file)
                
                # Mostrar tabla
                table = Table(title="📊 Estructura del Proyecto", show_header=True)
                table.add_column("Tipo", style="cyan")
                table.add_column("Cantidad", style="green")
                table.add_column("Ejemplos", style="dim")
                
                for ext, file_list in sorted(by_extension.items()):
                    examples = ", ".join([f.name for f in file_list[:3]])
                    if len(file_list) > 3:
                        examples += f" (+{len(file_list) - 3})"
                    table.add_row(ext, str(len(file_list)), examples)
                
                console.print(table)
                console.print(f"\n[dim]Usa /project para cargar archivos al contexto[/dim]")
            else:
                console.print("[yellow]⚠️  No se encontraron archivos[/yellow]")
                
        except Exception as e:
            console.print(f"[red]✗ Error al analizar: {e}[/red]")
    
    # ==================== COMANDO DESCONOCIDO ====================
    
    else:
        console.print(f"[yellow]⚠️  Comando desconocido: {cmd}[/yellow]")
        console.print("[dim]Usa /help para ver todos los comandos disponibles[/dim]")
    
    return True


def main() -> None:
    """
    Función principal del CLI.
    
    Maneja el loop de interacción, procesamiento de comandos
    y manejo de errores.
    """
    # Setup
    setup_logging()
    logger.info("Iniciando PatCode...")
    
    try:
        # Inicializar agente
        with console.status("[bold yellow]Inicializando PatCode...[/bold yellow]"):
            agent = PatAgent()
        
        # Mostrar bienvenida
        print_welcome()
        
        # Mensaje si hay README cargado
        if agent.file_manager.loaded_files:
            console.print(
                "[dim]💡 README detectado y cargado automáticamente[/dim]\n"
            )
        
        # Loop principal
        while True:
            try:
                # Obtener input del usuario
                prompt = Prompt.ask("\n[bold green]Tú[/bold green]")
                
                # Verificar si es un comando especial
                if prompt.startswith('/'):
                    should_continue = handle_special_commands(prompt, agent)
                    if not should_continue:
                        break
                    continue
                
                # Procesar pregunta normal
                with console.status("[bold yellow]🤔 Pat está pensando...[/bold yellow]"):
                    answer = agent.ask(prompt)
                
                # Mostrar respuesta
                console.print(f"\n[bold cyan]Pat:[/bold cyan]")
                console.print(Markdown(answer))
                
            except InvalidPromptError as e:
                console.print(f"[yellow]⚠️  {e}[/yellow]")
                console.print("[dim]Tip: Escribe una pregunta no vacía[/dim]")
            
            except OllamaModelNotFoundError as e:
                console.print(f"[red]🔍 {e}[/red]")
                console.print(
                    f"[yellow]Tip: Descarga el modelo con:[/yellow]\n"
                    f"  [cyan]ollama pull {settings.ollama.model}[/cyan]"
                )
                retry = Prompt.ask("¿Continuar esperando?", choices=["s", "n"], default="n")
                if retry == "n":
                    break
            
            except OllamaTimeoutError as e:
                console.print(f"[red]⏱️  {e}[/red]")
                console.print(
                    "[yellow]Tip: Aumenta REQUEST_TIMEOUT en .env o usa un modelo más rápido[/yellow]"
                )
                retry = Prompt.ask("¿Intentar de nuevo?", choices=["s", "n"], default="s")
                if retry == "n":
                    break
            
            except OllamaConnectionError as e:
                console.print(f"[red]🔌 {e}[/red]")
                console.print(
                    "[yellow]Verifica que Ollama esté corriendo:[/yellow]\n"
                    "  [cyan]ollama serve[/cyan]"
                )
                retry = Prompt.ask("¿Reintentar conexión?", choices=["s", "n"], default="s")
                if retry == "n":
                    break
            
            except KeyboardInterrupt:
                console.print("\n[yellow]⏸️  Interrumpido por el usuario[/yellow]")
                save = Prompt.ask(
                    "¿Guardar historial antes de salir?", 
                    choices=["s", "n"], 
                    default="s"
                )
                if save == "s":
                    try:
                        agent._save_history()
                        console.print("[green]✓ Historial guardado[/green]")
                    except Exception as e:
                        console.print(f"[red]✗ Error al guardar: {e}[/red]")
                break
            
            except PatCodeError as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                logger.exception("Error manejado en main loop")
                
                # Ofrecer continuar o salir
                continue_chat = Prompt.ask(
                    "¿Deseas continuar?", 
                    choices=["s", "n"], 
                    default="s"
                )
                if continue_chat == "n":
                    break
            
            except Exception as e:
                console.print(f"[red]💥 Error inesperado: {e}[/red]")
                logger.exception("Error no manejado en main loop")
                console.print(
                    "[yellow]Por favor reporta este error en:[/yellow]\n"
                    "  [cyan]https://github.com/gonzacba17/Patcode/issues[/cyan]"
                )
                
                # Ofrecer continuar o salir
                continue_chat = Prompt.ask(
                    "¿Deseas continuar (puede ser inestable)?", 
                    choices=["s", "n"], 
                    default="n"
                )
                if continue_chat == "n":
                    break
    
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Saliendo...[/yellow]")
        sys.exit(0)
    
    except ConfigurationError as e:
        console.print(f"[red]⚙️  Error de configuración: {e}[/red]")
        console.print(
            "[yellow]Verifica tu archivo .env y compáralo con .env.example[/yellow]"
        )
        logger.exception("Error de configuración")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]💥 Error fatal al inicializar: {e}[/red]")
        logger.exception("Error fatal")
        sys.exit(1)
    
    logger.info("PatCode finalizado correctamente")


if __name__ == "__main__":
    main()