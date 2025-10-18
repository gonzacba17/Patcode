"""
Example Multi-LLM - Ejemplos de uso del sistema Multi-LLM

Demuestra cómo usar el sistema Multi-LLM con diferentes providers
y estrategias.
"""

import os
import logging
from llm.provider_manager import ProviderManager
from llm.ollama_client import OllamaClient
from llm.groq_client import GroqClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """Ejemplo básico: Usar un solo provider."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Uso básico con Ollama")
    print("="*60)
    
    config = {
        "model": "llama3.2",
        "base_url": "http://localhost:11434",
        "timeout": 60
    }
    
    client = OllamaClient(config)
    
    if not client.is_available():
        print("❌ Ollama no está disponible")
        return
    
    response = client.generate("What is Python?")
    
    print(f"\n✅ Provider: {response.provider}")
    print(f"✅ Model: {response.model}")
    print(f"✅ Response:\n{response.content}")


def example_2_provider_manager():
    """Ejemplo con ProviderManager: Fallback automático."""
    print("\n" + "="*60)
    print("EJEMPLO 2: ProviderManager con fallback")
    print("="*60)
    
    config = {
        "providers": {
            "ollama": {
                "enabled": True,
                "model": "llama3.2",
                "base_url": "http://localhost:11434"
            },
            "groq": {
                "enabled": True,
                "model": "llama-3.1-70b-versatile",
                "api_key": os.getenv("GROQ_API_KEY")
            }
        },
        "strategies": {
            "simple": ["ollama"],
            "complex": ["groq", "ollama"]
        }
    }
    
    manager = ProviderManager(config)
    
    print("\nProviders disponibles:", manager.get_available_providers())
    
    print("\n--- Query Simple (usa Ollama) ---")
    try:
        response = manager.generate(
            prompt="Say 'hello' in one word",
            strategy="simple"
        )
        print(f"✅ Provider usado: {response.provider}")
        print(f"✅ Response: {response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n--- Query Compleja (intenta Groq, fallback a Ollama) ---")
    try:
        response = manager.generate(
            prompt="Explain async/await in JavaScript with examples",
            strategy="complex"
        )
        print(f"✅ Provider usado: {response.provider}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Response (primeros 300 chars):\n{response.content[:300]}...")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_custom_strategy():
    """Ejemplo: Crear estrategia personalizada."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Estrategia personalizada")
    print("="*60)
    
    config = {
        "providers": {
            "ollama": {
                "enabled": True,
                "model": "llama3.2",
                "base_url": "http://localhost:11434"
            },
            "groq": {
                "enabled": True,
                "model": "llama-3.1-70b-versatile",
                "api_key": os.getenv("GROQ_API_KEY")
            }
        },
        "strategies": {}
    }
    
    manager = ProviderManager(config)
    
    manager.set_strategy("my_custom_strategy", ["groq", "ollama"])
    
    print("Estrategias configuradas:", manager.get_strategies())
    
    try:
        response = manager.generate(
            prompt="Write a Python function to reverse a string",
            strategy="my_custom_strategy"
        )
        print(f"\n✅ Provider usado: {response.provider}")
        print(f"✅ Response:\n{response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_rate_limit_handling():
    """Ejemplo: Manejo de rate limits."""
    print("\n" + "="*60)
    print("EJEMPLO 4: Manejo de rate limits")
    print("="*60)
    
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Necesitas GROQ_API_KEY para este ejemplo")
        return
    
    config = {
        "providers": {
            "groq": {
                "enabled": True,
                "model": "llama-3.1-70b-versatile",
                "api_key": os.getenv("GROQ_API_KEY")
            }
        },
        "strategies": {
            "default": ["groq"]
        }
    }
    
    manager = ProviderManager(config)
    
    print("\nStatus de rate limits:")
    status = manager.get_status()
    for provider, info in status.items():
        if info.get("available"):
            print(f"\n{provider}:")
            print(f"  Model: {info['model']}")
            rl = info['rate_limit']
            if rl.get('has_limit'):
                print(f"  RPM: {rl['rpm_used']}/{rl['rpm_limit']}")
                print(f"  RPD: {rl['rpd_used']}/{rl['rpd_limit']}")
    
    print("\nHaciendo varias requests para ver rate limiting...")
    for i in range(3):
        try:
            response = manager.generate(
                prompt=f"Count to {i+1}",
                strategy="default"
            )
            print(f"✅ Request {i+1}: Success")
        except Exception as e:
            print(f"❌ Request {i+1}: {e}")


def example_5_system_prompt():
    """Ejemplo: Usar system prompt."""
    print("\n" + "="*60)
    print("EJEMPLO 5: System Prompt")
    print("="*60)
    
    config = {
        "providers": {
            "ollama": {
                "enabled": True,
                "model": "llama3.2",
                "base_url": "http://localhost:11434"
            }
        },
        "strategies": {
            "default": ["ollama"]
        }
    }
    
    manager = ProviderManager(config)
    
    system_prompt = "You are a helpful Python programming assistant. Always respond with concise, practical code examples."
    
    try:
        response = manager.generate(
            prompt="How do I read a CSV file?",
            system_prompt=system_prompt,
            strategy="default"
        )
        print(f"\n✅ Response:\n{response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          PatCode - Multi-LLM Examples                     ║
║                                                            ║
║  Ejemplos de uso del sistema Multi-LLM                    ║
╚════════════════════════════════════════════════════════════╝
""")
    
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        if example == "1":
            example_1_basic_usage()
        elif example == "2":
            example_2_provider_manager()
        elif example == "3":
            example_3_custom_strategy()
        elif example == "4":
            example_4_rate_limit_handling()
        elif example == "5":
            example_5_system_prompt()
        else:
            print(f"Ejemplo desconocido: {example}")
    else:
        print("Ejemplos disponibles:")
        print("  python example_multi_llm.py 1  - Uso básico con Ollama")
        print("  python example_multi_llm.py 2  - ProviderManager con fallback")
        print("  python example_multi_llm.py 3  - Estrategia personalizada")
        print("  python example_multi_llm.py 4  - Manejo de rate limits")
        print("  python example_multi_llm.py 5  - System prompt")
        print()
        
        response = input("¿Ejecutar todos los ejemplos? (s/n): ").strip().lower()
        if response == "s":
            example_1_basic_usage()
            example_2_provider_manager()
            example_3_custom_strategy()
            example_4_rate_limit_handling()
            example_5_system_prompt()
