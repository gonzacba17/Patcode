# ============================================================================
# tools/file_operations.py - VERSIÓN CORREGIDA
# ============================================================================

import os
from pathlib import Path
from typing import Optional, List, Tuple
import shutil


class FileOperations:
    """
    Herramientas para manipular archivos del sistema.
    Proporciona operaciones seguras de lectura, escritura y edición.
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa el sistema de operaciones de archivos.
        
        Args:
            base_path: Directorio base para operaciones relativas
        """
        self.base_path = Path(base_path).resolve()
        self._create_backup_dir()
    
    def _create_backup_dir(self):
        """Crea directorio para backups automáticos"""
        backup_dir = self.base_path / ".patcode" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, path: str) -> Path:
        """Convierte ruta relativa a absoluta dentro del proyecto"""
        full_path = (self.base_path / path).resolve()
        
        # Verificar que esté dentro del proyecto (seguridad)
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"Ruta fuera del proyecto: {path}")
        
        return full_path
    
    def _backup_file(self, path: Path):
        """Crea backup de un archivo antes de modificarlo"""
        if not path.exists():
            return
        
        backup_dir = self.base_path / ".patcode" / "backups"
        backup_name = f"{path.name}.backup"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(path, backup_path)
    
    def read_file(self, path: str) -> str:
        """
        Lee el contenido completo de un archivo.
        
        Args:
            path: Ruta relativa del archivo
            
        Returns:
            Contenido del archivo como string
            
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        full_path = self._get_full_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, path: str, content: str, backup: bool = True) -> bool:
        """
        Escribe contenido en un archivo (sobrescribe si existe).
        
        Args:
            path: Ruta relativa del archivo
            content: Contenido a escribir
            backup: Si True, crea backup antes de sobrescribir
            
        Returns:
            True si la operación fue exitosa
        """
        full_path = self._get_full_path(path)
        
        # Backup si el archivo existe
        if backup and full_path.exists():
            self._backup_file(full_path)
        
        # Crear directorio padre si no existe
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def edit_file(self, path: str, old_content: str, new_content: str) -> Tuple[bool, str]:
        """
        Edita una porción específica de un archivo.
        
        Args:
            path: Ruta relativa del archivo
            old_content: Contenido a reemplazar
            new_content: Nuevo contenido
            
        Returns:
            Tuple (success, message)
        """
        try:
            content = self.read_file(path)
            
            if old_content not in content:
                return False, f"No se encontró el contenido a reemplazar en {path}"
            
            # Contar ocurrencias
            occurrences = content.count(old_content)
            if occurrences > 1:
                return False, f"Contenido ambiguo: encontrado {occurrences} veces en {path}"
            
            # Reemplazar
            new_file_content = content.replace(old_content, new_content, 1)
            
            # Escribir con backup
            self.write_file(path, new_file_content, backup=True)
            
            return True, f"Archivo {path} editado exitosamente"
            
        except Exception as e:
            return False, f"Error al editar {path}: {str(e)}"
    
    def create_file(self, path: str, content: str = "") -> Tuple[bool, str]:
        """
        Crea un nuevo archivo.
        
        Args:
            path: Ruta relativa del archivo
            content: Contenido inicial (opcional)
            
        Returns:
            Tuple (success, message)
        """
        full_path = self._get_full_path(path)
        
        if full_path.exists():
            return False, f"El archivo {path} ya existe"
        
        self.write_file(path, content, backup=False)
        return True, f"Archivo {path} creado exitosamente"
    
    def delete_file(self, path: str, backup: bool = True) -> Tuple[bool, str]:
        """
        Elimina un archivo.
        
        Args:
            path: Ruta relativa del archivo
            backup: Si True, crea backup antes de eliminar
            
        Returns:
            Tuple (success, message)
        """
        try:
            full_path = self._get_full_path(path)
            
            if not full_path.exists():
                return False, f"Archivo no encontrado: {path}"
            
            if backup:
                self._backup_file(full_path)
            
            os.remove(full_path)
            return True, f"Archivo {path} eliminado exitosamente"
            
        except Exception as e:
            return False, f"Error al eliminar {path}: {str(e)}"
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> List[str]:
        """
        Lista archivos en un directorio.
        
        Args:
            directory: Directorio a listar
            pattern: Patrón de archivos (ej: "*.py")
            
        Returns:
            Lista de rutas relativas
        """
        full_path = self._get_full_path(directory)
        
        if not full_path.is_dir():
            return []
        
        files = []
        for file_path in full_path.rglob(pattern):
            if file_path.is_file():
                relative = file_path.relative_to(self.base_path)
                files.append(str(relative))
        
        return sorted(files)
    
    def get_file_info(self, path: str) -> dict:
        """
        Obtiene información de un archivo.
        
        Args:
            path: Ruta relativa del archivo
            
        Returns:
            Dict con información del archivo
        """
        full_path = self._get_full_path(path)
        
        if not full_path.exists():
            return {"exists": False}
        
        stat = full_path.stat()
        
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": full_path.is_file(),
            "is_dir": full_path.is_dir(),
            "extension": full_path.suffix
        }