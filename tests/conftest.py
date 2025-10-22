"""Configuración global de pytest y fixtures"""

import pytest
import sys
import platform
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """
    Registrar markers personalizados ANTES de la colección de tests.
    Esto debe ejecutarse ANTES de pytest_collection_modifyitems.
    """
    # Registrar todos los markers
    config.addinivalue_line(
        "markers", 
        "ui: Tests de interfaz de usuario (requieren consola interactiva)"
    )
    config.addinivalue_line(
        "markers", 
        "integration: Tests de integración (requieren servicios externos)"
    )
    config.addinivalue_line(
        "markers", 
        "requires_ollama: Tests que requieren Ollama corriendo en localhost:11434"
    )
    config.addinivalue_line(
        "markers", 
        "obsolete: Tests obsoletos que necesitan actualización de API"
    )
    config.addinivalue_line(
        "markers", 
        "slow: Tests lentos (>5 segundos)"
    )
    config.addinivalue_line(
        "markers",
        "unit: Tests unitarios rápidos"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modifica automáticamente items de test según el entorno.
    Esto permite skip automático de tests incompatibles.
    """
    
    # Markers para skip automático
    skip_ui_windows = pytest.mark.skip(
        reason="UI tests requieren consola interactiva (incompatible con pytest en Windows)"
    )
    
    skip_requires_ollama = pytest.mark.skip(
        reason="Test requiere Ollama corriendo en localhost:11434"
    )
    
    skip_obsolete = pytest.mark.skip(
        reason="Test obsoleto - requiere actualización de API"
    )
    
    skip_git_windows = pytest.mark.skip(
        reason="Git tests tienen issues de permisos en Windows"
    )
    
    # Verificar si Ollama está disponible
    ollama_available = False
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        ollama_available = response.status_code == 200
    except:
        pass
    
    # Procesar cada test
    for item in items:
        test_file = str(item.fspath)
        test_name = item.name
        
        # Skip tests de UI en Windows (prompt_toolkit issues)
        if platform.system() == "Windows":
            if "test_rich_ui" in test_file or "streaming_display" in test_name:
                item.add_marker(skip_ui_windows)
        
        # Skip tests que requieren Ollama si no está disponible
        if not ollama_available:
            if "requires_ollama" in [marker.name for marker in item.iter_markers()]:
                item.add_marker(skip_requires_ollama)
        
        # Skip tests obsoletos automáticamente (solo si tienen el marker)
        if "obsolete" in [marker.name for marker in item.iter_markers()]:
            item.add_marker(skip_obsolete)
        
        # Skip tests de Git con permisos en Windows
        if platform.system() == "Windows" and "test_git_plugin" in test_file:
            item.add_marker(skip_git_windows)


# =====================================================================
# FIXTURES COMPARTIDAS
# =====================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Directorio temporal para tests"""
    return tmp_path


@pytest.fixture
def mock_settings():
    """Settings mockeados para tests"""
    from unittest.mock import Mock
    
    settings = Mock()
    settings.ollama = Mock()
    settings.ollama.base_url = "http://localhost:11434"
    settings.ollama.model = "test-model"
    settings.ollama.temperature = 0.7
    settings.ollama.timeout = 30
    
    return settings


@pytest.fixture
def mock_ollama_response():
    """Mock de respuesta de Ollama"""
    return {
        "model": "test-model",
        "created_at": "2024-01-01T00:00:00Z",
        "response": "Test response from Ollama",
        "done": True
    }