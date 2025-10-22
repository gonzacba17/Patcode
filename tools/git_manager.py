"""
Integración con Git para operaciones básicas.
"""
from pathlib import Path
from typing import Tuple, List, Optional
from tools.shell_executor import ShellExecutor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GitManager:
    """
    Gestor de operaciones Git usando ShellExecutor.
    """
    
    def __init__(self):
        """
        Inicializa el gestor de Git.
        """
        self.executor = ShellExecutor()
        logger.info("GitManager inicializado")
    
    def is_git_repo(self) -> bool:
        """
        Verifica si el directorio actual es un repositorio Git.
        
        Returns:
            True si es un repo Git
        """
        return Path('.git').exists() and Path('.git').is_dir()
    
    def git_status(self) -> Tuple[bool, str]:
        """
        Obtiene el estado del repositorio.
        
        Returns:
            Tupla (success, output)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        result = self.executor.execute('git status', timeout=10)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, stdout
        else:
            return False, stderr or "Error ejecutando git status"
    
    def git_diff(self, filepath: Optional[str] = None) -> Tuple[bool, str]:
        """
        Muestra diferencias en el repositorio.
        
        Args:
            filepath: Archivo específico (None = todos los cambios)
        
        Returns:
            Tupla (success, diff_output)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        command = f'git diff {filepath}' if filepath else 'git diff'
        result = self.executor.execute(command, timeout=10)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            if not stdout.strip():
                return True, "Sin cambios"
            return True, stdout
        else:
            return False, stderr or "Error ejecutando git diff"
    
    def git_add(self, files: List[str]) -> Tuple[bool, str]:
        """
        Agrega archivos al staging area.
        
        Args:
            files: Lista de archivos a agregar
        
        Returns:
            Tupla (success, message)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        if not files:
            return False, "❌ No se especificaron archivos"
        
        files_str = ' '.join(f'"{f}"' for f in files)
        command = f'git add {files_str}'
        
        result = self.executor.execute(command, timeout=10)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, f"✅ {len(files)} archivo(s) agregado(s) al staging"
        else:
            return False, stderr or "Error ejecutando git add"
    
    def git_commit(
        self,
        message: str,
        auto_add: bool = False
    ) -> Tuple[bool, str]:
        """
        Crea un commit con el mensaje dado.
        
        Args:
            message: Mensaje del commit
            auto_add: Si hacer git add -A antes de commit
        
        Returns:
            Tupla (success, message)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        if not message.strip():
            return False, "❌ El mensaje del commit no puede estar vacío"
        
        if auto_add:
            result = self.executor.execute('git add -A', timeout=10)
            success, stdout, stderr = result.success, result.stdout, result.stderr
            if not success:
                return False, f"Error en git add: {stderr}"
        
        escaped_message = message.replace('"', '\\"').replace('$', '\\$')
        command = f'git commit -m "{escaped_message}"'
        
        result = self.executor.execute(command, timeout=15)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, f"✅ Commit creado: {message[:50]}"
        elif "nothing to commit" in stderr.lower():
            return True, "ℹ️  Sin cambios para commitear"
        else:
            return False, stderr or "Error ejecutando git commit"
    
    def git_log(self, limit: int = 5) -> Tuple[bool, str]:
        """
        Muestra el historial de commits.
        
        Args:
            limit: Número de commits a mostrar
        
        Returns:
            Tupla (success, log_output)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        command = f'git log --oneline -n {limit}'
        result = self.executor.execute(command, timeout=10)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            if not stdout.strip():
                return True, "Sin commits aún"
            return True, stdout
        else:
            return False, stderr or "Error ejecutando git log"
    
    def create_branch(self, branch_name: str) -> Tuple[bool, str]:
        """
        Crea una nueva rama.
        
        Args:
            branch_name: Nombre de la rama
        
        Returns:
            Tupla (success, message)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        if not branch_name.strip():
            return False, "❌ El nombre de la rama no puede estar vacío"
        
        command = f'git branch "{branch_name}"'
        result = self.executor.execute(command, timeout=10)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, f"✅ Rama creada: {branch_name}"
        else:
            return False, stderr or "Error creando rama"
    
    def checkout_branch(self, branch_name: str) -> Tuple[bool, str]:
        """
        Cambia a una rama existente.
        
        Args:
            branch_name: Nombre de la rama
        
        Returns:
            Tupla (success, message)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        command = f'git checkout "{branch_name}"'
        result = self.executor.execute(command, timeout=10)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, f"✅ Cambiado a rama: {branch_name}"
        else:
            return False, stderr or "Error cambiando de rama"
    
    def get_current_branch(self) -> Tuple[bool, str]:
        """
        Obtiene el nombre de la rama actual.
        
        Returns:
            Tupla (success, branch_name)
        """
        if not self.is_git_repo():
            return False, "No es un repositorio Git"
        
        command = 'git branch --show-current'
        result = self.executor.execute(command, timeout=5)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            branch = stdout.strip()
            return True, branch if branch else "HEAD detached"
        else:
            return False, "Error obteniendo rama actual"
    
    def git_pull(self) -> Tuple[bool, str]:
        """
        Actualiza el repositorio desde el remoto.
        
        Returns:
            Tupla (success, message)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        result = self.executor.execute('git pull', timeout=30)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, stdout
        else:
            return False, stderr or "Error ejecutando git pull"
    
    def git_push(self) -> Tuple[bool, str]:
        """
        Envía commits al repositorio remoto.
        
        Returns:
            Tupla (success, message)
        """
        if not self.is_git_repo():
            return False, "❌ No es un repositorio Git"
        
        result = self.executor.execute('git push', timeout=30)
        success, stdout, stderr = result.success, result.stdout, result.stderr
        
        if success:
            return True, stdout
        else:
            return False, stderr or "Error ejecutando git push"
