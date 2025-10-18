"""
LLM - Sistema Multi-LLM para PatCode

Provee una interfaz unificada para múltiples proveedores de LLM con
fallback automático y rate limiting.
"""

from llm.base_client import BaseLLMClient, LLMResponse, LLMError
from llm.provider_manager import ProviderManager

__all__ = [
    'BaseLLMClient',
    'LLMResponse',
    'LLMError',
    'ProviderManager'
]
