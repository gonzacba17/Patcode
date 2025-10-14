"""
PatCode - Asistente de programación local con capacidades de agente autónomo
"""

from agents.tool_agent import ToolAgent
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import sys


def print_welcome():
    """Muestra mensaje de bienvenida"""
    console = Console()
    
    welcome_text = """
# 🤖 PatCode - Asistente de Programación Local

**Capacidades actuales:**
- 📖 Leer y analizar archivos
- ✏️ Editar y crear archivos
- 🔧 Ejecutar comandos y tests
- 🔀 Operaciones Git (status, diff, commit)
- 🧠 Memoria de conversación

**Comandos especiales:**
- `exit`, `quit`, `salir`: Salir del asistente
- `reset`: Reiniciar conversación
- `help`: Mostrar esta ayuda

**Ejemplos de uso:**
```
"Lee el archivo main.py y explícame qué hace"
"Crea un archivo test_example.py con un test básico"
"Ejecuta los tests y dime si pasan"
"Muestra el status de git"
"Haz un commit con mensaje 'feat: add new feature'"
```
    """
    
    console.print(Panel(Markdown(welcome_text), border_style="cyan"))


def main():
    """Función principal del asistente"""
    console = Console()
    
    # Mostrar bienvenida
    print_welcome()
    
    # Inicializar agente
    console.print("\n[yellow]Inicializando PatCode...[/yellow]")
    
    try:
        agent = ToolAgent(
            model="qwen2.5-coder:14b",  # Cambiar por el modelo que tengas
            project_path="."
        )
        console.print("[green]✓ PatCode listo para usar[/green]\n")
    except Exception as e:
        console.print(f"[red]Error al inicializar: {e}[/red]")
        console.print("[yellow]Verifica que Ollama esté corriendo: ollama serve[/yellow]")
        sys.exit(1)
    
    # Loop principal
    while True:
        try:
            # Obtener input del usuario
            user_input = console.input("\n[bold cyan]Tú >[/bold cyan] ")
            
            # Comandos especiales
            if user_input.lower() in ["exit", "quit", "salir"]:
                console.print("\n[yellow]👋 Hasta luego![/yellow]")
                break
            
            if user_input.lower() == "reset":
                agent.reset_conversation()
                continue
            
            if user_input.lower() == "help":
                print_welcome()
                continue
            
            if not user_input.strip():
                continue
            
            # Procesar mensaje
            response = agent.ask(user_input)
            
            # Mostrar respuesta
            console.print(f"\n[bold green]PatCode >[/bold green] {response}")
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Hasta luego![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()