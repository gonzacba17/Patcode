# test_imports.py - Archivo temporal para diagnosticar el problema

print("🔍 Probando imports...\n")

try:
    from tools.file_operations import FileOperations
    print("✅ FileOperations importado correctamente")
    
    # Probar instanciar
    file_ops = FileOperations(".")
    print(f"✅ FileOperations instanciado: {type(file_ops)}")
    print(f"   - base_path: {file_ops.base_path}")
    
except Exception as e:
    print(f"❌ Error con FileOperations: {e}")

print()

try:
    from tools.shell_operations import ShellOperations
    print("✅ ShellOperations importado correctamente")
    
    # Probar instanciar
    shell_ops = ShellOperations(".")
    print(f"✅ ShellOperations instanciado: {type(shell_ops)}")
    print(f"   - working_dir: {shell_ops.working_dir}")
    
except Exception as e:
    print(f"❌ Error con ShellOperations: {e}")

print()

try:
    from tools.git_operations import GitOperations
    print("✅ GitOperations importado correctamente")
    
    # Probar instanciar
    git_ops = GitOperations(".")
    print(f"✅ GitOperations instanciado: {type(git_ops)}")
    print(f"   - repo_path: {git_ops.repo_path}")
    
except Exception as e:
    print(f"❌ Error con GitOperations: {e}")
    import traceback
    traceback.print_exc()

print("\n✨ Diagnóstico completado")