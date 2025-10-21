"""
Test de Auditoría - Fase 4
Evalúa qué componentes de Fase 4 están implementados y su estado
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

class Fase4Auditor:
    """Auditor del estado de implementación de Fase 4"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {
            'implemented': [],
            'partial': [],
            'missing': [],
            'errors': []
        }
        
    def check_file_exists(self, filepath: str) -> bool:
        """Verifica si un archivo existe"""
        return (self.project_root / filepath).exists()
    
    def check_class_in_file(self, filepath: str, class_name: str) -> Tuple[bool, str]:
        """Verifica si una clase está definida en un archivo"""
        try:
            if not self.check_file_exists(filepath):
                return False, "File not found"
            
            with open(self.project_root / filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if f"class {class_name}" in content:
                    return True, "Found"
                return False, "Class not found"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_function_in_file(self, filepath: str, func_name: str) -> Tuple[bool, str]:
        """Verifica si una función está definida en un archivo"""
        try:
            if not self.check_file_exists(filepath):
                return False, "File not found"
            
            with open(self.project_root / filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if f"def {func_name}" in content:
                    return True, "Found"
                return False, "Function not found"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_import_available(self, module_name: str) -> Tuple[bool, str]:
        """Verifica si un módulo Python está disponible"""
        try:
            __import__(module_name)
            return True, "Available"
        except ImportError as e:
            return False, f"Not installed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def audit_context_manager(self):
        """Audita Context Manager"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Context Manager")
        print("="*60)
        
        checks = [
            ("File exists", "agents/context_manager.py"),
            ("ContextManager class", "agents/context_manager.py", "ContextManager"),
            ("ContextItem class", "agents/context_manager.py", "ContextItem"),
            ("count_tokens method", "agents/context_manager.py", "count_tokens"),
            ("add_message method", "agents/context_manager.py", "add_message"),
            ("_prune_context method", "agents/context_manager.py", "_prune_context"),
        ]
        
        score = 0
        total = len(checks)
        
        for check in checks:
            if check[0] == "File exists":
                exists = self.check_file_exists(check[1])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[1]}")
                if exists:
                    score += 1
            else:
                exists, msg = self.check_class_in_file(check[1], check[2]) if "class" in check[0] else \
                             self.check_function_in_file(check[1], check[2])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[2]} - {msg}")
                if exists:
                    score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        if percentage == 100:
            self.results['implemented'].append(("Context Manager", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Context Manager", score, total))
        else:
            self.results['missing'].append(("Context Manager", score, total))
    
    def audit_multi_file_editor(self):
        """Audita Multi-file Editor"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Multi-file Editor")
        print("="*60)
        
        checks = [
            ("File exists", "tools/multi_file_editor.py"),
            ("MultiFileEditor class", "tools/multi_file_editor.py", "MultiFileEditor"),
            ("FileEdit class", "tools/multi_file_editor.py", "FileEdit"),
            ("EditTransaction class", "tools/multi_file_editor.py", "EditTransaction"),
            ("begin_transaction method", "tools/multi_file_editor.py", "begin_transaction"),
            ("commit method", "tools/multi_file_editor.py", "commit"),
            ("rollback method", "tools/multi_file_editor.py", "rollback"),
        ]
        
        score = 0
        total = len(checks)
        
        for check in checks:
            if check[0] == "File exists":
                exists = self.check_file_exists(check[1])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[1]}")
                if exists:
                    score += 1
            else:
                exists, msg = self.check_class_in_file(check[1], check[2]) if "class" in check[0] else \
                             self.check_function_in_file(check[1], check[2])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[2]} - {msg}")
                if exists:
                    score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        if percentage == 100:
            self.results['implemented'].append(("Multi-file Editor", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Multi-file Editor", score, total))
        else:
            self.results['missing'].append(("Multi-file Editor", score, total))
    
    def audit_diff_engine(self):
        """Audita Diff Engine"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Diff Engine")
        print("="*60)
        
        checks = [
            ("File exists", "tools/diff_engine.py"),
            ("DiffEngine class", "tools/diff_engine.py", "DiffEngine"),
            ("FileDiff class", "tools/diff_engine.py", "FileDiff"),
            ("generate_diff method", "tools/diff_engine.py", "generate_diff"),
            ("apply_patch method", "tools/diff_engine.py", "apply_patch"),
            ("undo method", "tools/diff_engine.py", "undo"),
            ("redo method", "tools/diff_engine.py", "redo"),
        ]
        
        score = 0
        total = len(checks)
        
        for check in checks:
            if check[0] == "File exists":
                exists = self.check_file_exists(check[1])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[1]}")
                if exists:
                    score += 1
            else:
                exists, msg = self.check_class_in_file(check[1], check[2]) if "class" in check[0] else \
                             self.check_function_in_file(check[1], check[2])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[2]} - {msg}")
                if exists:
                    score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        # Nota: diff_viewer.py ya existe, es similar
        if self.check_file_exists("utils/diff_viewer.py"):
            print("\n💡 NOTA: utils/diff_viewer.py ya existe (similar)")
            score += 2  # Bonus por componente similar existente
        
        if percentage == 100:
            self.results['implemented'].append(("Diff Engine", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Diff Engine", score, total))
        else:
            self.results['missing'].append(("Diff Engine", score, total))
    
    def audit_conversation_memory(self):
        """Audita Conversation Memory"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Conversation Memory")
        print("="*60)
        
        checks = [
            ("File exists", "agents/memory/conversation_memory.py"),
            ("ConversationMemory class", "agents/memory/conversation_memory.py", "ConversationMemory"),
            ("ConversationSession class", "agents/memory/conversation_memory.py", "ConversationSession"),
            ("Message class", "agents/memory/conversation_memory.py", "Message"),
            ("create_session method", "agents/memory/conversation_memory.py", "create_session"),
            ("save_session method", "agents/memory/conversation_memory.py", "save_session"),
            ("search method", "agents/memory/conversation_memory.py", "search"),
        ]
        
        score = 0
        total = len(checks)
        
        for check in checks:
            if check[0] == "File exists":
                exists = self.check_file_exists(check[1])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[1]}")
                if exists:
                    score += 1
            else:
                exists, msg = self.check_class_in_file(check[1], check[2]) if "class" in check[0] else \
                             self.check_function_in_file(check[1], check[2])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[2]} - {msg}")
                if exists:
                    score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        # Nota: project_memory.py ya existe
        if self.check_file_exists("agents/memory/project_memory.py"):
            print("\n💡 NOTA: agents/memory/project_memory.py ya existe (similar)")
            score += 1
        
        if percentage == 100:
            self.results['implemented'].append(("Conversation Memory", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Conversation Memory", score, total))
        else:
            self.results['missing'].append(("Conversation Memory", score, total))
    
    def audit_rich_interface(self):
        """Audita Rich Interface"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Rich Interface")
        print("="*60)
        
        checks = [
            ("File exists", "cli/rich_interface.py"),
            ("RichInterface class", "cli/rich_interface.py", "RichInterface"),
            ("print_header method", "cli/rich_interface.py", "print_header"),
            ("print_table method", "cli/rich_interface.py", "print_table"),
            ("print_code method", "cli/rich_interface.py", "print_code"),
            ("create_progress method", "cli/rich_interface.py", "create_progress"),
        ]
        
        score = 0
        total = len(checks)
        
        for check in checks:
            if check[0] == "File exists":
                exists = self.check_file_exists(check[1])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[1]}")
                if exists:
                    score += 1
            else:
                exists, msg = self.check_class_in_file(check[1], check[2]) if "class" in check[0] else \
                             self.check_function_in_file(check[1], check[2])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[2]} - {msg}")
                if exists:
                    score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        # Nota: formatter.py ya existe con funcionalidad similar
        if self.check_file_exists("cli/formatter.py"):
            print("\n💡 NOTA: cli/formatter.py ya existe (similar, sin Rich)")
            score += 2
        
        if percentage == 100:
            self.results['implemented'].append(("Rich Interface", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Rich Interface", score, total))
        else:
            self.results['missing'].append(("Rich Interface", score, total))
    
    def audit_interactive_mode(self):
        """Audita Interactive Mode"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Interactive Mode")
        print("="*60)
        
        checks = [
            ("File exists", "cli/interactive.py"),
            ("InteractiveMode class", "cli/interactive.py", "InteractiveMode"),
            ("run method", "cli/interactive.py", "run"),
            ("setup_readline method", "cli/interactive.py", "setup_readline"),
            ("complete method", "cli/interactive.py", "complete"),
            ("execute_task method", "cli/interactive.py", "execute_task"),
        ]
        
        score = 0
        total = len(checks)
        
        for check in checks:
            if check[0] == "File exists":
                exists = self.check_file_exists(check[1])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[1]}")
                if exists:
                    score += 1
            else:
                exists, msg = self.check_class_in_file(check[1], check[2]) if "class" in check[0] else \
                             self.check_function_in_file(check[1], check[2])
                status = "✅" if exists else "❌"
                print(f"{status} {check[0]}: {check[2]} - {msg}")
                if exists:
                    score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        if percentage == 100:
            self.results['implemented'].append(("Interactive Mode", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Interactive Mode", score, total))
        else:
            self.results['missing'].append(("Interactive Mode", score, total))
    
    def audit_dependencies(self):
        """Audita dependencias requeridas"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Dependencias")
        print("="*60)
        
        deps = [
            ("rich", "Rich library"),
            ("tiktoken", "Tiktoken (token counting)"),
            ("prompt_toolkit", "Prompt toolkit"),
            ("readline", "Readline (built-in)"),
        ]
        
        score = 0
        total = len(deps)
        
        for module, desc in deps:
            exists, msg = self.check_import_available(module)
            status = "✅" if exists else "❌"
            print(f"{status} {desc}: {msg}")
            if exists:
                score += 1
        
        percentage = (score / total) * 100
        print(f"\n📊 Score: {score}/{total} ({percentage:.1f}%)")
        
        if percentage == 100:
            self.results['implemented'].append(("Dependencies", score, total))
        elif percentage > 0:
            self.results['partial'].append(("Dependencies", score, total))
        else:
            self.results['missing'].append(("Dependencies", score, total))
    
    def audit_existing_components(self):
        """Audita componentes similares ya existentes"""
        print("\n" + "="*60)
        print("🔍 AUDITANDO: Componentes Existentes (Similares)")
        print("="*60)
        
        existing = [
            ("cli/commands.py", "Command Registry (YA EXISTE)"),
            ("cli/formatter.py", "Output Formatter (YA EXISTE)"),
            ("utils/diff_viewer.py", "Diff Viewer (YA EXISTE)"),
            ("tools/file_editor.py", "File Editor con backup (YA EXISTE)"),
            ("agents/memory/project_memory.py", "Project Memory (YA EXISTE)"),
        ]
        
        score = 0
        total = len(existing)
        
        for filepath, desc in existing:
            exists = self.check_file_exists(filepath)
            status = "✅" if exists else "❌"
            print(f"{status} {desc}")
            if exists:
                score += 1
        
        print(f"\n📊 Score: {score}/{total} ({score * 100 / total:.1f}%)")
        print("\n💡 Estos componentes pueden ser base para Fase 4")
    
    def generate_report(self):
        """Genera reporte final"""
        print("\n\n" + "="*60)
        print("📊 REPORTE FINAL - FASE 4")
        print("="*60)
        
        print("\n✅ IMPLEMENTADOS COMPLETAMENTE:")
        if self.results['implemented']:
            for name, score, total in self.results['implemented']:
                print(f"  ✓ {name}: {score}/{total}")
        else:
            print("  (ninguno)")
        
        print("\n🟡 PARCIALMENTE IMPLEMENTADOS:")
        if self.results['partial']:
            for name, score, total in self.results['partial']:
                percentage = (score / total) * 100
                print(f"  • {name}: {score}/{total} ({percentage:.1f}%)")
        else:
            print("  (ninguno)")
        
        print("\n❌ FALTANTES:")
        if self.results['missing']:
            for name, score, total in self.results['missing']:
                print(f"  ✗ {name}: {score}/{total}")
        else:
            print("  (ninguno)")
        
        # Calcular score total
        all_components = self.results['implemented'] + self.results['partial'] + self.results['missing']
        if all_components:
            total_score = sum(score for _, score, _ in all_components)
            total_possible = sum(total for _, _, total in all_components)
            overall_percentage = (total_score / total_possible) * 100
            
            print(f"\n🎯 PROGRESO TOTAL: {total_score}/{total_possible} ({overall_percentage:.1f}%)")
            
            if overall_percentage >= 80:
                status = "🟢 EXCELENTE"
            elif overall_percentage >= 50:
                status = "🟡 BUENO"
            elif overall_percentage >= 25:
                status = "🟠 EN PROGRESO"
            else:
                status = "🔴 INICIAL"
            
            print(f"📈 ESTADO: {status}")
        
        print("\n" + "="*60)
        
        # Recomendaciones
        print("\n💡 RECOMENDACIONES:")
        
        if not self.results['implemented']:
            print("  1. Instalar dependencias faltantes: pip install tiktoken")
            print("  2. Crear archivos base de Fase 4 según el prompt")
            print("  3. Aprovechar componentes existentes similares")
        
        if 'tiktoken' in str(self.results):
            print("  • Instalar tiktoken: pip3 install tiktoken")
        
        print("  • cli/commands.py y cli/formatter.py ya existen - buen punto de partida")
        print("  • utils/diff_viewer.py puede servir como base para diff_engine.py")
        print("  • tools/file_editor.py tiene backup/rollback - reutilizable")
    
    def run_full_audit(self):
        """Ejecuta auditoría completa"""
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║          AUDITORÍA FASE 4 - PATOCODE/AETHERMIND           ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        self.audit_dependencies()
        self.audit_context_manager()
        self.audit_multi_file_editor()
        self.audit_diff_engine()
        self.audit_conversation_memory()
        self.audit_rich_interface()
        self.audit_interactive_mode()
        self.audit_existing_components()
        
        self.generate_report()


def main():
    auditor = Fase4Auditor()
    auditor.run_full_audit()


if __name__ == "__main__":
    main()
