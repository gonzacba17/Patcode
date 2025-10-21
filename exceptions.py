"""
Excepciones personalizadas para PatCode.

Este módulo define todas las excepciones custom del proyecto,
organizadas jerárquicamente desde una clase base.
"""


class PatCodeError(Exception):
    """Excepción base para todos los errores de PatCode."""
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


# ==================== Errores de Ollama ====================

class OllamaError(PatCodeError):
    """Excepción base para errores relacionados con Ollama."""
    pass


class OllamaConnectionError(OllamaError):
    """Error al intentar conectar con el servidor Ollama."""
    pass


class OllamaTimeoutError(OllamaError):
    """Timeout al esperar respuesta de Ollama."""
    pass


class OllamaModelNotFoundError(OllamaError):
    """El modelo solicitado no está disponible en Ollama."""
    pass


class OllamaResponseError(OllamaError):
    """Error al procesar la respuesta de Ollama."""
    pass


# ==================== Errores de Validación ====================

class ValidationError(PatCodeError):
    """Excepción base para errores de validación."""
    pass


class InvalidPromptError(ValidationError):
    """El prompt proporcionado no es válido."""
    pass


class InvalidConfigurationError(ValidationError):
    """La configuración proporcionada no es válida."""
    pass


# ==================== Errores de Memoria ====================

class PatCodeMemoryError(PatCodeError):
    """Excepción base para errores de memoria/persistencia."""
    pass


class MemoryReadError(PatCodeMemoryError):
    """Error al leer el archivo de memoria."""
    pass


class MemoryWriteError(PatCodeMemoryError):
    """Error al escribir en el archivo de memoria."""
    pass


class MemoryCorruptedError(PatCodeMemoryError):
    """El archivo de memoria está corrupto."""
    pass


# ==================== Errores de Configuración ====================

class ConfigurationError(PatCodeError):
    """Error en la configuración del sistema."""
    pass


# ==================== Errores de LLM ====================

class LLMError(PatCodeError):
    """Excepción base para errores de LLM."""
    pass


class LLMProviderError(LLMError):
    """Error relacionado con proveedores de LLM."""
    pass


class LLMTimeoutError(LLMError):
    """Timeout en llamada a LLM."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit excedido."""
    pass