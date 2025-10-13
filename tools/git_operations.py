# tools/git_operations.py
import subprocess

class GitOperations:
    """Herramientas para operaciones Git"""
    
    @staticmethod
    def git_status() -> str:
        """Obtiene el estado actual del repositorio"""
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def git_diff() -> str:
        """Obtiene los cambios no commiteados"""
        result = subprocess.run(['git', 'diff'], capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def git_commit(message: str) -> bool:
        """Crea un commit con todos los cambios"""
        subprocess.run(['git', 'add', '.'], check=True)
        result = subprocess.run(['git', 'commit', '-m', message], capture_output=True)
        return result.returncode == 0