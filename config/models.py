"""
Configuración y gestión de modelos Ollama disponibles
"""
import requests
from typing import Dict, List, Optional, Any
from config.settings import OLLAMA_BASE_URL


# ============================================================================
# MODELOS RECOMENDADOS PARA PATCODE
# ============================================================================

AVAILABLE_MODELS = {
    "llama3.2:latest": {
        "name": "Llama 3.2",
        "size": "3B",
        "ram_required": "4GB",
        "best_for": "General purpose, conversación",
        "coding_score": 6,
        "speed": "rápido",
        "description": "Modelo general de Meta, bueno para empezar",
        "recommended": False
    },
    
    "qwen2.5-coder:7b": {
        "name": "Qwen 2.5 Coder 7B",
        "size": "7B",
        "ram_required": "8GB",
        "best_for": "Programación general",
        "coding_score": 9,
        "speed": "medio",
        "description": "Excelente para coding, equilibrio perfecto",
        "recommended": True
    },
    
    "qwen2.5-coder:32b": {
        "name": "Qwen 2.5 Coder 32B",
        "size": "32B",
        "ram_required": "32GB",
        "best_for": "Programación avanzada",
        "coding_score": 10,
        "speed": "lento",
        "description": "El mejor para coding, requiere hardware potente",
        "recommended": True
    },
    
    "deepseek-coder-v2:latest": {
        "name": "DeepSeek Coder V2",
        "size": "16B",
        "ram_required": "16GB",
        "best_for": "Programación, seguimiento de instrucciones",
        "coding_score": 9,
        "speed": "medio",
        "description": "Excelente para tareas de coding complejas",
        "recommended": True
    },
    
    "codellama:7b": {
        "name": "Code Llama 7B",
        "size": "7B",
        "ram_required": "8GB",
        "best_for": "Programación Python",
        "coding_score": 8,
        "speed": "medio",
        "description": "Especializado en código, de Meta",
        "recommended": False
    },
    
    "mistral:7b": {
        "name": "Mistral 7B",
        "size": "7B",
        "ram_required": "8GB",
        "best_for": "General purpose",
        "coding_score": 7,
        "speed": "rápido",
        "description": "Buen equilibrio entre velocidad y calidad",
        "recommended": False
    },
    
    "phi3:mini": {
        "name": "Phi-3 Mini",
        "size": "3.8B",
        "ram_required": "4GB",
        "best_for": "Dispositivos con pocos recursos",
        "coding_score": 6,
        "speed": "muy rápido",
        "description": "Pequeño pero sorprendentemente capaz",
        "recommended": False
    }
}


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def get_installed_models() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de modelos instalados en Ollama
    
    Returns:
        Lista de diccionarios con información de modelos
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("models", [])
        return []
    except:
        return []


def is_model_installed(model_name: str) -> bool:
    """
    Verifica si un modelo está instalado
    
    Args:
        model_name: Nombre del modelo a verificar
        
    Returns:
        True si está instalado
    """
    installed = get_installed_models()
    return any(model["name"] == model_name for model in installed)


