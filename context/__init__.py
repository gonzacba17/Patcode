"""
Módulo de gestión de contexto para PatCode.
Maneja la lectura y análisis de archivos y directorios del proyecto.
"""

from .project_analyzer import ProjectAnalyzer
from .code_indexer import CodeIndexer
from .dependency_mapper import DependencyMapper
from .semantic_search import SemanticSearch

__all__ = [
    'ProjectAnalyzer',
    'CodeIndexer', 
    'DependencyMapper',
    'SemanticSearch'
]

__version__ = '1.0.0'