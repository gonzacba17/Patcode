#!/usr/bin/env python3
"""
Test Phase 3 - Sistema Agentic y Code Analyzer

Script para testear el sistema completo de Fase 3.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.code_analyzer import CodeAnalyzer
from agents.orchestrator import AgenticOrchestrator
from llm.provider_manager import ProviderManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_code_analyzer():
    """Test del Code Analyzer."""
    print("\n" + "="*60)
    print("🧪 TESTING CODE ANALYZER")
    print("="*60)
    
    print("\n1️⃣ Test Python analysis:")
    
    test_file = "test_sample.py"
    test_code = '''
"""Sample module for testing"""

import os
from typing import List, Optional

class Calculator:
    """A simple calculator"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers"""
        result = a + b
        self.history.append(result)
        return result
    
    async def async_multiply(self, a: int, b: int) -> int:
        """Multiply two numbers asynchronously"""
        return a * b

def factorial(n: int) -> int:
    """Calculate factorial"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
    
    with open(test_file, "w") as f:
        f.write(test_code)
    
    try:
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(test_file)
        
        if result:
            print(f"✅ Language: {result.language}")
            print(f"✅ Lines of code: {result.lines_of_code}")
            print(f"✅ Classes found: {len(result.classes)}")
            for cls in result.classes:
                print(f"   - {cls.name} with {len(cls.methods)} methods")
            print(f"✅ Functions found: {len(result.functions)}")
            for func in result.functions:
                async_marker = " (async)" if func.is_async else ""
                print(f"   - {func.name}({', '.join(func.params)}){async_marker}")
            print(f"✅ Imports: {len(result.imports)}")
            for imp in result.imports[:3]:
                print(f"   - from {imp.module} import {', '.join(imp.names) if imp.names else '*'}")
            print(f"✅ Summary: {result.summary}")
        else:
            print("❌ Analysis failed")
    
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
    
    print("\n2️⃣ Test directory analysis:")
    results = analyzer.analyze_directory("agents", recursive=False)
    print(f"✅ Analyzed {len(results)} files")
    for file_path in list(results.keys())[:3]:
        print(f"   - {file_path}")


def test_prompts():
    """Test del sistema de prompts."""
    print("\n" + "="*60)
    print("🧪 TESTING PROMPT SYSTEM")
    print("="*60)
    
    from agents.prompts import planning, code_generation, debugging, testing, reflection
    
    print("\n1️⃣ Test planning prompt:")
    sys_prompt, user_prompt = planning.create_planning_prompt(
        task_description="Add a new feature to the calculator",
        project_context="Calculator class in calculator.py",
        recent_changes="None"
    )
    print(f"✅ System prompt length: {len(sys_prompt)} chars")
    print(f"✅ User prompt length: {len(user_prompt)} chars")
    
    print("\n2️⃣ Test code generation prompt:")
    sys_prompt, user_prompt = code_generation.create_code_generation_prompt(
        task_description="Create a divide method",
        context="Calculator class",
        existing_code="class Calculator: ...",
        requirements="Should handle division by zero",
        language="python"
    )
    print(f"✅ Generated prompt with {len(user_prompt)} chars")
    
    print("\n3️⃣ Test debugging prompt:")
    sys_prompt, user_prompt = debugging.create_debugging_prompt(
        error_message="ZeroDivisionError: division by zero",
        stack_trace="File calculator.py, line 42",
        relevant_code="result = a / b",
        context="Calculator division method"
    )
    print(f"✅ Generated debugging prompt")
    
    print("\n4️⃣ Test testing prompt:")
    sys_prompt, user_prompt = testing.create_testing_prompt(
        code_to_test="def add(a, b): return a + b",
        target_name="add",
        requirements="Test with positive, negative, and zero",
        framework="pytest"
    )
    print(f"✅ Generated testing prompt")
    
    print("\n5️⃣ Test reflection prompt:")
    sys_prompt, user_prompt = reflection.create_reflection_prompt(
        task_description="Add feature X",
        steps_completed="1. Analyzed code\n2. Generated code\n3. Wrote file",
        results="Feature implemented successfully",
        files_modified=["calculator.py"],
        test_results="All tests passed"
    )
    print(f"✅ Generated reflection prompt")
    
    print("\n✅ All prompts generated successfully")


def test_orchestrator():
    """Test del Orchestrator (requiere LLM configurado)."""
    print("\n" + "="*60)
    print("🧪 TESTING AGENTIC ORCHESTRATOR")
    print("="*60)
    
    try:
        import yaml
        
        if not os.path.exists("config.yaml"):
            print("⚠️  config.yaml not found, skipping orchestrator test")
            return
        
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        
        llm_manager = ProviderManager(config["llm"])
        
        available = llm_manager.get_available_providers()
        if not available:
            print("⚠️  No LLM providers available, skipping orchestrator test")
            return
        
        print(f"✅ Available providers: {available}")
        
        orchestrator = AgenticOrchestrator(
            llm_manager=llm_manager,
            project_root=".",
            max_iterations=2,
            enable_shell=True
        )
        
        print("\n1️⃣ Test simple analysis task:")
        task = orchestrator.execute_task(
            task_description="List all Python files in the agents/ directory",
            context={"target_directory": "agents"}
        )
        
        print(f"Status: {task.status.value}")
        print(f"Iterations: {task.iterations}")
        print(f"Steps executed: {len(task.steps)}")
        
        if task.status.value == "completed":
            print("✅ Task completed successfully")
        else:
            print(f"❌ Task failed: {task.error_message}")
        
        print("\nSteps:")
        for i, step in enumerate(task.steps, 1):
            status = "✅" if step.status.value == "completed" else "❌"
            print(f"{status} {i}. {step.description}")
        
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal."""
    print("\n🚀 PatCode - Test Suite Fase 3")
    print("Sistema Agentic y Code Analyzer\n")
    
    test_code_analyzer()
    
    test_prompts()
    
    test_orchestrator()
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETADOS")
    print("="*60)


if __name__ == "__main__":
    main()
