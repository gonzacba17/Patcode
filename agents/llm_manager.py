import os
import time
from typing import Dict, List, Generator, Optional, Callable, Any
from datetime import datetime, timedelta
from functools import wraps

from agents.llm_adapters.base_adapter import BaseLLMAdapter
from agents.llm_adapters.ollama_adapter import OllamaAdapter
from agents.llm_adapters.groq_adapter import GroqAdapter
from agents.llm_adapters.openai_adapter import OpenAIAdapter
from utils.logger import setup_logger
from exceptions import LLMRateLimitError

try:
    from utils.telemetry import get_telemetry
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

logger = setup_logger(__name__)


class RateLimiter:
    """
    Decorador para limitar la tasa de llamadas a funciones.
    
    Attributes:
        max_calls: Número máximo de llamadas permitidas
        period: Periodo de tiempo en segundos
    """
    
    def __init__(self, max_calls: int = 20, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls: List[float] = []
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            now = time.time()
            
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.period]
            
            if len(self.calls) >= self.max_calls:
                wait_time = self.period - (now - self.calls[0])
                logger.warning(
                    f"Rate limit alcanzado: {len(self.calls)}/{self.max_calls} "
                    f"llamadas en {self.period}s. Espera requerida: {wait_time:.1f}s"
                )
                raise LLMRateLimitError(
                    f"Rate limit excedido. Máximo {self.max_calls} llamadas "
                    f"por {self.period}s. Espera {wait_time:.1f}s"
                )
            
            self.calls.append(now)
            logger.debug(f"Rate limiter: {len(self.calls)}/{self.max_calls} llamadas")
            
            return func(*args, **kwargs)
        
        return wrapper


