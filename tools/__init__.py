"""
tools/__init__.py
Módulo de herramientas para PatCode
"""

from .file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from .shell_tools import ExecuteCommandTool, SearchFilesTool


__all__ = [
    "ReadFileTool",
    "WriteFileTool", 
    "ListDirectoryTool",
    "ExecuteCommandTool",
    "SearchFilesTool",
    "list_tools",
    "get_tools_by_category",
    "get_all_tools"
]


def get_all_tools():
    """
    Retorna todas las herramientas disponibles
    
    Returns:
        Dict con todas las instancias de herramientas
    """
    return {
        "read_file": ReadFileTool,
        "write_file": WriteFileTool,
        "list_directory": ListDirectoryTool,
        "execute_command": ExecuteCommandTool,
        "search_files": SearchFilesTool
    }


def list_tools():
    """
    Lista todas las herramientas disponibles con sus descripciones
    
    Returns:
        List[Dict]: Lista de herramientas con nombre y descripción
    """
    tools = get_all_tools()
    
    result = []
    for name, tool_class in tools.items():
        # Crear instancia temporal para obtener descripción
        try:
            instance = tool_class()
            description = getattr(instance, 'description', 'Sin descripción')
        except:
            description = 'Sin descripción'
        
        result.append({
            "name": name,
            "description": description,
            "class": tool_class.__name__
        })
    
    return result


def get_tools_by_category():
    """
    Agrupa las herramientas por categoría
    
    Returns:
        Dict[str, List[str]]: Herramientas agrupadas por categoría
    """
    return {
        "archivos": [
            "read_file - Lee el contenido de un archivo",
            "write_file - Escribe contenido en un archivo",
            "list_directory - Lista archivos y directorios"
        ],
        "sistema": [
            "execute_command - Ejecuta comandos en la terminal",
            "search_files - Busca archivos por nombre o patrón"
        ],
        # Agregar más categorías según implementes más herramientas
        # "git": [...],
        # "analisis": [...],
    }


def get_tool_by_name(name: str):
    """
    Obtiene una clase de herramienta por nombre
    
    Args:
        name: Nombre de la herramienta
        
    Returns:
        Clase de la herramienta o None
    """
    tools = get_all_tools()
    return tools.get(name)