#!/usr/bin/env python3
"""Script para identificar y marcar tests problemáticos"""

import os
from pathlib import Path

TESTS_DIR = Path("tests")

# Tests con problemas conocidos
PROBLEMATIC_TESTS = {
    "test_rich_ui.py": "ui",
    "test_integration.py": "integration",
    "test_tools.py": "obsolete",
    "test_safety_shell_file.py": "obsolete",
    "test_rag_system.py": "requires_ollama",
    "test_git_plugin.py": "integration",
}

def add_marker_to_file(filepath: Path, marker: str):
    """Agrega marker pytest al archivo"""
    
    content = filepath.read_text(encoding='utf-8')
    
    # Si ya tiene el marker, skip
    if f"@pytest.mark.{marker}" in content:
        return False
    
    # Buscar primera función de test
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith("def test_") or line.strip().startswith("class Test"):
            # Insertar marker antes de la función/clase
            indent = len(line) - len(line.lstrip())
            lines.insert(i, " " * indent + f"@pytest.mark.{marker}")
            modified = True
            break
    
    if modified:
        filepath.write_text('\n'.join(lines), encoding='utf-8')
        return True
    
    return False

def main():
    """Procesa todos los tests problemáticos"""
    
    print("🔧 Marcando tests problemáticos...\n")
    
    for test_file, marker in PROBLEMATIC_TESTS.items():
        filepath = TESTS_DIR / test_file
        
        if not filepath.exists():
            print(f"⚠️  {test_file} no existe")
            continue
        
        if add_marker_to_file(filepath, marker):
            print(f"✅ {test_file} → marcado como @pytest.mark.{marker}")
        else:
            print(f"ℹ️  {test_file} → ya tiene marker")
    
    print("\n✅ Proceso completado!")
    print("\nAhora puedes ejecutar:")
    print("  pytest -m 'not obsolete'  # Skip tests obsoletos")
    print("  pytest -m 'not ui'        # Skip tests de UI")
    print("  pytest -m unit            # Solo tests unitarios")

if __name__ == "__main__":
    main()