class LLMManager:
    
    def __init__(self, config: 'LLMSettings'):
        self.config = config
        self.adapters: Dict[str, BaseLLMAdapter] = {}
        self.current_provider: Optional[str] = None
        self.availability_cache: Dict[str, tuple[bool, datetime]] = {}
        self.cache_ttl = 60
        self.rate_limiter = RateLimiter(max_calls=20, period=60)
        
        self._initialize_adapters()
        self._select_initial_provider()
    
    def _initialize_adapters(self):
        ollama_adapter = OllamaAdapter(
            base_url=self.config.ollama_url,
            model=self.config.ollama_model,
            timeout=self.config.ollama_timeout,
            temperature=self.config.temperature
        )
        self.adapters['ollama'] = ollama_adapter
        
        if self.config.groq_api_key:
            groq_adapter = GroqAdapter(
                api_key=self.config.groq_api_key,
                model=self.config.groq_model,
                timeout=self.config.groq_timeout,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            self.adapters['groq'] = groq_adapter
        else:
            logger.info("GROQ_API_KEY no configurada, Groq adapter no disponible")
        
        if self.config.openai_api_key:
            openai_adapter = OpenAIAdapter(
                api_key=self.config.openai_api_key,
                model=self.config.openai_model,
                timeout=self.config.openai_timeout,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            self.adapters['openai'] = openai_adapter
        else:
            logger.debug("OPENAI_API_KEY no configurada, OpenAI adapter no disponible")
        
        logger.info(f"Adapters inicializados: {list(self.adapters.keys())}")
    
    def _select_initial_provider(self):
        if self.config.default_provider in self.adapters:
            if self._is_provider_available(self.config.default_provider):
                self.current_provider = self.config.default_provider
                logger.info(f"Provider por defecto seleccionado: {self.current_provider}")
                return
        
        for provider in self.config.fallback_order:
            if provider in self.adapters and self._is_provider_available(provider):
                self.current_provider = provider
                logger.info(f"Provider seleccionado (fallback): {self.current_provider}")
                return
        
        if 'ollama' in self.adapters:
            self.current_provider = 'ollama'
            logger.warning(f"Ningún provider disponible, usando Ollama como último recurso")
        else:
            logger.error("No hay providers disponibles")
            self.current_provider = None
    
    def _is_provider_available(self, provider: str, use_cache: bool = True) -> bool:
        if provider not in self.adapters:
            return False
        
        if use_cache and provider in self.availability_cache:
            cached_available, cached_time = self.availability_cache[provider]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                return cached_available
        
        adapter = self.adapters[provider]
        available = adapter.is_available()
        
        self.availability_cache[provider] = (available, datetime.now())
        
        return available
    
    def _try_fallback(self, failed_provider: str, error_msg: str) -> Optional[str]:
        logger.warning(f"Provider '{failed_provider}' falló: {error_msg}")
        
        if not self.config.auto_fallback:
            logger.info("Auto-fallback desactivado")
            return None
        
        fallback_providers = [p for p in self.config.fallback_order if p != failed_provider]
        
        for provider in fallback_providers:
            if provider in self.adapters:
                logger.info(f"Intentando fallback a '{provider}'...")
                if self._is_provider_available(provider, use_cache=False):
                    self.current_provider = provider
                    logger.info(f"✓ Fallback exitoso a '{provider}'")
                    return provider
        
        logger.error("No hay providers de fallback disponibles")
        return None
    
    @RateLimiter(max_calls=20, period=60)
    def generate(self, messages: List[Dict], **kwargs) -> str:
        if not self.current_provider:
            raise RuntimeError(
                "No hay providers LLM disponibles.\n"
                "Verifica la configuración y que al menos un provider esté activo."
            )
        
        adapter = self.adapters[self.current_provider]
        
        try:
            if TELEMETRY_AVAILABLE:
                telemetry = get_telemetry()
                with telemetry.trace_operation("llm.generate", {
                    "provider": self.current_provider,
                    "messages_count": len(messages)
                }):
                    logger.debug(f"Generando respuesta con {self.current_provider}...")
                    response = adapter.generate(messages, **kwargs)
                    telemetry.record_request("generate", "success")
                    return response
            else:
                logger.debug(f"Generando respuesta con {self.current_provider}...")
                response = adapter.generate(messages, **kwargs)
                return response
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error en {self.current_provider}: {error_msg}")
            
            if TELEMETRY_AVAILABLE:
                telemetry = get_telemetry()
                telemetry.record_request("generate", "error")
            
            fallback_provider = self._try_fallback(self.current_provider, error_msg)
            
            if fallback_provider:
                try:
                    fallback_adapter = self.adapters[fallback_provider]
                    logger.info(f"Reintentando con {fallback_provider}...")
                    response = fallback_adapter.generate(messages, **kwargs)
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback a {fallback_provider} también falló: {fallback_error}")
            
            raise RuntimeError(
                f"Fallo en provider principal '{self.current_provider}': {error_msg}\n"
                f"No hay providers de fallback disponibles.\n"
                f"Sugerencias:\n"
                f"- Si usas Groq, verifica tu API key\n"
                f"- Si usas Ollama, verifica que esté corriendo: ollama serve\n"
                f"- Revisa los logs para más detalles"
            )
    
    def stream_generate(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        if not self.current_provider:
            raise RuntimeError("No hay providers LLM disponibles")
        
        adapter = self.adapters[self.current_provider]
        
        try:
            for chunk in adapter.stream_generate(messages, **kwargs):
                yield chunk
        except Exception as e:
            logger.error(f"Error en streaming con {self.current_provider}: {e}")
            raise
    
    def switch_provider(self, provider: str) -> bool:
        if provider not in self.adapters:
            logger.error(f"Provider '{provider}' no existe")
            return False
        
        if not self._is_provider_available(provider, use_cache=False):
            logger.error(f"Provider '{provider}' no está disponible")
            return False
        
        old_provider = self.current_provider
        self.current_provider = provider
        logger.info(f"Provider cambiado: {old_provider} → {provider}")
        return True
    
    def get_available_providers(self) -> List[str]:
        available = []
        for provider in self.adapters.keys():
            if self._is_provider_available(provider, use_cache=False):
                available.append(provider)
        return available
    
    def get_current_provider(self) -> str:
        return self.current_provider or "ninguno"
    
    def get_stats(self) -> Dict:
        stats = {
            'current_provider': self.current_provider,
            'available_providers': self.get_available_providers(),
            'all_providers': list(self.adapters.keys()),
            'auto_fallback': self.config.auto_fallback,
            'provider_stats': {}
        }
        
        for provider, adapter in self.adapters.items():
            stats['provider_stats'][provider] = adapter.get_stats()
        
        return stats
    
    def test_provider(self, provider: str) -> Dict:
        if provider not in self.adapters:
            return {
                'provider': provider,
                'available': False,
                'error': 'Provider no existe'
            }
        
        adapter = self.adapters[provider]
        available = self._is_provider_available(provider, use_cache=False)
        
        result = {
            'provider': provider,
            'available': available,
            'stats': adapter.get_stats()
        }
        
        if available:
            try:
                test_messages = [{"role": "user", "content": "Hola, este es un test"}]
                response = adapter.generate(test_messages)
                result['test_success'] = True
                result['test_response_length'] = len(response)
            except Exception as e:
                result['test_success'] = False
                result['test_error'] = str(e)
        
        return result
