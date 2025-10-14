"""
Validadores de entrada para PatCode.

Este módulo contiene funciones y clases para validar inputs del usuario,
asegurando que cumplan con los requisitos antes de procesarlos.
"""

import re
import json
from pathlib import Path
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


# ============================================================================
# FUNCIONES DE VALIDACIÓN ADICIONALES
# ============================================================================

def validate_file_path(file_path: str) -> Path:
    """
    Valida y normaliza una ruta de archivo.
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        Path objeto validado y resuelto
        
    Raises:
        ValueError: Si la ruta es inválida o peligrosa
    """
    # Convertir a Path
    path = Path(file_path).resolve()
    
    # Verificar rutas bloqueadas
    path_str = str(path)
    for blocked in settings.security.blocked_paths:
        if blocked in path_str:
            raise ValueError(f"Ruta bloqueada por seguridad: {blocked}")
    
    return path


def validate_directory_path(dir_path: str) -> Path:
    """
    Valida que una ruta sea un directorio válido.
    
    Args:
        dir_path: Ruta del directorio a validar
        
    Returns:
        Path objeto validado
        
    Raises:
        ValueError: Si no es un directorio válido
    """
    path = validate_file_path(dir_path)
    
    if path.exists() and not path.is_dir():
        raise ValueError(f"La ruta no es un directorio: {path}")
    
    return path


def validate_command(command: str) -> str:
    """
    Valida que un comando sea seguro de ejecutar.
    
    Args:
        command: Comando a validar
        
    Returns:
        Comando validado
        
    Raises:
        ValueError: Si el comando está bloqueado
    """
    command = command.strip()
    
    if not command:
        raise ValueError("El comando no puede estar vacío")
    
    # Extraer el comando base (primera palabra)
    base_command = command.split()[0]
    
    # Verificar si está bloqueado
    if base_command in settings.security.blocked_commands:
        raise ValueError(f"Comando bloqueado por seguridad: {base_command}")
    
    # Verificar si está en la whitelist
    if settings.security.allowed_commands:
        if base_command not in settings.security.allowed_commands:
            raise ValueError(
                f"Comando no permitido: {base_command}. "
                f"Solo se permiten comandos de la whitelist."
            )
    
    return command


def validate_model_name(model_name: str) -> str:
    """
    Valida el nombre de un modelo LLM.
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        Nombre del modelo validado
        
    Raises:
        ValueError: Si el nombre es inválido
    """
    model_name = model_name.strip()
    
    if not model_name:
        raise ValueError("El nombre del modelo no puede estar vacío")
    
    # Validar formato básico (letras, números, guiones, dos puntos, puntos)
    if not re.match(r'^[a-zA-Z0-9\-:.]+$', model_name):
        raise ValueError(
            f"Nombre de modelo inválido: {model_name}. "
            f"Solo se permiten letras, números, guiones, dos puntos y puntos."
        )
    
    return model_name


def validate_url(url: str) -> str:
    """
    Valida una URL básicamente.
    
    Args:
        url: URL a validar
        
    Returns:
        URL validada
        
    Raises:
        ValueError: Si la URL es inválida
    """
    url = url.strip()
    
    if not url:
        raise ValueError("La URL no puede estar vacía")
    
    # Validación básica de formato
    if not re.match(r'^https?://.+', url):
        raise ValueError(
            f"URL inválida: {url}. Debe comenzar con http:// o https://"
        )
    
    return url


def validate_port(port: int) -> int:
    """
    Valida un número de puerto.
    
    Args:
        port: Número de puerto
        
    Returns:
        Puerto validado
        
    Raises:
        ValueError: Si el puerto es inválido
    """
    if not isinstance(port, int):
        raise ValueError(f"El puerto debe ser un número entero, recibido: {type(port)}")
    
    if port < 1 or port > 65535:
        raise ValueError(f"Puerto fuera de rango (1-65535): {port}")
    
    return port


def validate_file_extension(filename: str, allowed_extensions: List[str] = None) -> str:
    """
    Valida que un archivo tenga una extensión permitida.
    
    Args:
        filename: Nombre del archivo
        allowed_extensions: Lista de extensiones permitidas (opcional)
        
    Returns:
        Nombre de archivo validado
        
    Raises:
        ValueError: Si la extensión no está permitida
    """
    if allowed_extensions is None:
        allowed_extensions = settings.files.allowed_extensions
    
    path = Path(filename)
    extension = path.suffix.lower()
    
    if not extension:
        raise ValueError(f"El archivo no tiene extensión: {filename}")
    
    if extension not in allowed_extensions:
        raise ValueError(
            f"Extensión no permitida: {extension}. "
            f"Extensiones válidas: {', '.join(allowed_extensions[:10])}..."
        )
    
    return filename


def validate_json_string(json_str: str) -> dict:
    """
    Valida que un string sea JSON válido.
    
    Args:
        json_str: String JSON a validar
        
    Returns:
        Diccionario parseado
        
    Raises:
        ValueError: Si el JSON es inválido
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}")


def validate_config(config: dict) -> dict:
    """
    Valida un diccionario de configuración.
    
    Args:
        config: Diccionario de configuración
        
    Returns:
        Configuración validada
        
    Raises:
        ValueError: Si la configuración es inválida
    """
    if not isinstance(config, dict):
        raise ValueError("La configuración debe ser un diccionario")
    
    # Aquí se pueden agregar validaciones específicas según necesidad
    return config


def sanitize_input(input_str: str) -> str:
    """
    Sanitiza un input eliminando caracteres peligrosos.
    
    Args:
        input_str: String a sanitizar
        
    Returns:
        String sanitizado
    """
    # Eliminar caracteres null y de control
    sanitized = input_str.replace('\x00', '').replace('\x1a', '')
    
    # Eliminar caracteres de control excepto tabs, newlines y returns
    sanitized = ''.join(
        char for char in sanitized 
        if char >= ' ' or char in '\t\n\r'
    )
    
    return sanitized


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

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