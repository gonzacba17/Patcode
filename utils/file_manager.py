"""
FileManager - Sistema de gestión de archivos para PatCode.

Este módulo permite cargar, analizar y gestionar archivos del proyecto
para incluirlos en el contexto de conversación con el LLM.
"""

import os
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging
from dataclasses import dataclass, field

# Solo importar excepciones, NO config (evita circular import)
from exceptions import PatCodeError

logger = logging.getLogger(__name__)


@dataclass
class LoadedFile:
    """Representa un archivo cargado en el contexto."""
    
    path: Path
    content: str
    size: int
    encoding: str = "utf-8"
    loaded_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def __str__(self) -> str:
        return f"{self.path.name} ({self.size} bytes)"
    
    def get_summary(self) -> str:
        """Retorna un resumen del archivo."""
        lines = len(self.content.splitlines())
        return f"📄 {self.path.name} | {lines} líneas | {self.size} bytes"


class FileManager:
    """
    Gestor de archivos para el contexto de PatCode.
    
    Permite cargar archivos individuales o analizar proyectos completos,
    manteniendo el contenido en memoria para incluirlo en el contexto del LLM.
    """
    
    # Extensiones permitidas por defecto
    ALLOWED_EXTENSIONS: Set[str] = {
        # Código
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
        # Web
        '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        # Config
        '.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.example',
        # Docs
        '.md', '.txt', '.rst', '.adoc',
        # Shell
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        # Data
        '.sql', '.csv', '.xml',
    }
    
    # Carpetas a ignorar
    IGNORED_FOLDERS: Set[str] = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules', 'venv', 'env',
        '.venv', '.env', 'dist', 'build', '.idea', '.vscode', '.vs',
        'target', 'bin', 'obj', '.pytest_cache', '.mypy_cache', 'coverage',
        '.next', '.nuxt', 'out', 'logs'
    }
    
    # Tamaño máximo por archivo (1MB)
    MAX_FILE_SIZE: int = 1 * 1024 * 1024
    
    def __init__(self, max_total_size: int = 5 * 1024 * 1024):
        """
        Inicializa el FileManager.
        
        Args:
            max_total_size: Tamaño total máximo de archivos cargados (default: 5MB)
        """
        self.loaded_files: Dict[str, LoadedFile] = {}
        self.max_total_size = max_total_size
        logger.info("FileManager inicializado")
    
    def load_file(self, file_path: str) -> LoadedFile:
        """
        Carga un archivo individual al contexto.
        
        Args:
            file_path: Ruta del archivo a cargar
            
        Returns:
            LoadedFile con el contenido cargado
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            PermissionError: Si no hay permisos para leer
            PatCodeError: Si el archivo es muy grande o tipo no permitido
        """
        path = Path(file_path).resolve()
        
        # Validaciones
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        
        if not path.is_file():
            raise PatCodeError(f"La ruta no es un archivo: {path}")
        
        if path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise PatCodeError(
                f"Extensión no permitida: {path.suffix}\n"
                f"Extensiones válidas: {', '.join(sorted(list(self.ALLOWED_EXTENSIONS)[:10]))}..."
            )
        
        # Verificar tamaño
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise PatCodeError(
                f"Archivo muy grande: {file_size / 1024:.1f}KB "
                f"(máximo: {self.MAX_FILE_SIZE / 1024:.1f}KB)"
            )
        
        # Verificar espacio disponible
        current_size = sum(f.size for f in self.loaded_files.values())
        if current_size + file_size > self.max_total_size:
            raise PatCodeError(
                f"No hay espacio suficiente. "
                f"Usa /unload para liberar espacio o /clear_files para limpiar todo."
            )
        
        # Leer archivo
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Intentar con otras codificaciones
            try:
                content = path.read_text(encoding='latin-1')
            except Exception as e:
                raise PatCodeError(f"No se pudo leer el archivo: {e}")
        
        # Crear LoadedFile
        loaded_file = LoadedFile(
            path=path,
            content=content,
            size=file_size,
            encoding='utf-8'
        )
        
        # Guardar
        file_key = str(path)
        self.loaded_files[file_key] = loaded_file
        
        logger.info(f"Archivo cargado: {path} ({file_size} bytes)")
        return loaded_file
    
    def unload_file(self, file_path: str) -> bool:
        """
        Descarga un archivo del contexto.
        
        Args:
            file_path: Ruta del archivo a descargar
            
        Returns:
            True si se descargó, False si no estaba cargado
        """
        path = str(Path(file_path).resolve())
        if path in self.loaded_files:
            del self.loaded_files[path]
            logger.info(f"Archivo descargado: {file_path}")
            return True
        return False
    
    def clear_all(self) -> int:
        """
        Limpia todos los archivos cargados.
        
        Returns:
            Cantidad de archivos eliminados
        """
        count = len(self.loaded_files)
        self.loaded_files.clear()
        logger.info(f"Limpiados {count} archivos del contexto")
        return count
    
    def analyze_project(
        self, 
        project_path: str = ".",
        max_files: int = 50
    ) -> List[Path]:
        """
        Analiza la estructura de un proyecto y retorna archivos relevantes.
        
        Args:
            project_path: Ruta del proyecto (default: directorio actual)
            max_files: Máximo de archivos a retornar
            
        Returns:
            Lista de rutas de archivos encontrados
        """
        project_dir = Path(project_path).resolve()
        
        if not project_dir.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {project_dir}")
        
        if not project_dir.is_dir():
            raise PatCodeError(f"La ruta no es un directorio: {project_dir}")
        
        found_files: List[Path] = []
        
        logger.info(f"Analizando proyecto en: {project_dir}")
        
        # Recorrer directorio
        for root, dirs, files in os.walk(project_dir):
            # Filtrar carpetas ignoradas
            dirs[:] = [d for d in dirs if d not in self.IGNORED_FOLDERS]
            
            # Procesar archivos
            for file in files:
                file_path = Path(root) / file
                
                # Verificar extensión
                if file_path.suffix.lower() in self.ALLOWED_EXTENSIONS:
                    # Verificar tamaño
                    try:
                        if file_path.stat().st_size <= self.MAX_FILE_SIZE:
                            found_files.append(file_path)
                            
                            if len(found_files) >= max_files:
                                logger.warning(
                                    f"Límite de {max_files} archivos alcanzado"
                                )
                                return found_files
                    except Exception as e:
                        logger.warning(f"Error al procesar {file_path}: {e}")
                        continue
        
        logger.info(f"Análisis completo: {len(found_files)} archivos encontrados")
        return found_files
    
    def load_project_files(
        self,
        project_path: str = ".",
        priority_files: Optional[List[str]] = None,
        max_files: int = 20
    ) -> List[LoadedFile]:
        """
        Carga archivos importantes del proyecto automáticamente.
        
        Args:
            project_path: Ruta del proyecto
            priority_files: Lista de nombres de archivos prioritarios
            max_files: Máximo de archivos a cargar
            
        Returns:
            Lista de archivos cargados
        """
        if priority_files is None:
            priority_files = [
                'README.md', 'README.txt', 'README',
                'requirements.txt', 'package.json', 'pyproject.toml',
                'main.py', 'app.py', 'index.js', 'index.ts',
                '.env.example', 'config.py', 'settings.py'
            ]
        
        project_dir = Path(project_path).resolve()
        loaded: List[LoadedFile] = []
        
        # 1. Cargar archivos prioritarios primero
        for priority_file in priority_files:
            file_path = project_dir / priority_file
            if file_path.exists():
                try:
                    loaded_file = self.load_file(str(file_path))
                    loaded.append(loaded_file)
                    logger.info(f"Archivo prioritario cargado: {priority_file}")
                except Exception as e:
                    logger.warning(f"No se pudo cargar {priority_file}: {e}")
        
        # 2. Si hay espacio, cargar más archivos del análisis
        if len(loaded) < max_files:
            remaining = max_files - len(loaded)
            all_files = self.analyze_project(project_path, max_files=remaining * 2)
            
            # Filtrar los ya cargados
            already_loaded = {str(f.path) for f in loaded}
            new_files = [f for f in all_files if str(f) not in already_loaded]
            
            # Cargar hasta el límite
            for file_path in new_files[:remaining]:
                try:
                    loaded_file = self.load_file(str(file_path))
                    loaded.append(loaded_file)
                except Exception as e:
                    logger.warning(f"No se pudo cargar {file_path}: {e}")
        
        logger.info(f"Proyecto cargado: {len(loaded)} archivos en contexto")
        return loaded
    
    def get_context_summary(self) -> str:
        """
        Genera un resumen del contexto actual para el LLM.
        
        Returns:
            String con el resumen formateado
        """
        if not self.loaded_files:
            return ""
        
        total_size = sum(f.size for f in self.loaded_files.values())
        total_lines = sum(
            len(f.content.splitlines()) 
            for f in self.loaded_files.values()
        )
        
        summary = (
            f"\n--- ARCHIVOS EN CONTEXTO ---\n"
            f"Total: {len(self.loaded_files)} archivos | "
            f"{total_lines} líneas | "
            f"{total_size / 1024:.1f}KB\n\n"
        )
        
        for file_path, loaded_file in self.loaded_files.items():
            summary += f"{loaded_file.get_summary()}\n"
        
        summary += "--- FIN ARCHIVOS ---\n"
        return summary
    
    def get_files_content(self) -> str:
        """
        Retorna el contenido completo de todos los archivos cargados.
        
        Returns:
            String con todo el contenido formateado
        """
        if not self.loaded_files:
            return ""
        
        content = "\n--- CONTENIDO DE ARCHIVOS ---\n"
        
        for file_path, loaded_file in self.loaded_files.items():
            content += f"\n=== {loaded_file.path} ===\n"
            content += f"```{loaded_file.path.suffix[1:] if loaded_file.path.suffix else ''}\n"
            content += loaded_file.content
            content += "\n```\n"
        
        content += "\n--- FIN CONTENIDO ---\n"
        return content
    
    def get_stats(self) -> Dict[str, any]:
        """
        Retorna estadísticas sobre los archivos cargados.
        
        Returns:
            Diccionario con estadísticas
        """
        total_size = sum(f.size for f in self.loaded_files.values())
        
        return {
            'total_files': len(self.loaded_files),
            'total_size_bytes': total_size,
            'total_size_kb': round(total_size / 1024, 2),
            'max_size_mb': round(self.max_total_size / (1024 * 1024), 2),
            'usage_percent': round((total_size / self.max_total_size) * 100, 2) if self.max_total_size > 0 else 0,
            'files': [str(f.path) for f in self.loaded_files.values()]
        }
    
    def list_files(self) -> List[str]:
        """
        Retorna lista de archivos cargados.
        
        Returns:
            Lista de rutas de archivos
        """
        return [str(f.path) for f in self.loaded_files.values()]