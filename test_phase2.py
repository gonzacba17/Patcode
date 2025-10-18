#!/usr/bin/env python3
"""
Test Phase 2 - Sistema Multi-LLM y Shell Executor

Script para testear el sistema Multi-LLM y Shell Executor de PatCode.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.provider_manager import ProviderManager
from tools.shell_executor import ShellExecutor


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_config():
    """Carga la configuración desde config.yaml."""
    try:
        import yaml
        
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        
        for provider_name, provider_config in config["llm"]["providers"].items():
            if "api_key" in provider_config and provider_config["api_key"].startswith("${"):
                env_var = provider_config["api_key"][2:-1]
                provider_config["api_key"] = os.getenv(env_var)
        
        return config
    except ImportError:
        print("❌ PyYAML not installed. Install it with: pip install pyyaml")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)


def test_llm_system():
    """Test del sistema Multi-LLM."""
    print("\n" + "="*60)
    print("🧪 TESTING SISTEMA MULTI-LLM")
    print("="*60)
    
    config = load_config()
    
    try:
        manager = ProviderManager(config["llm"])
    except Exception as e:
        print(f"❌ Error initializing ProviderManager: {e}")
        return
    
    print("\n1️⃣ Verificando providers disponibles:")
    available = manager.get_available_providers()
    print(f"✅ Providers disponibles: {available}")
    
    if not available:
        print("⚠️  No hay providers disponibles. Asegúrate de:")
        print("   - Ollama: ollama serve")
        print("   - Groq: export GROQ_API_KEY=your_key")
        return
    
    print("\n2️⃣ Test query simple (estrategia: simple):")
    try:
        response = manager.generate(
            prompt="Say hello in one word",
            strategy="simple"
        )
        print(f"✅ Provider: {response.provider}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Response: {response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n3️⃣ Test query compleja (estrategia: complex):")
    try:
        response = manager.generate(
            prompt="Explain what is a closure in JavaScript with a simple example",
            strategy="complex"
        )
        print(f"✅ Provider: {response.provider}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Tokens used: {response.tokens_used}")
        print(f"✅ Response (first 200 chars): {response.content[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n4️⃣ Status de providers:")
    status = manager.get_status()
    for provider, info in status.items():
        print(f"  {provider}:")
        print(f"    Available: {info.get('available', 'N/A')}")
        print(f"    Model: {info.get('model', 'N/A')}")
        rate_limit = info.get('rate_limit', {})
        if rate_limit.get('has_limit'):
            print(f"    Rate limit: {rate_limit}")


def test_shell_executor():
    """Test del Shell Executor."""
    print("\n" + "="*60)
    print("🧪 TESTING SHELL EXECUTOR")
    print("="*60)
    
    executor = ShellExecutor(working_dir=".")
    
    print("\n1️⃣ Test comando seguro (python --version):")
    try:
        result = executor.execute("python --version")
        print(f"✅ Exit code: {result.exit_code}")
        print(f"✅ Duration: {result.duration:.2f}s")
        print(f"✅ Output: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n2️⃣ Test comando peligroso (rm):")
    try:
        result = executor.execute("rm -rf /")
        print("❌ FALLO: Comando peligroso fue ejecutado!")
    except ValueError as e:
        print(f"✅ Bloqueado correctamente: {e}")
    
    print("\n3️⃣ Test comando no permitido (curl):")
    try:
        result = executor.execute("curl https://example.com")
        print("❌ FALLO: Comando no permitido fue ejecutado!")
    except ValueError as e:
        print(f"✅ Bloqueado correctamente: {e}")
    
    print("\n4️⃣ Test can_execute:")
    test_commands = [
        "ls -la",
        "python test.py",
        "rm file.txt",
        "curl https://example.com",
        "git status"
    ]
    for cmd in test_commands:
        can_exec, reason = executor.can_execute(cmd)
        status = "✅" if can_exec else "❌"
        print(f"{status} {cmd}: {reason}")
    
    print("\n5️⃣ Test múltiples comandos:")
    commands = [
        "echo Hello",
        "python --version",
        "ls setup.py"
    ]
    try:
        results = executor.execute_multiple(commands, stop_on_error=False)
        for i, result in enumerate(results, 1):
            status = "✅" if result.success else "❌"
            print(f"{status} Command {i}: {result.command} (exit: {result.exit_code})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n6️⃣ Estadísticas:")
    stats = executor.get_stats()
    print(f"  Total commands: {stats['total_commands']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    print(f"  Avg duration: {stats['avg_duration_seconds']:.2f}s")


def main():
    """Función principal."""
    print("\n🚀 PatCode - Test Suite Fase 2")
    print("Sistema Multi-LLM y Shell Executor\n")
    
    test_llm_system()
    
    test_shell_executor()
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETADOS")
    print("="*60)


if __name__ == "__main__":
    main()
