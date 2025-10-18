"""
Groq Client - FASE 2: Sistema Multi-LLM

Cliente para Groq (API gratuita super rápida).
"""

import os
import logging
from typing import Optional, Dict, Any

from llm.base_client import BaseLLMClient, LLMResponse, LLMError
from llm.utils import RateLimiter


logger = logging.getLogger(__name__)


class GroqClient(BaseLLMClient):
    """
    Cliente para Groq.
    
    Groq ofrece acceso gratuito a modelos como Llama 3.1 70B
    con 14,400 requests/día en el tier gratuito.
    
    Límites del tier gratuito:
    - 30 requests por minuto
    - 14,400 requests por día
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el cliente Groq.
        
        Args:
            config: Configuración
                {
                    "model": "llama-3.1-70b-versatile",
                    "api_key": "gsk_...",
                    "timeout": 60,
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
        """
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in config or environment")
        
        self.timeout = config.get("timeout", 60)
        
        self.rate_limiter = RateLimiter(
            requests_per_minute=30,
            requests_per_day=14400
        )
        
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            logger.info(f"GroqClient initialized | Model: {self.model}")
        except ImportError:
            raise ImportError(
                "groq package not installed. Install it with: pip install groq"
            )
    
    def is_available(self) -> bool:
        """
        Verifica que la API key sea válida.
        
        Returns:
            True si Groq está disponible
        """
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.debug(f"Groq not available: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Genera una respuesta usando Groq.
        
        Args:
            prompt: El prompt del usuario
            system_prompt: System prompt opcional
            
        Returns:
            LLMResponse con la respuesta
            
        Raises:
            LLMError: Si hay error
        """
        if not self.rate_limiter.can_make_request():
            status = self.rate_limiter.get_status()
            raise LLMError(
                provider="groq",
                error_type="rate_limit",
                message=f"Rate limit exceeded. RPM: {status['rpm_used']}/{status['rpm_limit']}, "
                        f"RPD: {status['rpd_used']}/{status['rpd_limit']}"
            )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            logger.debug(f"Groq request | Model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            self.rate_limiter.record_request()
            
            content = response.choices[0].message.content
            
            logger.debug(f"Groq response: {len(content)} chars, {response.usage.total_tokens} tokens")
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="groq",
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            error_msg = str(e)
            
            if "rate_limit" in error_msg.lower():
                error_type = "rate_limit"
            elif "timeout" in error_msg.lower():
                error_type = "timeout"
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                error_type = "authentication_error"
            else:
                error_type = "api_error"
            
            raise LLMError(
                provider="groq",
                error_type=error_type,
                message=error_msg
            )
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Retorna estado del rate limiter.
        
        Returns:
            Dict con información de límites
        """
        return self.rate_limiter.get_status()
