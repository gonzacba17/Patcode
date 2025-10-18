"""
Example - Uso del Orchestrator

Ejemplo de cómo usar el Orchestrator de PatCode para ejecutar tareas
de programación autónomas.
"""

import logging
from pathlib import Path

from agents.orchestrator import Orchestrator
from agents.llm_adapters.ollama_adapter import OllamaAdapter
from agents.llm_adapters.groq_adapter import GroqAdapter
from utils.logger import setup_logger


setup_logger("patcode", level=logging.INFO)
logger = logging.getLogger(__name__)


def example_with_ollama():
    """Ejemplo usando Ollama (modelo local)."""
    print("=" * 60)
    print("EJEMPLO 1: Orchestrator con Ollama")
    print("=" * 60)
    
    llm = OllamaAdapter(
        base_url="http://localhost:11434",
        model="qwen2.5-coder:1.5b",
        timeout=60
    )
    
    if not llm.is_available():
        print("❌ Ollama no está disponible")
        print("   Asegúrate de que esté corriendo: ollama serve")
        print("   Y descarga el modelo: ollama pull qwen2.5-coder:1.5b")
        return
    
    orchestrator = Orchestrator(
        llm_client=llm,
        workspace_root="."
    )
    
    task = "Lee el archivo setup.py y dime cuál es la versión del proyecto"
    
    print(f"\n📝 Tarea: {task}\n")
    
    result = orchestrator.execute_task(task, max_iterations=5)
    
    print(f"\n✅ Resultado:")
    print(result)
    
    print("\n📊 Estadísticas:")
    stats = orchestrator.get_stats()
    print(f"   Total de acciones: {stats['total_actions']}")
    print(f"   Archivos recientes: {stats['recent_files']}")


def example_with_groq():
    """Ejemplo usando Groq (API gratuita)."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Orchestrator con Groq")
    print("=" * 60)
    
    import os
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY no está configurada")
        print("   Configúrala en tu .env o exporta la variable de entorno")
        return
    
    llm = GroqAdapter(
        api_key=groq_api_key,
        model="llama-3.3-70b-versatile",
        timeout=30
    )
    
    if not llm.is_available():
        print("❌ Groq no está disponible")
        return
    
    orchestrator = Orchestrator(
        llm_client=llm,
        workspace_root="."
    )
    
    task = "Crea un archivo test_hello.py con una función hello_world() que retorne 'Hello, World!'"
    
    print(f"\n📝 Tarea: {task}\n")
    
    result = orchestrator.execute_task(task, max_iterations=5)
    
    print(f"\n✅ Resultado:")
    print(result)
    
    print("\n📊 Estadísticas:")
    stats = orchestrator.get_stats()
    print(f"   Total de acciones: {stats['total_actions']}")
    print(f"   Archivos recientes: {stats['recent_files']}")


def example_edit_file():
    """Ejemplo de edición de archivo."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Editar archivo con Orchestrator")
    print("=" * 60)
    
    llm = OllamaAdapter(
        base_url="http://localhost:11434",
        model="qwen2.5-coder:1.5b",
        timeout=60
    )
    
    if not llm.is_available():
        print("❌ Ollama no está disponible")
        return
    
    orchestrator = Orchestrator(
        llm_client=llm,
        workspace_root="."
    )
    
    task = "Añade un comentario docstring a la primera función que encuentres en config/settings.py"
    
    print(f"\n📝 Tarea: {task}\n")
    
    result = orchestrator.execute_task(task, max_iterations=10)
    
    print(f"\n✅ Resultado:")
    print(result)


def interactive_mode():
    """Modo interactivo para probar el Orchestrator."""
    print("\n" + "=" * 60)
    print("MODO INTERACTIVO - Orchestrator")
    print("=" * 60)
    
    llm = OllamaAdapter(
        base_url="http://localhost:11434",
        model="qwen2.5-coder:1.5b",
        timeout=60
    )
    
    if not llm.is_available():
        print("❌ Ollama no está disponible")
        print("   Iniciando con Ollama desconectado (algunas funciones no estarán disponibles)")
        return
    
    orchestrator = Orchestrator(
        llm_client=llm,
        workspace_root="."
    )
    
    print("\n🤖 Orchestrator listo. Escribe 'salir' para terminar.\n")
    
    while True:
        try:
            task = input("📝 Tarea: ").strip()
            
            if not task:
                continue
            
            if task.lower() in ["salir", "exit", "quit"]:
                print("👋 ¡Hasta luego!")
                break
            
            if task.lower() == "stats":
                stats = orchestrator.get_stats()
                print(f"\n📊 Estadísticas:")
                print(f"   Total de acciones: {stats['total_actions']}")
                print(f"   Tarea actual: {stats['current_task']}")
                print(f"   Archivos recientes: {stats['recent_files']}")
                print()
                continue
            
            if task.lower() == "clear":
                orchestrator.clear_history()
                print("✅ Historial limpiado\n")
                continue
            
            print()
            result = orchestrator.execute_task(task, max_iterations=10)
            
            print(f"\n✅ Resultado:")
            print(result)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por el usuario")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    import sys
    
    print("""
╔════════════════════════════════════════════════════════════╗
║          PatCode - Orchestrator Examples                  ║
║                                                            ║
║  Ejemplos de uso del sistema agentico                     ║
╚════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "ollama":
            example_with_ollama()
        elif mode == "groq":
            example_with_groq()
        elif mode == "edit":
            example_edit_file()
        elif mode == "interactive":
            interactive_mode()
        else:
            print(f"Modo desconocido: {mode}")
            print("Modos disponibles: ollama, groq, edit, interactive")
    else:
        print("Uso:")
        print("  python example_orchestrator.py ollama        - Ejemplo con Ollama")
        print("  python example_orchestrator.py groq          - Ejemplo con Groq")
        print("  python example_orchestrator.py edit          - Ejemplo de edición")
        print("  python example_orchestrator.py interactive   - Modo interactivo")
        print()
        
        response = input("¿Ejecutar modo interactivo? (s/n): ").strip().lower()
        if response == "s":
            interactive_mode()
        else:
            print("\n👋 Saliendo...")
