"""
DEPRECATED: Este archivo ha sido marcado como obsoleto.

Usar agents/llm_manager.py en su lugar, que consolida toda
la funcionalidad de gestión de providers LLM.

Este archivo se mantendrá temporalmente para compatibilidad
pero será eliminado en futuras versiones.

Fecha de deprecación: 2025-10-18
Versión de eliminación planeada: 0.4.0
"""

import warnings
warnings.warn(
    "llm.provider_manager está deprecated. Usar agents.llm_manager.LLMManager en su lugar",
    DeprecationWarning,
    stacklevel=2
)

from llm.provider_manager import ProviderManager as _ProviderManagerDeprecated

ProviderManager = _ProviderManagerDeprecated
