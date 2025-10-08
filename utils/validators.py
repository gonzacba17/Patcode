"""
Validadores para entradas y configuraciones
"""

import os
import re


def validate_file_path(file_path):
    """
    Valida que una ruta de archivo sea válida
    
    Args:
        file_path (str): Ruta del archivo
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    if not file_path:
        return False, "La ruta del archivo no puede estar vacía"
    
    if not isinstance(file_path, str):
        return False, "La ruta debe ser una cadena de texto"
    
    # Validar caracteres inválidos
    invalid_chars = '<>"|?*'
    if any(char in file_path for char in invalid_chars):
        return False, f"La ruta contiene caracteres inválidos: {invalid_chars}"
    
    # Validar que no sea una ruta absoluta peligrosa
    if file_path.startswith('/') and not os.path.exists(file_path):
        return False, "Ruta absoluta no encontrada"
    
    return True, ""


def validate_directory_path(dir_path):
    """
    Valida que una ruta de directorio sea válida
    
    Args:
        dir_path (str): Ruta del directorio
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    is_valid, error = validate_file_path(dir_path)
    
    if not is_valid:
        return is_valid, error
    
    if os.path.exists(dir_path) and not os.path.isdir(dir_path):
        return False, "La ruta existe pero no es un directorio"
    
    return True, ""


def validate_command(command):
    """
    Valida comandos de shell para seguridad básica
    
    Args:
        command (str): Comando a validar
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    if not command:
        return False, "El comando no puede estar vacío"
    
    if not isinstance(command, str):
        return False, "El comando debe ser una cadena de texto"
    
    # Lista de comandos potencialmente peligrosos
    dangerous_patterns = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r':\(\)\{.*\}',   # Fork bomb
        r'sudo\s+rm',     # sudo rm
        r'mkfs\.',        # Formatear disco
        r'dd\s+if=',      # dd puede ser peligroso
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return False, f"Comando potencialmente peligroso detectado"
    
    return True, ""


def validate_model_name(model_name):
    """
    Valida el nombre de un modelo de Ollama
    
    Args:
        model_name (str): Nombre del modelo
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    if not model_name:
        return False, "El nombre del modelo no puede estar vacío"
    
    if not isinstance(model_name, str):
        return False, "El nombre del modelo debe ser una cadena de texto"
    
    # Validar formato básico de modelo (nombre:tag)
    pattern = r'^[a-z0-9._-]+(?::[a-z0-9._-]+)?$'
    if not re.match(pattern, model_name):
        return False, "Formato de modelo inválido (ejemplo: llama3.2:latest)"
    
    return True, ""


def validate_url(url):
    """
    Valida una URL
    
    Args:
        url (str): URL a validar
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    if not url:
        return False, "La URL no puede estar vacía"
    
    if not isinstance(url, str):
        return False, "La URL debe ser una cadena de texto"
    
    # Patrón básico de URL
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        return False, "Formato de URL inválido"
    
    return True, ""


def validate_port(port):
    """
    Valida un número de puerto
    
    Args:
        port (int): Número de puerto
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    try:
        port = int(port)
    except (ValueError, TypeError):
        return False, "El puerto debe ser un número entero"
    
    if port < 1 or port > 65535:
        return False, "El puerto debe estar entre 1 y 65535"
    
    # Puertos reservados comunes
    reserved_ports = [22, 25, 80, 443]
    if port in reserved_ports:
        return True, f"Advertencia: puerto {port} es comúnmente reservado"
    
    return True, ""


def validate_file_extension(file_path, allowed_extensions):
    """
    Valida que un archivo tenga una extensión permitida
    
    Args:
        file_path (str): Ruta del archivo
        allowed_extensions (list): Lista de extensiones permitidas
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    if not file_path:
        return False, "La ruta del archivo no puede estar vacía"
    
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if not ext:
        return False, "El archivo no tiene extensión"
    
    allowed_extensions = [e.lower() if e.startswith('.') else f'.{e.lower()}' 
                         for e in allowed_extensions]
    
    if ext not in allowed_extensions:
        return False, f"Extensión no permitida. Permitidas: {', '.join(allowed_extensions)}"
    
    return True, ""


def validate_json_string(json_string):
    """
    Valida que una cadena sea JSON válido
    
    Args:
        json_string (str): Cadena JSON
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    import json
    
    if not json_string:
        return False, "La cadena JSON no puede estar vacía"
    
    try:
        json.loads(json_string)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON inválido: {str(e)}"


def validate_config(config_dict, required_keys):
    """
    Valida que un diccionario de configuración tenga las claves requeridas
    
    Args:
        config_dict (dict): Diccionario de configuración
        required_keys (list): Lista de claves requeridas
    
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_error)
    """
    if not isinstance(config_dict, dict):
        return False, "La configuración debe ser un diccionario"
    
    missing_keys = [key for key in required_keys if key not in config_dict]
    
    if missing_keys:
        return False, f"Faltan claves requeridas: {', '.join(missing_keys)}"
    
    return True, ""


def sanitize_input(user_input, max_length=1000):
    """
    Sanitiza entrada de usuario
    
    Args:
        user_input (str): Entrada del usuario
        max_length (int): Longitud máxima permitida
    
    Returns:
        str: Entrada sanitizada
    """
    if not user_input:
        return ""
    
    # Convertir a string si no lo es
    user_input = str(user_input)
    
    # Truncar si es muy largo
    if len(user_input) > max_length:
        user_input = user_input[:max_length]
    
    # Remover caracteres de control peligrosos
    user_input = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', user_input)
    
    # Strip espacios
    user_input = user_input.strip()
    
    return user_input