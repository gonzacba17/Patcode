"""
Módulo de configuración de PatCode
"""
from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    WORKSPACE_DIR,
    MAX_HISTORY_MESSAGES,
    STREAM_RESPONSES,
    REQUEST_TIMEOUT,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    MEMORY_FILE
)

from config.prompts import (
    SYSTEM_PROMPT,
    TOOL_USE_PROMPT,
    CODING_ASSISTANT_PROMPT,
    ERROR_PROMPT
)

from config.models import (
    AVAILABLE_MODELS,
    get_model_info,
    recommend_model,
    is_model_installed
)

__all__ = [
    # Settings
    'OLLAMA_BASE_URL',
    'OLLAMA_MODEL',
    'WORKSPACE_DIR',
    'MAX_HISTORY_MESSAGES',
    'STREAM_RESPONSES',
    'REQUEST_TIMEOUT',
    'MAX_FILE_SIZE',
    'ALLOWED_EXTENSIONS',
    'MEMORY_FILE',
    
    # Prompts
    'SYSTEM_PROMPT',
    'TOOL_USE_PROMPT',
    'CODING_ASSISTANT_PROMPT',
    'ERROR_PROMPT',
    
    # Models
    'AVAILABLE_MODELS',
    'get_model_info',
    'recommend_model',
    'is_model_installed'
]