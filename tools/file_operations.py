# tools/file_operations.py

class FileOperations:
    """Herramientas para manipular archivos"""
    
    @staticmethod
    def read_file(path: str) -> str:
        """Lee el contenido de un archivo"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_file(path: str, content: str) -> bool:
        """Escribe contenido en un archivo"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    @staticmethod
    def edit_file(path: str, old_content: str, new_content: str) -> bool:
        """Edita una porción específica de un archivo"""
        content = FileOperations.read_file(path)
        if old_content not in content:
            return False
        content = content.replace(old_content, new_content, 1)
        return FileOperations.write_file(path, content)
    
    @staticmethod
    def create_file(path: str, content: str = "") -> bool:
        """Crea un nuevo archivo"""
        return FileOperations.write_file(path, content)
    
    @staticmethod
    def delete_file(path: str) -> bool:
        """Elimina un archivo"""
        import os
        os.remove(path)
        return True