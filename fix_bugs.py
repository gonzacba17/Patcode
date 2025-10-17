"""
Fix definitivo para el bug de LoadedFile en response_cache.py
"""
from pathlib import Path

def main():
    print("=" * 60)
    print("  🔧 Reparando response_cache.py")
    print("=" * 60)
    print()
    
    # 1. Detectar atributo correcto de LoadedFile
    print("[1/3] Analizando LoadedFile...")
    try:
        from agents.memory.models import LoadedFile
        import inspect
        
        # Obtener código fuente
        source = inspect.getsource(LoadedFile)
        print("✓ LoadedFile encontrado")
        
        # Detectar atributo correcto
        if 'path:' in source or 'path =' in source:
            attr = 'path'
        elif 'file_path:' in source:
            attr = 'file_path'
        elif 'filename:' in source:
            attr = 'filename'
        else:
            # Por defecto usar representación de string
            attr = None
            
        if attr:
            print(f"✓ Atributo detectado: {attr}")
            fix_line = f"'files': sorted([str(f.{attr}) for f in files_context])"
        else:
            print("✓ Usando conversión genérica")
            fix_line = "'files': sorted([str(f) for f in files_context])"
            
    except Exception as e:
        print(f"⚠ No se pudo analizar LoadedFile: {e}")
        print("✓ Aplicando fix genérico")
        fix_line = "'files': sorted([str(f) for f in files_context])"
    
    # 2. Aplicar fix
    print("\n[2/3] Aplicando fix...")
    cache_file = Path('utils/response_cache.py')
    
    if not cache_file.exists():
        print("❌ ERROR: No se encuentra utils/response_cache.py")
        return False
    
    content = cache_file.read_text(encoding='utf-8')
    
    # Buscar y reemplazar TODAS las variantes posibles
    variants = [
        "'files': sorted([f.name for f in files_context])",
        "'files': sorted([str(f.filepath) for f in files_context])",
        "'files': sorted([f.filepath for f in files_context])",
        "'files': sorted([str(f.path) for f in files_context])",
        "'files': sorted([f.path for f in files_context])",
    ]
    
    replaced = False
    for variant in variants:
        if variant in content:
            content = content.replace(variant, fix_line)
            replaced = True
            print(f"✓ Reemplazado: {variant[:50]}...")
    
    if not replaced:
        print("⚠ No se encontró línea para reemplazar")
        print("Buscando línea 36...")
        lines = content.split('\n')
        if len(lines) >= 36 and 'files' in lines[35]:
            print(f"Línea 36 actual: {lines[35].strip()}")
            # Reemplazar línea 36 directamente
            lines[35] = "        " + fix_line + ","
            content = '\n'.join(lines)
            replaced = True
            print("✓ Línea 36 reemplazada directamente")
    
    if replaced:
        # Guardar archivo
        cache_file.write_text(content, encoding='utf-8')
        print("✓ Archivo guardado")
    else:
        print("❌ No se pudo aplicar el fix")
        return False
    
    # 3. Verificar
    print("\n[3/3] Verificando fix...")
    new_content = cache_file.read_text(encoding='utf-8')
    if fix_line in new_content:
        print("✓ Fix verificado correctamente")
        print()
        print("=" * 60)
        print("  ✅ FIX COMPLETADO")
        print("=" * 60)
        print()
        print(f"Línea aplicada: {fix_line}")
        return True
    else:
        print("❌ La verificación falló")
        return False

if __name__ == "__main__":
    try:
        success = main()
        print()
        if success:
            print("✅ Ahora puedes ejecutar PatCode:")
            print("   python main.py")
        else:
            print("❌ El fix falló. Por favor reporta este error.")
        print()
        input("Presiona Enter para salir...")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")