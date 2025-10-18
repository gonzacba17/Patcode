"""
Together AI Client - FASE 2: Sistema Multi-LLM

Cliente para Together AI (API con créditos gratuitos iniciales).
"""

import os
import requests
import logging
from typing import Optional, Dict, Any

from llm.base_client import BaseLLMClient, LLMResponse, LLMError


logger = logging.getLogger(__name__)


class TogetherClient(BaseLLMClient):
    """
    Cliente para Together AI.
    
    Together AI ofrece acceso a múltiples modelos open source
    con $5 de créditos gratis al registrarse.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el cliente Together AI.
        
        Args:
            config: Configuración
                {
                    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                    "api_key": "...",
                    "timeout": 60,
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
        """
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("TOGETHER_API_KEY")
        
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY not found in config or environment")
        
        self.base_url = "https://api.together.xyz/v1"
        self.timeout = config.get("timeout", 60)
        
        logger.info(f"TogetherClient initialized | Model: {self.model}")
    
    def is_available(self) -> bool:
        """
        Verifica que la API key sea válida.
        
        Returns:
            True si Together AI está disponible
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Together AI not available: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Genera una respuesta usando Together AI.
        
        Args:
            prompt: El prompt del usuario
            system_prompt: System prompt opcional
            
        Returns:
            LLMResponse con la respuesta
            
        Raises:
            LLMError: Si hay error
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            logger.debug(f"Together AI request | Model: {self.model}")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens")
            
            logger.debug(f"Together AI response: {len(content)} chars, {tokens_used} tokens")
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="together",
                tokens_used=tokens_used,
                finish_reason=data["choices"][0].get("finish_reason")
            )
            
        except requests.exceptions.Timeout:
            raise LLMError(
                provider="together",
                error_type="timeout",
                message=f"Request timeout after {self.timeout}s"
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_type = "authentication_error"
                message = "Invalid API key"
            elif e.response.status_code == 429:
                error_type = "rate_limit"
                message = "Rate limit exceeded or out of credits"
            else:
                error_type = "api_error"
                message = str(e)
            
            raise LLMError(
                provider="together",
                error_type=error_type,
                message=message
            )
        except Exception as e:
            raise LLMError(
                provider="together",
                error_type="api_error",
                message=str(e)
            )
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Together AI no expone información de rate limits via API.
        
        Returns:
            Dict con información limitada
        """
        return {
            "has_limit": True,
            "remaining": "unknown",
            "limit": "unknown"
        }
