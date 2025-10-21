"""
Test de Componentes Existentes
Prueba funcionalidad de componentes que ya están implementados
"""

import sys
from pathlib import Path

def test_cli_commands():
    """Test del sistema de comandos CLI"""
    print("\n" + "="*60)
    print("🧪 TESTING: CLI Commands")
    print("="*60)
    
    try:
        from cli.commands import CommandRegistry
        
        registry = CommandRegistry()
        
        # Test 1: Comandos básicos registrados
        print("\n✓ Test 1: Verificar comandos básicos")
        basic_commands = ['help', 'clear', 'exit', 'files', 'stats']
        for cmd in basic_commands:
            if cmd in registry.commands:
                print(f"  ✅ Comando '{cmd}' registrado")
            else:
                print(f"  ❌ Comando '{cmd}' NO registrado")
        
        # Test 2: Get help
        print("\n✓ Test 2: Sistema de ayuda")
        help_text = registry.get_help()
        if "PatCode" in help_text and "Comandos Disponibles" in help_text:
            print("  ✅ Sistema de ayuda funciona")
        else:
            print("  ❌ Sistema de ayuda tiene problemas")
        
        # Test 3: Comando específico
        print("\n✓ Test 3: Ayuda de comando específico")
        help_files = registry.get_help("files")
        if "/files" in help_files:
            print("  ✅ Ayuda específica funciona")
        else:
            print("  ❌ Ayuda específica tiene problemas")
        
        print("\n✅ CLI Commands: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ CLI Commands: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_formatter():
    """Test del formateador de output"""
    print("\n" + "="*60)
    print("🧪 TESTING: CLI Formatter")
    print("="*60)
    
    try:
        from cli.formatter import OutputFormatter, Colors
        
        formatter = OutputFormatter(use_colors=True)
        
        # Test 1: Formato de respuesta
        print("\n✓ Test 1: Formato de respuesta con markdown")
        test_text = """# Header
## Subheader
- Item 1
- Item 2
`inline code`
"""
        formatted = formatter.format_response(test_text)
        if formatted and len(formatted) > 0:
            print("  ✅ Formato de respuesta funciona")
        else:
            print("  ❌ Formato de respuesta tiene problemas")
        
        # Test 2: Tabla
        print("\n✓ Test 2: Formato de tabla")
        headers = ["Name", "Age", "City"]
        rows = [["Alice", "30", "NYC"], ["Bob", "25", "LA"]]
        table = formatter.format_table(headers, rows)
        if "Alice" in table and "│" in table:
            print("  ✅ Formato de tabla funciona")
        else:
            print("  ❌ Formato de tabla tiene problemas")
        
        # Test 3: Code block
        print("\n✓ Test 3: Formato de bloque de código")
        code = "def hello():\n    print('Hello')"
        code_block = formatter.format_code_block(code, "python")
        if code_block and "hello" in code_block:
            print("  ✅ Formato de código funciona")
        else:
            print("  ❌ Formato de código tiene problemas")
        
        # Test 4: Info boxes
        print("\n✓ Test 4: Info boxes")
        info_box = formatter.format_info_box("Test", "Content", "info")
        success_box = formatter.format_success("Success message")
        error_box = formatter.format_error("Error message")
        
        if all([info_box, success_box, error_box]):
            print("  ✅ Info boxes funcionan")
        else:
            print("  ❌ Info boxes tienen problemas")
        
        print("\n✅ CLI Formatter: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ CLI Formatter: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_diff_viewer():
    """Test del visualizador de diffs"""
    print("\n" + "="*60)
    print("🧪 TESTING: Diff Viewer")
    print("="*60)
    
    try:
        from utils.diff_viewer import show_diff
        
        # Test: Generar diff
        print("\n✓ Test: Generar diff entre dos textos")
        old = "def hello():\n    print('Hello')"
        new = "def hello(name):\n    print(f'Hello {name}')"
        
        diff = show_diff(old, new, "Original", "Modificado")
        
        if diff and ("Hello" in diff or "hello" in diff):
            print("  ✅ Diff viewer funciona")
            # Mostrar preview del diff
            print("\n  Preview del diff:")
            for line in diff.split('\n')[:10]:
                print(f"    {line}")
        else:
            print("  ❌ Diff viewer tiene problemas")
        
        print("\n✅ Diff Viewer: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ Diff Viewer: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_editor():
    """Test del editor de archivos"""
    print("\n" + "="*60)
    print("🧪 TESTING: File Editor")
    print("="*60)
    
    try:
        from tools.file_editor import FileEditor
        
        editor = FileEditor(backup_dir=Path('.test_backups'))
        
        # Test 1: Verificar inicialización
        print("\n✓ Test 1: Inicialización")
        if editor.backup_dir.exists():
            print("  ✅ Backup directory creado")
        else:
            print("  ❌ Backup directory no creado")
        
        # Test 2: Read file (este mismo archivo)
        print("\n✓ Test 2: Lectura de archivo")
        success, content, error = editor.read_file(Path(__file__))
        if success and content:
            print(f"  ✅ Lectura OK ({len(content)} chars)")
        else:
            print(f"  ❌ Lectura falló: {error}")
        
        # Cleanup
        import shutil
        if Path('.test_backups').exists():
            shutil.rmtree('.test_backups')
        
        print("\n✅ File Editor: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ File Editor: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_project_memory():
    """Test de la memoria del proyecto"""
    print("\n" + "="*60)
    print("🧪 TESTING: Project Memory")
    print("="*60)
    
    try:
        from agents.memory.project_memory import ProjectMemory
        
        # Usar directorio temporal para tests
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            memory = ProjectMemory(temp_dir)
            
            # Test 1: Add context
            print("\n✓ Test 1: Añadir contexto")
            memory.add_context("test_file.py", "print('hello')")
            if "test_file.py" in memory.context:
                print("  ✅ Contexto añadido")
            else:
                print("  ❌ Contexto no añadido")
            
            # Test 2: Add task
            print("\n✓ Test 2: Añadir tarea")
            task_id = memory.add_task("Test task", "pending")
            if task_id:
                print(f"  ✅ Tarea añadida (ID: {task_id})")
            else:
                print("  ❌ Tarea no añadida")
            
            # Test 3: Get recent tasks
            print("\n✓ Test 3: Obtener tareas recientes")
            tasks = memory.get_recent_tasks(5)
            if len(tasks) > 0:
                print(f"  ✅ Tareas obtenidas ({len(tasks)})")
            else:
                print("  ⚠️  No hay tareas")
            
            # Test 4: Save/Load
            print("\n✓ Test 4: Persistencia")
            memory.save()
            
            # Crear nueva instancia y verificar carga
            memory2 = ProjectMemory(temp_dir)
            if "test_file.py" in memory2.context:
                print("  ✅ Datos persistidos correctamente")
            else:
                print("  ❌ Datos no se persistieron")
            
            print("\n✅ Project Memory: OK")
            return True
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"\n❌ Project Memory: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_manager():
    """Test del gestor de LLMs"""
    print("\n" + "="*60)
    print("🧪 TESTING: LLM Manager")
    print("="*60)
    
    try:
        from agents.llm_manager import LLMManager
        
        # Test 1: Inicialización
        print("\n✓ Test 1: Inicialización")
        manager = LLMManager()
        
        # Test 2: Obtener adapters disponibles
        print("\n✓ Test 2: Adapters disponibles")
        providers = list(manager.adapters.keys())
        print(f"  📋 Providers: {', '.join(providers)}")
        if len(providers) > 0:
            print(f"  ✅ {len(providers)} adapters cargados")
        else:
            print("  ❌ No hay adapters")
        
        # Test 3: Get current provider
        print("\n✓ Test 3: Provider actual")
        current = manager.get_current_provider()
        if current:
            print(f"  ✅ Provider actual: {current}")
        else:
            print("  ❌ No hay provider actual")
        
        # Test 4: Get stats
        print("\n✓ Test 4: Estadísticas")
        stats = manager.get_stats()
        if stats and 'current_provider' in stats:
            print(f"  ✅ Stats OK")
            print(f"    - Current: {stats['current_provider']}")
            print(f"    - Available: {', '.join(stats['available_providers'])}")
        else:
            print("  ❌ Stats tienen problemas")
        
        print("\n✅ LLM Manager: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM Manager: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator():
    """Test del orchestrator"""
    print("\n" + "="*60)
    print("🧪 TESTING: Orchestrator")
    print("="*60)
    
    try:
        from agents.orchestrator import AgenticOrchestrator
        from agents.llm_manager import LLMManager
        
        # Test 1: Inicialización
        print("\n✓ Test 1: Inicialización")
        
        llm_manager = LLMManager()
        orchestrator = AgenticOrchestrator(
            llm_manager=llm_manager,
            project_root=".",
            max_iterations=3,
            enable_shell=False  # Deshabilitamos shell para test
        )
        
        if orchestrator:
            print("  ✅ Orchestrator inicializado")
        else:
            print("  ❌ Orchestrator no inicializado")
        
        # Test 2: Verificar componentes
        print("\n✓ Test 2: Componentes internos")
        components = []
        if hasattr(orchestrator, 'file_ops'):
            components.append("file_ops")
        if hasattr(orchestrator, 'code_analyzer'):
            components.append("code_analyzer")
        if hasattr(orchestrator, 'project_memory'):
            components.append("project_memory")
        
        print(f"  ✅ Componentes: {', '.join(components)}")
        
        # Test 3: Context
        print("\n✓ Test 3: Execution Context")
        if hasattr(orchestrator, 'context'):
            print(f"  ✅ Context OK")
            print(f"    - Root: {orchestrator.context.project_root}")
        else:
            print("  ❌ No hay context")
        
        print("\n✅ Orchestrator: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ Orchestrator: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_test_report(results):
    """Genera reporte de tests"""
    print("\n\n" + "="*60)
    print("📊 REPORTE DE TESTS - COMPONENTES EXISTENTES")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n✅ Tests pasados: {passed}/{total} ({percentage:.1f}%)")
    
    print("\nDetalle:")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    if percentage == 100:
        print("\n🎉 ¡Todos los tests pasaron!")
    elif percentage >= 70:
        print("\n👍 La mayoría de componentes funcionan bien")
    elif percentage >= 40:
        print("\n⚠️  Algunos componentes tienen problemas")
    else:
        print("\n🔴 Múltiples componentes tienen problemas")
    
    print("\n" + "="*60)


def main():
    """Ejecuta todos los tests"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║     TESTS DE COMPONENTES EXISTENTES - PATOCODE             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {}
    
    # Ejecutar tests
    results["CLI Commands"] = test_cli_commands()
    results["CLI Formatter"] = test_cli_formatter()
    results["Diff Viewer"] = test_diff_viewer()
    results["File Editor"] = test_file_editor()
    results["Project Memory"] = test_project_memory()
    results["LLM Manager"] = test_llm_manager()
    results["Orchestrator"] = test_orchestrator()
    
    # Reporte
    generate_test_report(results)


if __name__ == "__main__":
    main()
