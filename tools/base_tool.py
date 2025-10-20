"""
tools/base_tool.py
Clase base abstracta para todas las herramientas de PatCode
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """
    Resultado estándar para todas las herramientas.
    
    Attributes:
        success: Si la operación fue exitosa
        data: Datos retornados por la herramienta
        error: Mensaje de error si falló
        metadata: Información adicional (timestamps, stats, etc.)
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """Clase base para todas las herramientas"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "Sin descripción"
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la herramienta con los parámetros dados
        
        Returns:
            Dict con 'success', 'result' o 'error'
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Retorna el schema JSON de parámetros que acepta la herramienta
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Valida los parámetros contra el schema con validación robusta
        
        Returns:
            (is_valid, error_message)
        """
        schema = self.get_schema()
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for param in required:
            if param not in params:
                return False, f"Parámetro requerido faltante: {param}"
        
        for param_name, param_value in params.items():
            if param_name not in properties:
                logger.warning(f"Parámetro desconocido ignorado: {param_name}")
                continue
            
            param_schema = properties[param_name]
            expected_type = param_schema.get("type")
            
            if expected_type == "string":
                if not isinstance(param_value, str):
                    return False, f"Parámetro '{param_name}' debe ser string, recibido {type(param_value).__name__}"
                
                if "file_path" in param_name.lower() or "path" in param_name.lower():
                    if not self._validate_path(param_value):
                        return False, f"Path inválido o inseguro: {param_value}"
                
                max_length = param_schema.get("maxLength")
                if max_length and len(param_value) > max_length:
                    return False, f"Parámetro '{param_name}' excede longitud máxima de {max_length}"
            
            elif expected_type == "integer":
                if not isinstance(param_value, int):
                    return False, f"Parámetro '{param_name}' debe ser integer, recibido {type(param_value).__name__}"
                
                minimum = param_schema.get("minimum")
                maximum = param_schema.get("maximum")
                if minimum is not None and param_value < minimum:
                    return False, f"Parámetro '{param_name}' debe ser >= {minimum}"
                if maximum is not None and param_value > maximum:
                    return False, f"Parámetro '{param_name}' debe ser <= {maximum}"
            
            elif expected_type == "boolean":
                if not isinstance(param_value, bool):
                    return False, f"Parámetro '{param_name}' debe ser boolean, recibido {type(param_value).__name__}"
            
            elif expected_type == "array":
                if not isinstance(param_value, list):
                    return False, f"Parámetro '{param_name}' debe ser array, recibido {type(param_value).__name__}"
        
        return True, None
    
    def _validate_path(self, path_str: str) -> bool:
        """
        Valida que un path sea seguro (no path traversal)
        
        Args:
            path_str: Path a validar
        
        Returns:
            True si es seguro, False si es peligroso
        """
        try:
            path = Path(path_str).resolve()
            
            if ".." in str(path):
                logger.warning(f"Path traversal detectado: {path_str}")
                return False
            
            dangerous_paths = ["/etc", "/sys", "/proc", "/dev", "C:\\Windows", "C:\\System32"]
            for dangerous in dangerous_paths:
                if str(path).startswith(dangerous):
                    logger.warning(f"Intento de acceso a path crítico: {path_str}")
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validando path {path_str}: {e}")
            return False
    
    def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la herramienta con validación de parámetros
        """
        is_valid, error = self.validate_params(kwargs)
        
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "tool": self.name
            }
        
        try:
            result = self.execute(**kwargs)
            result["tool"] = self.name
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": self.name
            }
    
    def to_llm_format(self) -> Dict[str, Any]:
        """
        Convierte la herramienta a formato compatible con LLM
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_schema()
        }
    
    def __repr__(self):
        return f"<Tool: {self.name}>"