"""
Tests unitarios para el módulo validators.
"""

import pytest
from utils.validators import InputValidator, MemoryValidator
from exceptions import InvalidPromptError


class TestInputValidator:
    """Tests para InputValidator."""
    
    def test_validate_prompt_normal(self):
        """Test: prompt válido debe retornar limpio."""
        prompt = "Explica qué es Python"
        result = InputValidator.validate_prompt(prompt)
        assert result == "Explica qué es Python"
    
    def test_validate_prompt_with_whitespace(self):
        """Test: prompt con espacios debe limpiarlos."""
        prompt = "  Hola mundo  \n"
        result = InputValidator.validate_prompt(prompt)
        assert result == "Hola mundo"
    
    def test_validate_prompt_empty_raises_error(self):
        """Test: prompt vacío debe lanzar InvalidPromptError."""
        with pytest.raises(InvalidPromptError, match="no puede estar vacío"):
            InputValidator.validate_prompt("")
    
    def test_validate_prompt_only_spaces_raises_error(self):
        """Test: prompt solo con espacios debe lanzar error."""
        with pytest.raises(InvalidPromptError, match="no puede estar vacío"):
            InputValidator.validate_prompt("   \n\t  ")
    
    def test_validate_prompt_too_long_raises_error(self, monkeypatch):
        """Test: prompt muy largo debe lanzar error."""
        from config import settings
        monkeypatch.setattr(settings.validation, 'max_prompt_length', 50)
        
        long_prompt = "a" * 100
        with pytest.raises(InvalidPromptError, match="excede el límite"):
            InputValidator.validate_prompt(long_prompt)
    
    def test_validate_prompt_dangerous_chars_raises_error(self):
        """Test: prompt con caracteres peligrosos debe lanzar error."""
        prompt = "Hola\x00mundo"
        with pytest.raises(InvalidPromptError, match="no permitidos"):
            InputValidator.validate_prompt(prompt)
    
    def test_validate_prompt_with_special_chars_allowed(self):
        """Test: caracteres especiales normales deben ser permitidos."""
        prompt = "¿Cómo usar @decorators en Python?"
        result = InputValidator.validate_prompt(prompt)
        assert result == prompt
    
    def test_is_command_with_slash(self):
        """Test: texto que empieza con / debe ser comando."""
        assert InputValidator.is_command("/quit")
        assert InputValidator.is_command("/clear")
        assert InputValidator.is_command("/HELP")  # Case insensitive
    
    def test_is_command_without_slash(self):
        """Test: texto normal no debe ser comando."""
        assert not InputValidator.is_command("Hola")
        assert not InputValidator.is_command("¿Qué es Python?")
    
    def test_parse_command_without_args(self):
        """Test: parsear comando sin argumentos."""
        command, args = InputValidator.parse_command("/quit")
        assert command == "/quit"
        assert args == ""
    
    def test_parse_command_with_args(self):
        """Test: parsear comando con argumentos."""
        command, args = InputValidator.parse_command("/help me please")
        assert command == "/help"
        assert args == "me please"