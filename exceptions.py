"""
Excepciones personalizadas para PatCode.

Este módulo define todas las excepciones custom del proyecto,
organizadas jerárquicamente desde una clase base.
"""


class PatCodeError(Exception):
    """Excepción base para todos los errores de PatCode."""
    pass


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

class MemoryError(PatCodeError):
    """Excepción base para errores de memoria/persistencia."""
    pass


class MemoryReadError(MemoryError):
    """Error al leer el archivo de memoria."""
    pass


class MemoryWriteError(MemoryError):
    """Error al escribir en el archivo de memoria."""
    pass


class MemoryCorruptedError(MemoryError):
    """El archivo de memoria está corrupto."""
    pass


# ==================== Errores de Configuración ====================

class ConfigurationError(PatCodeError):
    """Error en la configuración del sistema."""
    pass