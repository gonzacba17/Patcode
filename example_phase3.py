"""
Example Phase 3 - Uso del Sistema Agentic

Ejemplo simple de cómo usar el AgenticOrchestrator.
"""

import os
import logging
from agents.orchestrator import AgenticOrchestrator
from llm.provider_manager import ProviderManager


logging.basicConfig(level=logging.INFO)


def load_config():
    """Carga configuración desde config.yaml."""
    try:
        import yaml
        
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        
        for provider_name, provider_config in config["llm"]["providers"].items():
            if "api_key" in provider_config and provider_config["api_key"].startswith("${"):
                env_var = provider_config["api_key"][2:-1]
                provider_config["api_key"] = os.getenv(env_var)
        
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def example_simple_task():
    """Ejemplo de tarea simple."""
    print("\n" + "="*60)
    print("EJEMPLO: Tarea Simple de Análisis")
    print("="*60)
    
    config = load_config()
    if not config:
        return
    
    llm_manager = ProviderManager(config["llm"])
    
    available = llm_manager.get_available_providers()
    print(f"\n✅ Providers disponibles: {available}")
    
    if not available:
        print("❌ No hay providers disponibles")
        print("   Asegúrate de:")
        print("   - Ollama: ollama serve")
        print("   - Groq: export GROQ_API_KEY=your_key")
        return
    
    orchestrator = AgenticOrchestrator(
        llm_manager=llm_manager,
        project_root=".",
        max_iterations=3
    )
    
    print("\n📋 Tarea: Analizar la estructura del directorio agents/")
    print("🚀 Iniciando ejecución...\n")
    
    task = orchestrator.execute_task(
        task_description="Analyze all Python files in the agents/ directory and provide a summary of the main components",
        context={"target_directory": "agents"}
    )
    
    print("\n" + "="*60)
    print("RESULTADOS")
    print("="*60)
    print(f"✅ Status: {task.status.value}")
    print(f"⏱️ Duration: {task.duration:.2f}s" if task.duration else "N/A")
    print(f"🔄 Iterations: {task.iterations}")
    print(f"📝 Steps: {len(task.steps)}")
    
    if task.status.value == "completed":
        print("\n✅ Tarea completada exitosamente!")
    else:
        print(f"\n❌ Tarea falló: {task.error_message}")
    
    print("\n📊 Pasos ejecutados:")
    for i, step in enumerate(task.steps, 1):
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "in_progress": "⏳",
            "pending": "⏸️"
        }.get(step.status.value, "❓")
        
        print(f"{status_emoji} {i}. {step.description}")
        if step.result:
            print(f"   Resultado: {str(step.result)[:100]}...")
    
    print("\n📁 Contexto de ejecución:")
    print(orchestrator.context.to_summary())


def example_code_generation():
    """Ejemplo de generación de código."""
    print("\n" + "="*60)
    print("EJEMPLO: Generación de Código")
    print("="*60)
    
    config = load_config()
    if not config:
        return
    
    llm_manager = ProviderManager(config["llm"])
    orchestrator = AgenticOrchestrator(
        llm_manager=llm_manager,
        project_root=".",
        max_iterations=5
    )
    
    print("\n📋 Tarea: Crear un módulo de utilidades matemáticas")
    print("🚀 Iniciando ejecución...\n")
    
    task = orchestrator.execute_task(
        task_description="""
        Create a Python module called 'math_utils.py' with:
        1. A function is_prime(n) that checks if a number is prime
        2. A function fibonacci(n) that returns the nth Fibonacci number
        Include proper docstrings and type hints.
        """,
        context={"language": "python"}
    )
    
    print("\n" + "="*60)
    print("RESULTADOS")
    print("="*60)
    print(f"Status: {task.status.value}")
    print(f"Duration: {task.duration:.2f}s" if task.duration else "N/A")
    
    if orchestrator.context.files_modified:
        print(f"\n📁 Archivos creados/modificados:")
        for file in orchestrator.context.files_modified:
            print(f"   - {file}")
            
            if os.path.exists(file):
                print(f"\n📄 Contenido de {file}:")
                print("-" * 60)
                with open(file, "r") as f:
                    print(f.read())
                print("-" * 60)
                
                cleanup = input("\n🧹 ¿Eliminar archivo de prueba? (s/n): ")
                if cleanup.lower() == 's':
                    os.remove(file)
                    print(f"✅ {file} eliminado")


def main():
    """Función principal."""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║              🤖 PatCode - Fase 3 Examples 🤖               ║
║                                                            ║
║                  Sistema Agentic Completo                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
    
    ejemplos = [
        ("1", "Análisis Simple", example_simple_task),
        ("2", "Generación de Código", example_code_generation),
        ("q", "Salir", None)
    ]
    
    while True:
        print("\n" + "="*60)
        print("SELECCIONA UN EJEMPLO:")
        print("="*60)
        
        for key, name, _ in ejemplos:
            print(f"  {key}. {name}")
        
        choice = input("\nTu elección: ").strip().lower()
        
        if choice == 'q':
            print("\n👋 ¡Hasta luego!")
            break
        
        ejemplo_func = next((func for k, _, func in ejemplos if k == choice), None)
        
        if ejemplo_func:
            try:
                ejemplo_func()
                input("\nPresiona Enter para continuar...")
            except KeyboardInterrupt:
                print("\n\n⏸️ Ejemplo interrumpido")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                input("\nPresiona Enter para continuar...")
        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Adiós!")
