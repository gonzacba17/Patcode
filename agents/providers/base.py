"""Interfaz base para providers de LLM"""

from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class GenerationConfig:
    """Configuración para generación de texto"""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 0.9
    stop_sequences: Optional[list[str]] = None
    stream: bool = False

class LLMProvider(ABC):
    """Interfaz abstracta para providers de modelos de lenguaje"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        config: Optional[GenerationConfig] = None
    ) -> str  < /dev/null |  Generator[str, None, None]:
        """Genera texto basado en un prompt"""
        pass
    
    @abstractmethod
    def check_health(self) -> bool:
        """Verifica si el servicio está disponible"""
        pass
    
    @abstractmethod
    def list_models(self) -> list[str]:
        """Lista modelos disponibles"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo actual"""
        pass