def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene información detallada de un modelo
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        Diccionario con info del modelo o None
    """
    return AVAILABLE_MODELS.get(model_name)


def recommend_model(task_type: str = "coding", ram_available: int = 8) -> str:
    """
    Recomienda un modelo según el tipo de tarea y RAM disponible
    
    Args:
        task_type: Tipo de tarea ("coding", "general", "chat")
        ram_available: GB de RAM disponibles
        
    Returns:
        Nombre del modelo recomendado
    """
    # Filtrar por RAM disponible
    suitable_models = {
        name: info for name, info in AVAILABLE_MODELS.items()
        if int(info["ram_required"].rstrip("GB")) <= ram_available
    }
    
    if not suitable_models:
        return "llama3.2:latest"  # Fallback más ligero
    
    # Filtrar por tarea
    if task_type == "coding":
        # Ordenar por coding_score descendente
        sorted_models = sorted(
            suitable_models.items(),
            key=lambda x: x[1]["coding_score"],
            reverse=True
        )
        return sorted_models[0][0]
    
    # Para general/chat, devolver el recomendado o el primero
    for name, info in suitable_models.items():
        if info.get("recommended"):
            return name
    
    return list(suitable_models.keys())[0]


def print_available_models():
    """Imprime una tabla con los modelos disponibles"""
    print("\n📦 MODELOS DISPONIBLES PARA PATCODE\n")
    print("=" * 100)
    print(f"{'Modelo':<25} {'Tamaño':<8} {'RAM':<8} {'Coding':<8} {'Velocidad':<12} {'Recomendado':<12}")
    print("=" * 100)
    
    for model_name, info in AVAILABLE_MODELS.items():
        installed = "✅" if is_model_installed(model_name) else "⬇️ "
        recommended = "⭐" if info.get("recommended") else ""
        
        print(f"{installed} {model_name:<22} {info['size']:<8} {info['ram_required']:<8} "
              f"{info['coding_score']}/10   {info['speed']:<12} {recommended}")
    
    print("=" * 100)
    print("\n💡 LEYENDA:")
    print("  ✅ = Instalado")
    print("  ⬇️  = No instalado (ejecutá: ollama pull <modelo>)")
    print("  ⭐ = Recomendado para PatCode\n")


def print_model_details(model_name: str):
    """
    Imprime detalles de un modelo específico
    
    Args:
        model_name: Nombre del modelo
    """
    info = get_model_info(model_name)
    
    if not info:
        print(f"❌ Modelo desconocido: {model_name}")
        return
    
    installed = is_model_installed(model_name)
    
    print(f"\n📦 {info['name']}")
    print("=" * 60)
    print(f"Modelo: {model_name}")
    print(f"Tamaño: {info['size']} parámetros")
    print(f"RAM requerida: {info['ram_required']}")
    print(f"Mejor para: {info['best_for']}")
    print(f"Puntuación coding: {info['coding_score']}/10")
    print(f"Velocidad: {info['speed']}")
    print(f"Estado: {'✅ Instalado' if installed else '⬇️  No instalado'}")
    
    if info.get("recommended"):
        print("⭐ RECOMENDADO para PatCode")
    
    print(f"\nDescripción: {info['description']}")
    
    if not installed:
        print(f"\n💡 Para instalar: ollama pull {model_name}")
    
    print("=" * 60 + "\n")


def get_recommended_models_list() -> List[str]:
    """
    Devuelve lista de modelos recomendados
    
    Returns:
        Lista de nombres de modelos
    """
    return [
        name for name, info in AVAILABLE_MODELS.items()
        if info.get("recommended")
    ]


def check_model_compatibility(model_name: str) -> Dict[str, Any]:
    """
    Verifica la compatibilidad de un modelo con el sistema
    
    Args:
        model_name: Nombre del modelo a verificar
        
    Returns:
        Diccionario con información de compatibilidad
    """
    info = get_model_info(model_name)
    
    if not info:
        return {
            "compatible": False,
            "reason": "Modelo desconocido"
        }
    
    # Obtener RAM del sistema (aproximado)
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        ram_gb = 8  # Asumir 8GB si no se puede detectar
    
    required_ram = int(info["ram_required"].rstrip("GB"))
    
    if ram_gb < required_ram:
        return {
            "compatible": False,
            "reason": f"RAM insuficiente. Requerido: {required_ram}GB, Disponible: {ram_gb:.1f}GB",
            "recommendation": recommend_model("coding", int(ram_gb))
        }
    
    return {
        "compatible": True,
        "reason": "Compatible con tu sistema",
        "ram_available": ram_gb,
        "ram_required": required_ram
    }


def install_model_instructions(model_name: str):
    """
    Muestra instrucciones para instalar un modelo
    
    Args:
        model_name: Nombre del modelo
    """
    info = get_model_info(model_name)
    
    if not info:
        print(f"❌ Modelo desconocido: {model_name}")
        return
    
    print(f"\n📥 INSTALACIÓN DE {info['name']}")
    print("=" * 60)
    print(f"\n1️⃣  Verificá que tenés suficiente espacio en disco")
    print(f"    (Se necesitan ~{info['size']} parámetros)")
    
    print(f"\n2️⃣  Verificá que tenés suficiente RAM")
    print(f"    (Mínimo recomendado: {info['ram_required']})")
    
    print(f"\n3️⃣  Ejecutá el siguiente comando:")
    print(f"    ollama pull {model_name}")
    
    print(f"\n4️⃣  Esperá a que se descargue (puede tardar varios minutos)")
    
    print(f"\n5️⃣  Una vez instalado, configuralo en PatCode:")
    print(f"    export OLLAMA_MODEL={model_name}")
    print(f"    # O editá config/settings.py")
    
    print("\n=" * 60 + "\n")


def compare_models(model1: str, model2: str):
    """
    Compara dos modelos lado a lado
    
    Args:
        model1: Primer modelo
        model2: Segundo modelo
    """
    info1 = get_model_info(model1)
    info2 = get_model_info(model2)
    
    if not info1 or not info2:
        print("❌ Uno o ambos modelos no existen")
        return
    
    print(f"\n⚖️  COMPARACIÓN DE MODELOS\n")
    print("=" * 80)
    print(f"{'Característica':<25} {info1['name']:<25} {info2['name']:<25}")
    print("=" * 80)
    
    comparisons = [
        ("Modelo", model1, model2),
        ("Tamaño", info1['size'], info2['size']),
        ("RAM requerida", info1['ram_required'], info2['ram_required']),
        ("Coding score", f"{info1['coding_score']}/10", f"{info2['coding_score']}/10"),
        ("Velocidad", info1['speed'], info2['speed']),
        ("Mejor para", info1['best_for'], info2['best_for']),
        ("Instalado", 
         "✅" if is_model_installed(model1) else "❌",
         "✅" if is_model_installed(model2) else "❌"),
    ]
    
    for label, val1, val2 in comparisons:
        print(f"{label:<25} {val1:<25} {val2:<25}")
    
    print("=" * 80)
    
    # Recomendación
    if info1['coding_score'] > info2['coding_score']:
        print(f"\n💡 {info1['name']} es mejor para coding")
    elif info2['coding_score'] > info1['coding_score']:
        print(f"\n💡 {info2['name']} es mejor para coding")
    else:
        print(f"\n💡 Ambos tienen el mismo nivel para coding")
    
    print()


# ============================================================================
# INFORMACIÓN DE BENCHMARKS
# ============================================================================

BENCHMARK_SCORES = {
    "qwen2.5-coder:32b": {
        "humaneval": 92.7,
        "mbpp": 84.1,
        "description": "Mejor modelo para coding en PatCode"
    },
    "qwen2.5-coder:7b": {
        "humaneval": 88.3,
        "mbpp": 79.8,
        "description": "Excelente equilibrio rendimiento/recursos"
    },
    "deepseek-coder-v2:latest": {
        "humaneval": 86.5,
        "mbpp": 78.2,
        "description": "Muy bueno para seguir instrucciones"
    },
    "codellama:7b": {
        "humaneval": 78.6,
        "mbpp": 72.1,
        "description": "Sólido para Python"
    },
    "llama3.2:latest": {
        "humaneval": 67.4,
        "mbpp": 63.5,
        "description": "General purpose, no especializado en código"
    }
}


def print_benchmarks():
    """Imprime benchmarks de los modelos"""
    print("\n📊 BENCHMARKS DE CODING\n")
    print("=" * 70)
    print(f"{'Modelo':<30} {'HumanEval':<15} {'MBPP':<15}")
    print("=" * 70)
    
    sorted_models = sorted(
        BENCHMARK_SCORES.items(),
        key=lambda x: x[1]["humaneval"],
        reverse=True
    )
    
    for model_name, scores in sorted_models:
        print(f"{model_name:<30} {scores['humaneval']:.1f}%          {scores['mbpp']:.1f}%")
    
    print("=" * 70)
    print("\n📖 REFERENCIAS:")
    print("  • HumanEval: Capacidad de resolver problemas de programación")
    print("  • MBPP: Mostly Basic Python Problems\n")


# ============================================================================
# AUTO-CONFIGURACIÓN
# ============================================================================

def auto_select_model() -> str:
    """
    Selecciona automáticamente el mejor modelo disponible
    
    Returns:
        Nombre del modelo seleccionado
    """
    installed = get_installed_models()
    
    if not installed:
        print("⚠️  No hay modelos instalados. Instalando llama3.2:latest...")
        return "llama3.2:latest"
    
    # Buscar modelos recomendados instalados
    installed_names = [m["name"] for m in installed]
    recommended = get_recommended_models_list()
    
    for rec_model in recommended:
        if rec_model in installed_names:
            print(f"✅ Usando modelo recomendado: {rec_model}")
            return rec_model
    
    # Usar el primer instalado
    selected = installed[0]["name"]
    print(f"ℹ️  Usando modelo instalado: {selected}")
    return selected