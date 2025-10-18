"""
Ollama Client - FASE 2: Sistema Multi-LLM

Cliente para Ollama (LLM local).
"""

import requests
import logging
from typing import Optional, Dict, Any

from llm.base_client import BaseLLMClient, LLMResponse, LLMError


logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """
    Cliente para Ollama.
    
    Ollama es un runtime local para LLMs que permite ejecutar
    modelos como Llama, Mistral, etc. de forma completamente gratuita.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el cliente Ollama.
        
        Args:
            config: Configuración
                {
                    "model": "llama3.2",
                    "base_url": "http://localhost:11434",
                    "timeout": 300,
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434").rstrip('/')
        self.timeout = config.get("timeout", 300)
        
        logger.info(f"OllamaClient initialized: {self.base_url} | Model: {self.model}")
    
    def is_available(self) -> bool:
        """
        Verifica que Ollama esté corriendo.
        
        Returns:
            True si Ollama está disponible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code != 200:
                logger.debug(f"Ollama not available: status {response.status_code}")
                return False
            
            models_data = response.json()
            available_models = [m['name'] for m in models_data.get('models', [])]
            
            model_available = any(
                self.model in m or m.startswith(self.model.split(':')[0])
                for m in available_models
            )
            
            if not model_available:
                logger.debug(f"Model {self.model} not found in Ollama")
                logger.debug(f"Available models: {available_models}")
                return False
            
            return True
            
        except requests.exceptions.ConnectionError:
            logger.debug("Cannot connect to Ollama")
            return False
        except Exception as e:
            logger.debug(f"Error checking Ollama availability: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Genera una respuesta usando Ollama.
        
        Args:
            prompt: El prompt del usuario
            system_prompt: System prompt opcional
            
        Returns:
            LLMResponse con la respuesta
            
        Raises:
            LLMError: Si hay error
        """
        if not self.is_available():
            raise LLMError(
                provider="ollama",
                error_type="connection_error",
                message=f"Ollama is not running at {self.base_url}. Start it with 'ollama serve'"
            )
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.debug(f"Ollama request: {self.base_url}/api/generate | Model: {self.model}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise LLMError(
                    provider="ollama",
                    error_type="model_not_found",
                    message=f"Model '{self.model}' not found. Pull it with: ollama pull {self.model}"
                )
            
            response.raise_for_status()
            
            data = response.json()
            
            content = data.get("response", "")
            
            if not content:
                logger.warning("Ollama returned empty response")
                content = "Sorry, I couldn't generate a response. Please try again."
            
            logger.debug(f"Ollama response: {len(content)} chars")
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="ollama",
                tokens_used=None,
                finish_reason=data.get("done_reason")
            )
            
        except requests.exceptions.Timeout:
            raise LLMError(
                provider="ollama",
                error_type="timeout",
                message=f"Request timeout after {self.timeout}s"
            )
        except requests.exceptions.ConnectionError:
            raise LLMError(
                provider="ollama",
                error_type="connection_error",
                message=f"Cannot connect to Ollama at {self.base_url}"
            )
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(
                provider="ollama",
                error_type="api_error",
                message=str(e)
            )
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Ollama no tiene rate limits (es local).
        
        Returns:
            Dict indicando que no hay límites
        """
        return {
            "has_limit": False,
            "remaining": float('inf'),
            "limit": float('inf')
        }
