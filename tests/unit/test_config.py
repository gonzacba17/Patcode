import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from config.settings import Settings


class TestSettings:
    
    def test_settings_initialization(self):
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            assert settings is not None
    
    def test_ollama_settings_defaults(self):
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            assert hasattr(settings, 'ollama')
            assert settings.ollama.base_url is not None
    
    def test_memory_settings(self):
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            assert hasattr(settings, 'memory')
            assert settings.memory.max_active_messages > 0
    
    def test_logging_settings(self):
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            assert hasattr(settings, 'logging')
            assert settings.logging.level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
