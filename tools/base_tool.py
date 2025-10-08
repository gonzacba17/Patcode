"""
tools/base_tool.py
Clase base abstracta para todas las herramientas de PatCode
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


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
        Valida los parámetros contra el schema
        
        Returns:
            (is_valid, error_message)
        """
        schema = self.get_schema()
        required = schema.get("required", [])
        
        # Verificar parámetros requeridos
        for param in required:
            if param not in params:
                return False, f"Parámetro requerido faltante: {param}"
        
        return True, None
    
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