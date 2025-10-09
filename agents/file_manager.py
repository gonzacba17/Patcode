"""
FileManager - Gestión segura de archivos para PatCode
Fase 1: Lectura, escritura y análisis de archivos
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import mimetypes

class SecurityError(Exception):
    """Error de seguridad en operaciones de archivos"""
    pass

class FileManager:
    """Gestor de archivos con capacidades de seguridad y backup"""
    
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs', '.scala',
        '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.xml', '.csv',
        '.html', '.css', '.scss', '.sass', '.sql', '.sh', '.bash'
    }
    
    BLOCKED_DIRS = {
        'node_modules', '.git', 'venv', 'env', '.venv', '__pycache__',
        '.next', 'dist', 'build', '.cache', '.pytest_cache', '.mypy_cache'
    }
    
    FORBIDDEN_PATHS = {
        '/etc', '/sys', '/proc', '/dev', '/boot', '/root',
        os.path.expanduser('~/.ssh'),
        os.path.expanduser('~/.aws'),
    }
    
    def __init__(
        self,
        working_dir: str = ".",
        backup_enabled: bool = True,
        backup_dir: str = ".patcode_backups",
        max_file_size_mb: int = 5,
        sandbox_mode: bool = True
    ):
        self.working_dir = Path(working_dir).resolve()
        self.backup_enabled = backup_enabled
        self.backup_dir = Path(backup_dir)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.sandbox_mode = sandbox_mode
        
        if self.backup_enabled:
            self.backup_dir.mkdir(exist_ok=True)