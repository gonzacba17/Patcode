"""
Sistema de configuración para PatCode.

Este módulo centraliza toda la configuración del proyecto,
cargándola desde variables de entorno con valores por defecto sensatos.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


@dataclass
class OllamaConfig:
    """Configuración para el servicio Ollama."""
    
    base_url: str
    model: str
    timeout: int
    
    @classmethod
    def from_env(cls) -> 'OllamaConfig':
        """
        Carga la configuración de Ollama desde variables de entorno.
        
        Returns:
            Instancia de OllamaConfig con valores cargados
        """
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
            timeout=int(os.getenv("REQUEST_TIMEOUT", "60"))
        )
    
    def validate(self) -> None:
        """
        Valida la configuración.
        
        Raises:
            ValueError: Si algún valor es inválido
        """
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"OLLAMA_BASE_URL debe ser una URL válida: {self.base_url}")
        
        if self.timeout < 1:
            raise ValueError(f"REQUEST_TIMEOUT debe ser positivo: {self.timeout}")
        
        if not self.model:
            raise ValueError("OLLAMA_MODEL no puede estar vacío")


@dataclass
class MemoryConfig:
    """Configuración para el sistema de memoria."""
    
    path: Path
    context_size: int
    max_size: int
    
    @classmethod
    def from_env(cls) -> 'MemoryConfig':
        """
        Carga la configuración de memoria desde variables de entorno.
        
        Returns:
            Instancia de MemoryConfig con valores cargados
        """
        return cls(
            path=Path(os.getenv("MEMORY_PATH", "./data/memory/memory.json")),
            context_size=int(os.getenv("CONTEXT_WINDOW_SIZE", "5")),
            max_size=int(os.getenv("MAX_MEMORY_SIZE", "1000"))
        )
    
    def validate(self) -> None:
        """
        Valida la configuración.
        
        Raises:
            ValueError: Si algún valor es inválido
        """
        if self.context_size < 1:
            raise ValueError(f"CONTEXT_WINDOW_SIZE debe ser positivo: {self.context_size}")
        
        if self.max_size < 1:
            raise ValueError(f"MAX_MEMORY_SIZE debe ser positivo: {self.max_size}")
        
        if self.context_size > self.max_size:
            raise ValueError(
                f"CONTEXT_WINDOW_SIZE ({self.context_size}) no puede ser mayor "
                f"que MAX_MEMORY_SIZE ({self.max_size})"
            )


@dataclass
class ValidationConfig:
    """Configuración para validación de inputs."""
    
    max_prompt_length: int
    min_prompt_length: int
    
    @classmethod
    def from_env(cls) -> 'ValidationConfig':
        """
        Carga la configuración de validación desde variables de entorno.
        
        Returns:
            Instancia de ValidationConfig con valores cargados
        """
        return cls(
            max_prompt_length=int(os.getenv("MAX_PROMPT_LENGTH", "10000")),
            min_prompt_length=int(os.getenv("MIN_PROMPT_LENGTH", "1"))
        )
    
    def validate(self) -> None:
        """
        Valida la configuración.
        
        Raises:
            ValueError: Si algún valor es inválido
        """
        if self.min_prompt_length < 1:
            raise ValueError(f"MIN_PROMPT_LENGTH debe ser positivo: {self.min_prompt_length}")
        
        if self.max_prompt_length < self.min_prompt_length:
            raise ValueError(
                f"MAX_PROMPT_LENGTH ({self.max_prompt_length}) debe ser mayor "
                f"que MIN_PROMPT_LENGTH ({self.min_prompt_length})"
            )


@dataclass
class LoggingConfig:
    """Configuración para el sistema de logging."""
    
    level: str
    file: Optional[Path]
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """
        Carga la configuración de logging desde variables de entorno.
        
        Returns:
            Instancia de LoggingConfig con valores cargados
        """
        log_file_str = os.getenv("LOG_FILE")
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            file=Path(log_file_str) if log_file_str else None
        )
    
    def validate(self) -> None:
        """
        Valida la configuración.
        
        Raises:
            ValueError: Si algún valor es inválido
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL debe ser uno de {valid_levels}: {self.level}"
            )


@dataclass
class Settings:
    """Configuración global de PatCode."""
    
    ollama: OllamaConfig
    memory: MemoryConfig
    validation: ValidationConfig
    logging: LoggingConfig
    
    @classmethod
    def load(cls) -> 'Settings':
        """
        Carga toda la configuración desde variables de entorno.
        
        Returns:
            Instancia de Settings con toda la configuración cargada
            
        Raises:
            ValueError: Si alguna configuración es inválida
        """
        ollama_config = OllamaConfig.from_env()
        memory_config = MemoryConfig.from_env()
        validation_config = ValidationConfig.from_env()
        logging_config = LoggingConfig.from_env()
        
        # Validar todas las configuraciones
        ollama_config.validate()
        memory_config.validate()
        validation_config.validate()
        logging_config.validate()
        
        return cls(
            ollama=ollama_config,
            memory=memory_config,
            validation=validation_config,
            logging=logging_config
        )
    
    def __str__(self) -> str:
        """Representación en string de la configuración (ocultando datos sensibles)."""
        return (
            f"Settings(\n"
            f"  Ollama: {self.ollama.base_url} | Model: {self.ollama.model}\n"
            f"  Memory: {self.memory.path} | Context: {self.memory.context_size}\n"
            f"  Logging: {self.logging.level}\n"
            f")"
        )


# Instancia global de configuración
# Esta se carga automáticamente al importar el módulo
try:
    settings = Settings.load()
except Exception as e:
    # Si falla la carga, crear configuración por defecto
    print(f"⚠️  Advertencia: Error al cargar configuración: {e}")
    print("📝 Usando valores por defecto. Crea un archivo .env para personalizarla.")
    
    # Configuración fallback
    settings = Settings(
        ollama=OllamaConfig(
            base_url="http://localhost:11434",
            model="llama3.2:latest",
            timeout=60
        ),
        memory=MemoryConfig(
            path=Path("./data/memory/memory.json"),
            context_size=5,
            max_size=1000
        ),
        validation=ValidationConfig(
            max_prompt_length=10000,
            min_prompt_length=1
        ),
        logging=LoggingConfig(
            level="INFO",
            file=Path("./logs/patcode.log")
        )
    )