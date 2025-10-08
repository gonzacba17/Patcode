"""
tools/__init__.py
Módulo de herramientas para PatCode
"""

from .base_tool import BaseTool

# File operations
from .file_tools import ReadFileTool, WriteFileTool, AppendFileTool

# Directory operations
from .directory_tools import ListDirectoryTool, FindFilesTool, GetTreeTool

# Shell operations
from .shell_tools import RunCommandTool, RunPythonScriptTool, RunTestsTool

# Search operations
from .search_tools import GrepTool, FindDefinitionTool, FindReferencesTool

# Git operations
from .git_tools import (
    GitStatusTool,
    GitDiffTool,
    GitCommitTool,
    GitLogTool,
    GitBranchTool
)

# Code analysis
from .analysis_tools import (
    SyntaxCheckTool,
    CodeMetricsTool,
    FindTODOTool,
    ComplexityAnalysisTool,
    ImportAnalysisTool
)


# Registro de todas las herramientas disponibles
ALL_TOOLS = {
    # File tools
    "read_file": ReadFileTool,
    "write_file": WriteFileTool,
    "append_file": AppendFileTool,
    
    # Directory tools
    "list_directory": ListDirectoryTool,
    "find_files": FindFilesTool,
    "get_tree": GetTreeTool,
    
    # Shell tools
    "run_command": RunCommandTool,
    "run_python": RunPythonScriptTool,
    "run_tests": RunTestsTool,
    
    # Search tools
    "grep": GrepTool,
    "find_definition": FindDefinitionTool,
    "find_references": FindReferencesTool,
    
    # Git tools
    "git_status": GitStatusTool,
    "git_diff": GitDiffTool,
    "git_commit": GitCommitTool,
    "git_log": GitLogTool,
    "git_branch": GitBranchTool,
    
    # Analysis tools
    "syntax_check": SyntaxCheckTool,
    "code_metrics": CodeMetricsTool,
    "find_todos": FindTODOTool,
    "complexity_analysis": ComplexityAnalysisTool,
    "import_analysis": ImportAnalysisTool,
}


def get_tool(tool_name: str, workspace_root: str = "."):
    """
    Obtiene una instancia de una herramienta por su nombre
    
    Args:
        tool_name: Nombre de la herramienta
        workspace_root: Directorio raíz del workspace
    
    Returns:
        Instancia de la herramienta o None si no existe
    """
    tool_class = ALL_TOOLS.get(tool_name)
    if tool_class:
        return tool_class(workspace_root=workspace_root)
    return None


def list_tools():
    """
    Lista todas las herramientas disponibles con sus descripciones
    
    Returns:
        Lista de diccionarios con info de cada herramienta
    """
    tools_info = []
    for name, tool_class in ALL_TOOLS.items():
        instance = tool_class()
        tools_info.append({
            "name": name,
            "class": tool_class.__name__,
            "description": instance.description,
            "schema": instance.get_schema()
        })
    return tools_info


def get_tools_by_category():
    """
    Organiza herramientas por categoría
    
    Returns:
        Diccionario con categorías y sus herramientas
    """
    return {
        "file_operations": [
            "read_file", "write_file", "append_file"
        ],
        "directory_operations": [
            "list_directory", "find_files", "get_tree"
        ],
        "shell_operations": [
            "run_command", "run_python", "run_tests"
        ],
        "search_operations": [
            "grep", "find_definition", "find_references"
        ],
        "git_operations": [
            "git_status", "git_diff", "git_commit", "git_log", "git_branch"
        ],
        "code_analysis": [
            "syntax_check", "code_metrics", "find_todos", 
            "complexity_analysis", "import_analysis"
        ]
    }


__all__ = [
    # Base
    "BaseTool",
    
    # File tools
    "ReadFileTool",
    "WriteFileTool",
    "AppendFileTool",
    
    # Directory tools
    "ListDirectoryTool",
    "FindFilesTool",
    "GetTreeTool",
    
    # Shell tools
    "RunCommandTool",
    "RunPythonScriptTool",
    "RunTestsTool",
    
    # Search tools
    "GrepTool",
    "FindDefinitionTool",
    "FindReferencesTool",
    
    # Git tools
    "GitStatusTool",
    "GitDiffTool",
    "GitCommitTool",
    "GitLogTool",
    "GitBranchTool",
    
    # Analysis tools
    "SyntaxCheckTool",
    "CodeMetricsTool",
    "FindTODOTool",
    "ComplexityAnalysisTool",
    "ImportAnalysisTool",
    
    # Utilities
    "ALL_TOOLS",
    "get_tool",
    "list_tools",
    "get_tools_by_category",
]