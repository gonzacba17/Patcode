"""
Fixtures compartidos para todos los tests de PatCode.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock
from typing import Generator

from config import Settings, OllamaConfig, MemoryConfig, ValidationConfig, LoggingConfig


@pytest.fixture
def temp_memory_file(tmp_path: Path) -> Path:
    """
    Crea un archivo temporal para memoria en tests.
    
    Args:
        tmp_path: Path temporal de pytest
        
    Returns:
        Path al archivo de memoria temporal
    """
    memory_file = tmp_path / "test_memory.json"
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    return memory_file


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Path:
    """
    Crea un archivo temporal para logs en tests.
    
    Args:
        tmp_path: Path temporal de pytest
        
    Returns:
        Path al archivo de log temporal
    """
    log_file = tmp_path / "test.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


@pytest.fixture
def mock_ollama_config() -> OllamaConfig:
    """Configuración de Ollama para tests."""
    return OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3.2:latest",
        timeout=30
    )


@pytest.fixture
def mock_memory_config(temp_memory_file: Path) -> MemoryConfig:
    """Configuración de memoria para tests."""
    return MemoryConfig(
        path=temp_memory_file,
        context_size=5,
        max_size=100
    )


@pytest.fixture
def mock_validation_config() -> ValidationConfig:
    """Configuración de validación para tests."""
    return ValidationConfig(
        max_prompt_length=10000,
        min_prompt_length=1
    )


@pytest.fixture
def mock_logging_config(temp_log_file: Path) -> LoggingConfig:
    """Configuración de logging para tests."""
    return LoggingConfig(
        level="DEBUG",
        file=temp_log_file
    )


@pytest.fixture
def mock_settings(
    mock_ollama_config: OllamaConfig,
    mock_memory_config: MemoryConfig,
    mock_validation_config: ValidationConfig,
    mock_logging_config: LoggingConfig
) -> Settings:
    """Settings completo para tests."""
    return Settings(
        ollama=mock_ollama_config,
        memory=mock_memory_config,
        validation=mock_validation_config,
        logging=mock_logging_config
    )


@pytest.fixture
def sample_history() -> list:
    """Historial de ejemplo para tests."""
    return [
        {"role": "user", "content": "¿Qué es Python?"},
        {"role": "assistant", "content": "Python es un lenguaje de programación..."},
        {"role": "user", "content": "Dame un ejemplo"},
        {"role": "assistant", "content": "Aquí un ejemplo:\nprint('Hola')"},
    ]


@pytest.fixture
def mock_ollama_response() -> dict:
    """Respuesta de ejemplo de Ollama."""
    return {
        "model": "llama3.2:latest",
        "created_at": "2024-10-14T12:00:00Z",
        "response": "Esta es una respuesta de prueba del modelo.",
        "done": True
    }


@pytest.fixture
def mock_requests_post(mocker, mock_ollama_response: dict):
    """
    Mock de requests.post que simula respuestas de Ollama.
    
    Args:
        mocker: Fixture de pytest-mock
        mock_ollama_response: Respuesta de ejemplo
        
    Returns:
        Mock configurado
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ollama_response
    mock_response.raise_for_status = Mock()
    
    mock_post = mocker.patch('requests.post', return_value=mock_response)
    return mock_post


@pytest.fixture(autouse=True)
def mock_settings_in_modules(monkeypatch, mock_settings: Settings):
    """
    Automáticamente mockea settings en todos los tests.
    
    Esto evita que los tests usen la configuración real del sistema.
    """
    monkeypatch.setattr('config.settings', mock_settings)
    # También en los módulos que importan settings
    monkeypatch.setattr('agents.pat_agent.settings', mock_settings)
    monkeypatch.setattr('validators.settings', mock_settings)


@pytest.fixture
def populated_memory_file(temp_memory_file: Path, sample_history: list) -> Path:
    """
    Crea un archivo de memoria pre-populado con datos de prueba.
    
    Args:
        temp_memory_file: Path al archivo temporal
        sample_history: Historial de ejemplo
        
    Returns:
        Path al archivo populado
    """
    with open(temp_memory_file, 'w', encoding='utf-8') as f:
        json.dump(sample_history, f, indent=2)
    return temp_memory_file