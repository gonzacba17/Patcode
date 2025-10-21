"""
Utilidades para verificar disponibilidad de Ollama.

Este módulo proporciona funciones para verificar que Ollama esté corriendo
y que los modelos necesarios estén disponibles antes de usarlos.
"""

import requests
from typing import Tuple, List, Dict, Optional
from config.settings import settings
from exceptions import OllamaConnectionError, OllamaModelNotFoundError
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_ollama_service() -> bool:
    """
    Verifica si el servicio de Ollama está corriendo.
    
    Returns:
        True si está disponible, False si no
    """
    try:
        response = requests.get(
            f"{settings.ollama.base_url}/api/tags",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama no disponible: {e}")
        return False


def get_available_models() -> List[Dict[str, str]]:
    """
    Obtiene lista de modelos disponibles en Ollama.
    
    Returns:
        Lista de diccionarios con información de modelos
    
    Raises:
        OllamaConnectionError: Si no se puede conectar
    """
    try:
        response = requests.get(
            f"{settings.ollama.base_url}/api/tags",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        models = []
        for model in data.get("models", []):
            models.append({
                "name": model.get("name", "unknown"),
                "size": model.get("size", 0),
                "modified": model.get("modified_at", "")
            })
        
        return models
        
    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError(
            "No se pudo conectar con Ollama",
            f"Verifica que esté corriendo en {settings.ollama.base_url}"
        )
    except requests.exceptions.Timeout:
        raise OllamaConnectionError(
            "Timeout al conectar con Ollama",
            "El servicio no respondió a tiempo"
        )
    except Exception as e:
        raise OllamaConnectionError(
            "Error al obtener lista de modelos",
            str(e)
        )


def verify_model_exists(model_name: str) -> Tuple[bool, str]:
    """
    Verifica si un modelo específico está disponible.
    
    Args:
        model_name: Nombre del modelo a verificar
    
    Returns:
        Tupla (existe, mensaje)
    """
    try:
        models = get_available_models()
        model_names = [m["name"] for m in models]
        
        if model_name in model_names:
            return True, f"✓ Modelo '{model_name}' disponible"
        else:
            models_str = ", ".join(model_names) if model_names else "ninguno"
            return False, (
                f"✗ Modelo '{model_name}' no encontrado.\n"
                f"  Modelos disponibles: {models_str}\n"
                f"  Ejecuta: ollama pull {model_name}"
            )
    except OllamaConnectionError as e:
        return False, f"✗ Error al verificar modelos: {str(e)}"


def get_model_info(model_name: str) -> Optional[Dict]:
    """
    Obtiene información detallada de un modelo.
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        Diccionario con información del modelo o None si no existe
    """
    try:
        response = requests.post(
            f"{settings.ollama.base_url}/api/show",
            json={"name": model_name},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        logger.debug(f"Error al obtener info del modelo: {e}")
        return None


def startup_checks() -> None:
    """
    Ejecuta todas las verificaciones de inicio.
    
    Verifica:
    1. Que Ollama esté disponible
    2. Que el modelo configurado exista
    
    Raises:
        OllamaConnectionError: Si Ollama no está disponible
        OllamaModelNotFoundError: Si el modelo configurado no existe
    """
    logger.info("Verificando disponibilidad de Ollama...")
    
    # Verificar servicio
    if not check_ollama_service():
        raise OllamaConnectionError(
            "Ollama no está corriendo",
            f"Verifica el servicio en {settings.ollama.base_url}\n"
            "Ejecuta: ollama serve"
        )
    
    logger.info("✓ Ollama está disponible")
    
    # Verificar modelo
    model_exists, message = verify_model_exists(settings.ollama.model)
    
    if not model_exists:
        raise OllamaModelNotFoundError(
            f"Modelo '{settings.ollama.model}' no disponible",
            message
        )
    
    logger.info(message)
    
    # Info adicional del modelo
    model_info = get_model_info(settings.ollama.model)
    if model_info:
        logger.debug(f"Info del modelo: {model_info.get('modelfile', 'N/A')[:100]}")


def list_models() -> None:
    """
    Lista todos los modelos disponibles en formato legible.
    
    Útil para debugging y selección de modelos.
    """
    try:
        models = get_available_models()
        
        if not models:
            print("No hay modelos instalados")
            print("Descarga uno con: ollama pull <modelo>")
            return
        
        print(f"\n📦 Modelos disponibles en Ollama ({len(models)}):\n")
        
        for i, model in enumerate(models, 1):
            size_gb = model['size'] / (1024**3) if model['size'] else 0
            print(f"{i}. {model['name']}")
            print(f"   Tamaño: {size_gb:.2f} GB")
            print(f"   Modificado: {model['modified']}\n")
            
    except OllamaConnectionError as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Test del módulo
    print("🔍 Verificando Ollama...\n")
    
    try:
        startup_checks()
        print("\n✅ Todas las verificaciones pasaron")
        print("\nModelos disponibles:")
        list_models()
        
    except (OllamaConnectionError, OllamaModelNotFoundError) as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'details'):
            print(f"   {e.details}")
