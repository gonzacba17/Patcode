"""
Provider Manager - FASE 2: Sistema Multi-LLM

Orquestador principal que gestiona múltiples providers LLM
con fallback automático y estrategias inteligentes.
"""

import logging
from typing import Optional, List, Dict, Any

from llm.base_client import BaseLLMClient, LLMResponse, LLMError
from llm.ollama_client import OllamaClient
from llm.groq_client import GroqClient
from llm.together_client import TogetherClient


logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Gestor de múltiples providers LLM.
    
    Características:
    - Fallback automático entre providers
    - Estrategias por tipo de tarea
    - Gestión de rate limits
    - Logging detallado
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el gestor de providers.
        
        Args:
            config: Configuración
                {
                    "providers": {
                        "ollama": {...},
                        "groq": {...},
                        "together": {...}
                    },
                    "strategies": {
                        "simple": ["ollama"],
                        "complex": ["groq", "ollama"],
                        "code_generation": ["groq", "ollama"]
                    }
                }
        """
        self.config = config
        self.clients: Dict[str, BaseLLMClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Inicializa todos los clientes habilitados."""
        providers_config = self.config.get("providers", {})
        
        for provider_name, provider_config in providers_config.items():
            if not provider_config.get("enabled", False):
                logger.info(f"⏭️  {provider_name} disabled in config")
                continue
            
            try:
                if provider_name == "ollama":
                    self.clients[provider_name] = OllamaClient(provider_config)
                elif provider_name == "groq":
                    self.clients[provider_name] = GroqClient(provider_config)
                elif provider_name == "together":
                    self.clients[provider_name] = TogetherClient(provider_config)
                else:
                    logger.warning(f"⚠️  Unknown provider: {provider_name}")
                    continue
                
                logger.info(f"✅ {provider_name} client initialized")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize {provider_name}: {e}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        strategy: str = "simple",
        preferred_provider: Optional[str] = None
    ) -> LLMResponse:
        """
        Genera una respuesta usando la estrategia especificada.
        
        Args:
            prompt: El prompt para el LLM
            system_prompt: System prompt opcional
            strategy: "simple", "complex", "code_generation"
            preferred_provider: Provider específico a usar (ignora estrategia)
            
        Returns:
            LLMResponse con la respuesta
            
        Raises:
            LLMError: Si todos los providers fallan
        """
        if preferred_provider:
            providers_to_try = [preferred_provider]
            logger.info(f"Using preferred provider: {preferred_provider}")
        else:
            strategies = self.config.get("strategies", {})
            providers_to_try = strategies.get(strategy, ["ollama"])
            logger.info(f"Using strategy '{strategy}': {providers_to_try}")
        
        errors = []
        
        for provider_name in providers_to_try:
            if provider_name not in self.clients:
                logger.warning(f"⚠️  Provider {provider_name} not available, skipping")
                continue
            
            client = self.clients[provider_name]
            
            try:
                logger.info(f"🤖 Trying {provider_name}...")
                
                response = client.generate(prompt, system_prompt)
                
                logger.info(f"✅ {provider_name} succeeded")
                return response
                
            except LLMError as e:
                logger.warning(f"❌ {provider_name} failed: {e.error_type} - {e.message}")
                errors.append(e)
                
                if e.error_type == "rate_limit":
                    logger.info(f"⏭️  Rate limit hit, trying next provider...")
                    continue
                
                if e.error_type in ["connection_error", "timeout", "api_error"]:
                    logger.info(f"⏭️  Error occurred, trying next provider...")
                    continue
                
                continue
            
            except Exception as e:
                logger.error(f"❌ Unexpected error with {provider_name}: {e}")
                errors.append(LLMError(
                    provider=provider_name,
                    error_type="unexpected_error",
                    message=str(e)
                ))
                continue
        
        error_summary = "\n".join([f"- {e.provider}: {e.message}" for e in errors])
        raise LLMError(
            provider="all",
            error_type="all_failed",
            message=f"All providers failed:\n{error_summary}"
        )
    
    def get_available_providers(self) -> List[str]:
        """
        Retorna lista de providers disponibles.
        
        Returns:
            Lista de nombres de providers disponibles
        """
        available = []
        for name, client in self.clients.items():
            if client.is_available():
                available.append(name)
        return available
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna estado de todos los providers.
        
        Returns:
            Dict con estado de cada provider
        """
        status = {}
        for name, client in self.clients.items():
            try:
                status[name] = {
                    "available": client.is_available(),
                    "model": client.model,
                    "rate_limit": client.get_rate_limit_status()
                }
            except Exception as e:
                status[name] = {
                    "available": False,
                    "error": str(e)
                }
        return status
    
    def set_strategy(self, strategy_name: str, providers: List[str]) -> None:
        """
        Configura una estrategia personalizada.
        
        Args:
            strategy_name: Nombre de la estrategia
            providers: Lista de providers en orden de prioridad
        """
        if "strategies" not in self.config:
            self.config["strategies"] = {}
        
        self.config["strategies"][strategy_name] = providers
        logger.info(f"Strategy '{strategy_name}' set to: {providers}")
    
    def get_strategies(self) -> Dict[str, List[str]]:
        """
        Retorna todas las estrategias configuradas.
        
        Returns:
            Dict con estrategias
        """
        return self.config.get("strategies", {})
