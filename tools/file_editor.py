"""
Editor de archivos con diffs, backups y rollback.
"""
import difflib
import shutil
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime
from tools.safety_checker import SafetyChecker
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FileEditor:
    """
    Editor de archivos con preview de cambios, backups automáticos
    y capacidad de rollback.
    """
    
    def __init__(self, backup_dir: Path = Path('.patcode_backups')):
        """
        Inicializa el editor de archivos.
        
        Args:
            backup_dir: Directorio para almacenar backups
        """
        self.safety_checker = SafetyChecker()
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.edit_history: List[Dict] = []
        logger.info(f"FileEditor inicializado (backup_dir={backup_dir})")
    
    def read_file(self, filepath: Path) -> Tuple[bool, str, str]:
        """
        Lee el contenido de un archivo.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            Tupla (success, content, error_message)
        """
        try:
            filepath = Path(filepath).resolve()
            
            is_safe, safety_msg = self.safety_checker.check_file_operation(
                filepath, 'read'
            )
            
            if not is_safe:
                logger.warning(f"Lectura bloqueada: {filepath} - {safety_msg}")
                return False, "", f"⚠️  {safety_msg}"
            
            if not filepath.exists():
                logger.warning(f"Archivo no existe: {filepath}")
                return False, "", f"❌ El archivo no existe: {filepath}"
            
            if not filepath.is_file():
                logger.warning(f"No es un archivo: {filepath}")
                return False, "", f"❌ No es un archivo: {filepath}"
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Archivo leído: {filepath} ({len(content)} bytes)")
            return True, content, ""
        
        except UnicodeDecodeError:
            logger.error(f"Error de encoding: {filepath}")
            return False, "", "❌ El archivo no es texto válido (posiblemente binario)"
        
        except Exception as e:
            logger.exception(f"Error leyendo archivo: {filepath}")
            return False, "", f"❌ Error al leer archivo: {str(e)}"
    
    def write_file(
        self,
        filepath: Path,
        content: str,
        create_backup: bool = True,
        show_diff: bool = True,
        auto_approve: bool = False
    ) -> Tuple[bool, str]:
        """
        Escribe contenido a un archivo con backup y diff.
        
        Args:
            filepath: Ruta del archivo
            content: Contenido a escribir
            create_backup: Si crear backup antes de escribir
            show_diff: Si mostrar diff antes de aplicar
            auto_approve: Si auto-aprobar sin confirmación
        
        Returns:
            Tupla (success, message)
        """
        try:
            filepath = Path(filepath).resolve()
            
            is_safe, safety_msg = self.safety_checker.check_file_operation(
                filepath, 'write'
            )
            
            if not is_safe:
                logger.warning(f"Escritura bloqueada: {filepath} - {safety_msg}")
                return False, f"⚠️  {safety_msg}"
            
            old_content = ""
            file_exists = filepath.exists()
            
            if file_exists:
                success, old_content, error = self.read_file(filepath)
                if not success:
                    return False, error
                
                if show_diff:
                    diff = self._generate_diff(old_content, content, str(filepath.name))
                    if diff.strip():
                        print("\n📝 Cambios propuestos:")
                        print(diff)
                    else:
                        print("\n📝 Sin cambios (contenido idéntico)")
                        return True, "Sin cambios necesarios"
                
                if not auto_approve:
                    response = input("\n¿Aplicar estos cambios? (s/N): ").strip().lower()
                    if response not in ['s', 'si', 'sí', 'y', 'yes']:
                        logger.info(f"Escritura cancelada por usuario: {filepath}")
                        return False, "Cambios cancelados por el usuario"
                
                if create_backup:
                    backup_path = self._create_backup(filepath, old_content)
                    logger.info(f"Backup creado: {backup_path}")
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_edit(filepath, old_content, content, file_exists)
            
            logger.info(f"Archivo escrito: {filepath} ({len(content)} bytes)")
            return True, f"✅ Archivo {'actualizado' if file_exists else 'creado'}: {filepath}"
        
        except Exception as e:
            logger.exception(f"Error escribiendo archivo: {filepath}")
            return False, f"❌ Error al escribir archivo: {str(e)}"
    
    def apply_diff(
        self,
        filepath: Path,
        old_str: str,
        new_str: str,
        create_backup: bool = True,
        auto_approve: bool = False
    ) -> Tuple[bool, str]:
        """
        Aplica un cambio quirúrgico reemplazando old_str por new_str.
        
        Args:
            filepath: Ruta del archivo
            old_str: Texto a buscar
            new_str: Texto de reemplazo
            create_backup: Si crear backup
        
        Returns:
            Tupla (success, message)
        """
        try:
            success, content, error = self.read_file(filepath)
            if not success:
                return False, error
            
            if old_str not in content:
                logger.warning(f"Texto no encontrado en {filepath}")
                return False, f"❌ Texto no encontrado en el archivo"
            
            occurrences = content.count(old_str)
            if occurrences > 1:
                logger.warning(f"Múltiples ocurrencias ({occurrences}) en {filepath}")
                return False, f"❌ Se encontraron {occurrences} ocurrencias. Use write_file para mayor control."
            
            new_content = content.replace(old_str, new_str, 1)
            
            return self.write_file(
                filepath,
                new_content,
                create_backup=create_backup,
                show_diff=True,
                auto_approve=auto_approve
            )
        
        except Exception as e:
            logger.exception(f"Error aplicando diff: {filepath}")
            return False, f"❌ Error al aplicar cambios: {str(e)}"
    
    def rollback_last_edit(self) -> Tuple[bool, str]:
        """
        Revierte el último cambio realizado.
        
        Returns:
            Tupla (success, message)
        """
        if not self.edit_history:
            logger.warning("No hay cambios para revertir")
            return False, "❌ No hay cambios para revertir"
        
        try:
            last_edit = self.edit_history[-1]
            filepath = Path(last_edit['filepath'])
            
            if not filepath.exists():
                logger.error(f"Archivo no existe para rollback: {filepath}")
                return False, f"❌ El archivo ya no existe: {filepath}"
            
            backup_path = last_edit.get('backup_path')
            if backup_path and Path(backup_path).exists():
                shutil.copy2(backup_path, filepath)
                logger.info(f"Rollback desde backup: {filepath}")
                message = f"✅ Archivo revertido desde backup: {filepath}"
            elif 'old_content' in last_edit:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(last_edit['old_content'])
                logger.info(f"Rollback desde historial: {filepath}")
                message = f"✅ Archivo revertido desde historial: {filepath}"
            else:
                return False, "❌ No hay backup disponible para revertir"
            
            self.edit_history.pop()
            return True, message
        
        except Exception as e:
            logger.exception("Error en rollback")
            return False, f"❌ Error al revertir: {str(e)}"
    
    def _create_backup(self, filepath: Path, content: str) -> Path:
        """
        Crea un backup del archivo.
        
        Args:
            filepath: Archivo a respaldar
            content: Contenido del archivo
        
        Returns:
            Ruta del backup creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return backup_path
    
    def _generate_diff(self, old: str, new: str, filename: str) -> str:
        """
        Genera diff unified estilo Git.
        
        Args:
            old: Contenido antiguo
            new: Contenido nuevo
            filename: Nombre del archivo
        
        Returns:
            Diff formateado
        """
        diff_lines = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff_lines)
    
    def _log_edit(
        self,
        filepath: Path,
        old_content: str,
        new_content: str,
        had_backup: bool
    ) -> None:
        """
        Registra una edición en el historial.
        
        Args:
            filepath: Archivo editado
            old_content: Contenido anterior
            new_content: Contenido nuevo
            had_backup: Si se creó backup
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'filepath': str(filepath),
            'old_content': old_content if len(old_content) < 10000 else old_content[:10000],
            'new_content': new_content if len(new_content) < 10000 else new_content[:10000],
            'backup_path': str(self.backup_dir / f"{filepath.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak") if had_backup else None
        }
        
        self.edit_history.append(entry)
        
        if len(self.edit_history) > 50:
            self.edit_history = self.edit_history[-50:]
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene historial de ediciones.
        
        Args:
            limit: Número máximo de entradas
        
        Returns:
            Lista de ediciones
        """
        return list(reversed(self.edit_history[-limit:]))
    
    def clear_backups(self, older_than_days: int = 7) -> int:
        """
        Limpia backups antiguos.
        
        Args:
            older_than_days: Días de antigüedad
        
        Returns:
            Número de archivos eliminados
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=older_than_days)
        deleted = 0
        
        for backup_file in self.backup_dir.glob('*.bak'):
            if backup_file.stat().st_mtime < cutoff.timestamp():
                backup_file.unlink()
                deleted += 1
        
        logger.info(f"Backups antiguos eliminados: {deleted}")
        return deleted
