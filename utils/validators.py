"""
Validadores de entrada para PatCode.

Este módulo contiene funciones y clases para validar inputs del usuario,
asegurando que cumplan con los requisitos antes de procesarlos.
"""

from typing import List
from config import settings
from exceptions import InvalidPromptError


class InputValidator:
    """Validador de inputs del usuario."""
    
    # Caracteres considerados peligrosos o problemáticos
    DANGEROUS_CHARS: List[str] = [
        '\x00',  # Null byte
        '\x1a',  # EOF en algunos sistemas
    ]
    
    @staticmethod
    def validate_prompt(prompt: str) -> str:
        """
        Valida un prompt del usuario.
        
        Realiza las siguientes validaciones:
        1. Limpia espacios al inicio y final
        2. Verifica longitud mínima
        3. Verifica longitud máxima
        4. Detecta caracteres peligrosos
        
        Args:
            prompt: Texto ingresado por el usuario
            
        Returns:
            Prompt limpio y validado
            
        Raises:
            InvalidPromptError: Si el prompt no cumple los requisitos
            
        Examples:
            >>> InputValidator.validate_prompt("  Hola  ")
            "Hola"
            
            >>> InputValidator.validate_prompt("")
            InvalidPromptError: El prompt no puede estar vacío
        """
        # 1. Limpiar espacios
        cleaned_prompt = prompt.strip()
        
        # 2. Validar longitud mínima
        if len(cleaned_prompt) < settings.validation.min_prompt_length:
            raise InvalidPromptError(
                "El prompt no puede estar vacío"
            )
        
        # 3. Validar longitud máxima
        if len(cleaned_prompt) > settings.validation.max_prompt_length:
            raise InvalidPromptError(
                f"El prompt excede el límite de "
                f"{settings.validation.max_prompt_length} caracteres. "
                f"Longitud actual: {len(cleaned_prompt)}"
            )
        
        # 4. Detectar caracteres peligrosos
        dangerous_found = [
            char for char in InputValidator.DANGEROUS_CHARS 
            if char in cleaned_prompt
        ]
        
        if dangerous_found:
            raise InvalidPromptError(
                f"El prompt contiene caracteres no permitidos: "
                f"{[repr(c) for c in dangerous_found]}"
            )
        
        return cleaned_prompt
    
    @staticmethod
    def is_command(text: str) -> bool:
        """
        Verifica si el texto es un comando especial.
        
        Args:
            text: Texto a verificar
            
        Returns:
            True si es un comando, False en caso contrario
            
        Examples:
            >>> InputValidator.is_command("/quit")
            True
            
            >>> InputValidator.is_command("Hola")
            False
        """
        text = text.strip().lower()
        return text.startswith('/')
    
    @staticmethod
    def parse_command(text: str) -> tuple[str, str]:
        """
        Parsea un comando separando el comando de sus argumentos.
        
        Args:
            text: Texto del comando
            
        Returns:
            Tupla (comando, argumentos)
            
        Examples:
            >>> InputValidator.parse_command("/help me")
            ("/help", "me")
            
            >>> InputValidator.parse_command("/quit")
            ("/quit", "")
        """
        text = text.strip()
        parts = text.split(maxsplit=1)
        
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        return command, args


class MemoryValidator:
    """Validador para datos de memoria."""
    
    @staticmethod
    def validate_history_entry(entry: dict) -> bool:
        """
        Valida que una entrada del historial tenga el formato correcto.
        
        Args:
            entry: Diccionario con una entrada del historial
            
        Returns:
            True si es válida, False en caso contrario
            
        Examples:
            >>> MemoryValidator.validate_history_entry(
            ...     {"role": "user", "content": "Hola"}
            ... )
            True
        """
        if not isinstance(entry, dict):
            return False
        
        # Debe tener las claves necesarias
        required_keys = {"role", "content"}
        if not required_keys.issubset(entry.keys()):
            return False
        
        # role debe ser 'user' o 'assistant'
        if entry["role"] not in ["user", "assistant"]:
            return False
        
        # content debe ser string no vacío
        if not isinstance(entry["content"], str) or not entry["content"].strip():
            return False
        
        return True
    
    @staticmethod
    def validate_history(history: list) -> bool:
        """
        Valida que un historial completo sea válido.
        
        Args:
            history: Lista con el historial completo
            
        Returns:
            True si es válido, False en caso contrario
        """
        if not isinstance(history, list):
            return False
        
        # Validar cada entrada
        return all(
            MemoryValidator.validate_history_entry(entry) 
            for entry in history
        )


# Funciones de utilidad para validación rápida

def validate_and_clean_prompt(prompt: str) -> str:
    """
    Función de conveniencia para validar y limpiar un prompt.
    
    Args:
        prompt: Prompt a validar
        
    Returns:
        Prompt validado y limpio
        
    Raises:
        InvalidPromptError: Si el prompt es inválido
    """
    return InputValidator.validate_prompt(prompt)


def is_special_command(text: str) -> bool:
    """
    Función de conveniencia para verificar si es un comando especial.
    
    Args:
        text: Texto a verificar
        
    Returns:
        True si es comando, False en caso contrario
    """
    return InputValidator.is_command(text)