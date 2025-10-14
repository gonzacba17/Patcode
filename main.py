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
    import logging
    from config.settings import settings
    from rich.console import Console

    console = Console()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []

    # Handler de archivo si está habilitado
    if settings.logging.file:
        try:
            # Asegurarse que el directorio exista
            log_path = Path(settings.logging.filename)
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

[dim]Versión: 0.2.0 | Modelo: {settings.ollama.model}[/dim]

[bold]Comandos disponibles:[/bold]
  [yellow]/clear[/yellow]     - Limpiar historial de conversación
  [yellow]/stats[/yellow]     - Ver estadísticas de la sesión
  [yellow]/export[/yellow]    - Exportar historial
  [yellow]/quit[/yellow]      - Salir de PatCode
  [yellow]/exit[/yellow]      - Salir de PatCode
  [yellow]Ctrl+C[/yellow]     - Salir (con confirmación)

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
    command = command.lower().strip()
    
    # Comandos de salida
    if command in ["/quit", "/exit"]:
        console.print("[yellow]👋 ¡Hasta luego![/yellow]")
        return False
    
    # Limpiar historial
    elif command == "/clear":
        try:
            agent.clear_history()
            console.print("[green]✓ Historial limpiado[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error al limpiar: {e}[/red]")
    
    # Mostrar estadísticas
    elif command == "/stats":
        stats = agent.get_stats()
        stats_text = f"""
[bold]Estadísticas de la sesión:[/bold]

  Total de mensajes: {stats['total_messages']}
  Mensajes de usuario: {stats['user_messages']}
  Respuestas de Pat: {stats['assistant_messages']}
  Modelo: {stats['model']}
  Memoria: {stats['memory_path']}
        """
        console.print(Panel(stats_text, border_style="blue", title="📊 Stats"))
    
    # Exportar historial
    elif command == "/export":
        try:
            export_path = Path(f"./data/exports/history_export.json")
            agent.export_history(export_path)
            console.print(f"[green]✓ Historial exportado a: {export_path}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error al exportar: {e}[/red]")
    
    # Comando desconocido
    else:
        console.print(f"[yellow]⚠️  Comando desconocido: {command}[/yellow]")
        console.print("[dim]Usa /quit, /clear, /stats o /export[/dim]")
    
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