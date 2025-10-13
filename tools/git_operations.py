# ============================================================================
# tools/git_operations.py - VERSIÓN COMPLETA
# ============================================================================

import subprocess
from typing import Tuple, List, Optional


class GitOperations:
    """
    Herramientas para operaciones Git.
    Permite gestionar commits, branches y estado del repositorio.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Inicializa operaciones Git.
        
        Args:
            repo_path: Ruta al repositorio
        """
        self.repo_path = repo_path
    
    def _run_git_command(self, command: List[str]) -> Tuple[str, str, int]:
        """Ejecuta un comando git y retorna el resultado"""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1
    
    def status(self) -> str:
        """
        Obtiene el estado actual del repositorio.
        
        Returns:
            Output de git status
        """
        stdout, stderr, _ = self._run_git_command(['status'])
        return stdout if stdout else stderr
    
    def diff(self, staged: bool = False) -> str:
        """
        Obtiene los cambios no commiteados.
        
        Args:
            staged: Si True, muestra cambios en staging
            
        Returns:
            Output de git diff
        """
        command = ['diff', '--cached'] if staged else ['diff']
        stdout, stderr, _ = self._run_git_command(command)
        return stdout if stdout else stderr
    
    def add(self, files: List[str] = None) -> Tuple[bool, str]:
        """
        Agrega archivos al staging area.
        
        Args:
            files: Lista de archivos (None = agregar todos)
            
        Returns:
            Tuple (success, message)
        """
        if files is None:
            command = ['add', '.']
        else:
            command = ['add'] + files
        
        stdout, stderr, code = self._run_git_command(command)
        
        if code == 0:
            return True, "Archivos agregados al staging"
        else:
            return False, stderr
    
    def commit(self, message: str, add_all: bool = True) -> Tuple[bool, str]:
        """
        Crea un commit.
        
        Args:
            message: Mensaje del commit
            add_all: Si True, hace 'git add .' antes
            
        Returns:
            Tuple (success, message)
        """
        # Add all si se solicita
        if add_all:
            success, msg = self.add()
            if not success:
                return False, f"Error al agregar archivos: {msg}"
        
        # Crear commit
        stdout, stderr, code = self._run_git_command(['commit', '-m', message])
        
        if code == 0:
            return True, f"Commit creado: {message}"
        else:
            # Git retorna error si no hay cambios
            if "nothing to commit" in stderr:
                return False, "No hay cambios para commitear"
            return False, stderr
    
    def log(self, max_count: int = 10) -> List[dict]:
        """
        Obtiene el historial de commits.
        
        Args:
            max_count: Número máximo de commits
            
        Returns:
            Lista de dicts con info de commits
        """
        format_str = '%H|%an|%ae|%ad|%s'
        command = ['log', f'--max-count={max_count}', f'--pretty=format:{format_str}']
        
        stdout, _, code = self._run_git_command(command)
        
        if code != 0 or not stdout:
            return []
        
        commits = []
        for line in stdout.strip().split('\n'):
            parts = line.split('|')
            if len(parts) == 5:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'date': parts[3],
                    'message': parts[4]
                })
        
        return commits
    
    def branch_list(self) -> List[str]:
        """
        Lista todas las ramas.
        
        Returns:
            Lista de nombres de ramas
        """
        stdout, _, code = self._run_git_command(['branch'])
        
        if code != 0:
            return []
        
        branches = []
        for line in stdout.strip().split('\n'):
            # Remover el asterisco de la rama actual
            branch = line.strip().replace('* ', '')
            if branch:
                branches.append(branch)
        
        return branches
    
    def current_branch(self) -> str:
        """
        Obtiene la rama actual.
        
        Returns:
            Nombre de la rama actual
        """
        stdout, _, code = self._run_git_command(['branch', '--show-current'])
        
        if code == 0:
            return stdout.strip()
        return ""
    
    def create_branch(self, branch_name: str) -> Tuple[bool, str]:
        """
        Crea una nueva rama.
        
        Args:
            branch_name: Nombre de la nueva rama
            
        Returns:
            Tuple (success, message)
        """
        stdout, stderr, code = self._run_git_command(['branch', branch_name])
        
        if code == 0:
            return True, f"Rama '{branch_name}' creada"
        else:
            return False, stderr
    
    def checkout(self, branch_name: str) -> Tuple[bool, str]:
        """
        Cambia a una rama diferente.
        
        Args:
            branch_name: Nombre de la rama
            
        Returns:
            Tuple (success, message)
        """
        stdout, stderr, code = self._run_git_command(['checkout', branch_name])
        
        if code == 0:
            return True, f"Cambiado a rama '{branch_name}'"
        else:
            return False, stderr
    
    def pull(self, remote: str = "origin", branch: str = None) -> Tuple[bool, str]:
        """
        Pull de cambios desde remoto.
        
        Args:
            remote: Nombre del remoto
            branch: Rama específica (None = rama actual)
            
        Returns:
            Tuple (success, message)
        """
        if branch:
            command = ['pull', remote, branch]
        else:
            command = ['pull', remote]
        
        stdout, stderr, code = self._run_git_command(command)
        
        if code == 0:
            return True, stdout
        else:
            return False, stderr
    
    def push(self, remote: str = "origin", branch: str = None) -> Tuple[bool, str]:
        """
        Push de cambios al remoto.
        
        Args:
            remote: Nombre del remoto
            branch: Rama específica (None = rama actual)
            
        Returns:
            Tuple (success, message)
        """
        if branch:
            command = ['push', remote, branch]
        else:
            command = ['push', remote]
        
        stdout, stderr, code = self._run_git_command(command)
        
        if code == 0:
            return True, stdout
        else:
            return False, stderr