"""
Base Client - FASE 2: Sistema Multi-LLM

Clase abstracta base para todos los clientes LLM.
Define la interfaz común que todos los providers deben implementar.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Respuesta de un LLM."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class LLMError(Exception):
    """Error al llamar a un LLM."""
    provider: str
    error_type: str
    message: str
    
    def __str__(self):
        return f"[{self.provider}] {self.error_type}: {self.message}"


class BaseLLMClient(ABC):
    """
    Clase base abstracta para clientes LLM.
    
    Todos los providers (Ollama, Groq, Together, etc.) deben heredar
    de esta clase e implementar los métodos abstractos.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el cliente LLM.
        
        Args:
            config: Configuración del provider
                {
                    "model": "nombre-del-modelo",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    ...
                }
        """
        self.config = config
        self.model = config.get("model")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Genera una respuesta del LLM.
        
        Args:
            prompt: El prompt del usuario
            system_prompt: System prompt opcional
            
        Returns:
            LLMResponse con la respuesta
            
        Raises:
            LLMError: Si hay algún error
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el provider está disponible.
        
        Returns:
            True si está disponible, False si no
        """
        pass
    
    @abstractmethod
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Retorna estado del rate limit.
        
        Returns:
            Dict con información de rate limits
            {
                "has_limit": bool,
                "remaining": int,
                "limit": int,
                ...
            }
        """
        pass
