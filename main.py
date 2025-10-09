"""
PatCode - Asistente de Programación Local
main.py - Punto de entrada mejorado
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import print as rprint
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

# Importar agente
try:
    from agents.pat_agent import PatAgent
except ImportError as e:
    print(f"⚠️  Advertencia: No se pudo importar PatAgent - {e}")
    PatAgent = None

# Importar tools
try:
    from tools import list_tools, get_tools_by_category
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Advertencia: Módulo tools no disponible - {e}")
    TOOLS_AVAILABLE = False


console = Console()


def show_banner():
    """Muestra el banner de bienvenida"""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║         🧠 PatCode - AI Code Assistant        ║
    ║         Powered by Ollama (Local AI)          ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print("💡 Escribe '/help' para ver comandos disponibles\n", style="dim")


def show_help():
    """Muestra ayuda con comandos disponibles"""
    help_text = """
    ## 📚 Comandos Disponibles
    
    **Comandos Básicos:**
    - `/help` - Muestra esta ayuda
    - `/clear` - Limpia la pantalla
    - `/history` - Muestra historial de conversación
    - `/reset` - Reinicia la conversación (limpia memoria)
    - `/exit` o `/quit` - Sale del programa
    
    **Comandos de Herramientas:**
    - `/tools` - Lista todas las herramientas disponibles
    - `/tools <categoría>` - Lista herramientas de una categoría
    
    **Comandos de Contexto:**
    - `/context` - Muestra información del proyecto actual
    - `/analyze <archivo>` - Analiza un archivo específico
    
    **Modo Conversación:**
    - Simplemente escribe tu pregunta o instrucción
    - Usa Ctrl+C para cancelar operación actual
    - Usa Ctrl+D o escribe 'exit' para salir
    """
    console.print(Panel(Markdown(help_text), title="Ayuda", border_style="blue"))


def show_tools():
    """Muestra herramientas disponibles"""
    if not TOOLS_AVAILABLE:
        console.print("⚠️  Herramientas no disponibles", style="yellow")
        return
    
    try:
        categories = get_tools_by_category()
        
        console.print("\n🔧 Herramientas Disponibles:\n", style="bold cyan")
        
        for category, tools in categories.items():
            console.print(f"  • {category.replace('_', ' ').title()}", style="bold green")
            for tool in tools:
                console.print(f"    - {tool}", style="dim")
        
        console.print(f"\n✅ Total: {sum(len(tools) for tools in categories.values())} herramientas\n")
    except Exception as e:
        console.print(f"⚠️  Error mostrando herramientas: {e}", style="yellow")


def show_context(workspace_root: Path):
    """Muestra información del contexto actual"""
    console.print("\n📂 Contexto del Proyecto:\n", style="bold cyan")
    console.print(f"  • Directorio: {workspace_root}", style="green")
    
    # Detectar tipo de proyecto
    project_types = []
    if (workspace_root / "requirements.txt").exists():
        project_types.append("Python")
    if (workspace_root / "package.json").exists():
        project_types.append("Node.js")
    if (workspace_root / ".git").exists():
        project_types.append("Git")
    
    if project_types:
        console.print(f"  • Tipo: {', '.join(project_types)}", style="blue")
    
    # Contar archivos
    try:
        py_files = list(workspace_root.rglob("*.py"))
        console.print(f"  • Archivos Python: {len(py_files)}", style="yellow")
    except:
        pass
    
    console.print()


def process_command(command: str, agent, workspace_root: Path) -> bool:
    """
    Procesa comandos especiales
    
    Returns:
        True si debe continuar, False si debe salir
    """
    command = command.strip().lower()
    
    if command in ["/exit", "/quit", "exit", "quit"]:
        console.print("\n👋 ¡Hasta luego!\n", style="bold cyan")
        return False
    
    elif command == "/help":
        show_help()
    
    elif command == "/clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        show_banner()
    
    elif command == "/tools":
        show_tools()
    
    elif command.startswith("/tools "):
        category = command.replace("/tools ", "")
        if TOOLS_AVAILABLE:
            try:
                categories = get_tools_by_category()
                if category in categories:
                    console.print(f"\n🔧 {category.replace('_', ' ').title()}:\n", style="bold green")
                    for tool in categories[category]:
                        console.print(f"  - {tool}")
                    console.print()
                else:
                    console.print(f"⚠️  Categoría no encontrada: {category}", style="yellow")
            except Exception as e:
                console.print(f"⚠️  Error: {e}", style="yellow")
    
    elif command == "/history":
        if agent and hasattr(agent, 'history'):
            console.print("\n📜 Historial de Conversación:\n", style="bold cyan")
            for i, msg in enumerate(agent.history[-10:], 1):  # Últimos 10
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]  # Primeros 100 chars
                console.print(f"{i}. [{role}]: {content}...", style="dim")
            console.print()
        else:
            console.print("⚠️  Sin historial disponible", style="yellow")
    
    elif command == "/reset":
        if agent and hasattr(agent, 'history'):
            agent.history = []
            if hasattr(agent, 'save_memory'):
                agent.save_memory()
            console.print("✅ Memoria reiniciada\n", style="green")
        else:
            console.print("⚠️  No se pudo reiniciar\n", style="yellow")
    
    elif command == "/context":
        show_context(workspace_root)
    
    elif command.startswith("/analyze "):
        file_path = command.replace("/analyze ", "").strip()
        console.print(f"🔍 Analizando: {file_path}", style="cyan")
        # TODO: Implementar análisis con herramientas
        if agent:
            try:
                # Leer archivo usando herramienta
                result = agent.execute_tool("read_file", file_path=file_path)
                if result.get("success"):
                    content = result.get("content", "")
                    console.print(f"\n📄 Contenido ({len(content)} caracteres):\n", style="green")
                    console.print(content[:500] + "..." if len(content) > 500 else content)
                    console.print()
                else:
                    console.print(f"⚠️  Error: {result.get('error')}", style="yellow")
            except Exception as e:
                console.print(f"⚠️  Error: {e}", style="yellow")
        else:
            console.print("⚠️  Agente no disponible\n", style="yellow")
    
    else:
        console.print(f"⚠️  Comando no reconocido: {command}", style="yellow")
        console.print("💡 Usa '/help' para ver comandos disponibles\n", style="dim")
    
    return True


def main():
    """Función principal"""
    # Obtener workspace root
    workspace_root = Path.cwd()
    
    # Mostrar banner
    show_banner()
    
    # Inicializar agente
    if PatAgent:
        try:
            # Modo debug temporal - puedes cambiar a False después
            agent = PatAgent(workspace_root=str(workspace_root), debug=True)
            console.print("✅ Agente inicializado correctamente", style="green")
            
            # Mostrar herramientas disponibles
            if agent.tools:
                console.print(f"✅ {len(agent.tools)} herramientas cargadas", style="green")
            else:
                console.print("⚠️  Sin herramientas disponibles", style="yellow")
            
            console.print()
        except Exception as e:
            console.print(f"⚠️  Error inicializando agente: {e}\n", style="yellow")
            agent = None
    else:
        console.print("⚠️  Ejecutando sin agente (modo limitado)\n", style="yellow")
        agent = None
    
    # Configurar prompt con historial
    history_file = Path.home() / ".patcode_history"
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
    )
    
    # Loop principal
    try:
        while True:
            try:
                # Obtener input
                user_input = session.prompt(
                    "Tú: ",
                    multiline=False,
                ).strip()
                
                if not user_input:
                    continue
                
                # Procesar comandos especiales
                if user_input.startswith('/'):
                    should_continue = process_command(user_input, agent, workspace_root)
                    if not should_continue:
                        break
                    continue
                
                # Procesar con el agente
                if agent:
                    try:
                        console.print()  # Línea en blanco
                        
                        # Mostrar indicador de procesamiento
                        with console.status("[bold cyan]🤔 Pensando...", spinner="dots"):
                            response = agent.ask(user_input)
                        
                        # Mostrar respuesta
                        console.print("PatCode:", style="bold green")
                        console.print(Markdown(response))
                        console.print()  # Línea en blanco
                    
                    except KeyboardInterrupt:
                        console.print("\n⚠️  Operación cancelada\n", style="yellow")
                        continue
                    except Exception as e:
                        console.print(f"\n❌ Error: {e}\n", style="bold red")
                        continue
                else:
                    console.print("\n⚠️  Agente no disponible. Usa comandos con '/'\n", style="yellow")
            
            except KeyboardInterrupt:
                console.print("\n💡 Usa '/exit' para salir o continúa escribiendo\n", style="dim")
                continue
    
    except (EOFError, KeyboardInterrupt):
        console.print("\n\n👋 ¡Hasta luego!\n", style="bold cyan")
    
    finally:
        # Guardar memoria si es posible
        if agent and hasattr(agent, 'save_memory'):
            try:
                agent.save_memory()
            except:
                pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n❌ Error fatal: {e}\n", style="bold red")
        import traceback
        traceback.print_exc()
        sys.exit(1)