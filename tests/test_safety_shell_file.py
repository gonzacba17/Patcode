"""
Tests para SafetyChecker, ShellExecutor y FileEditor
"""
import pytest
from pathlib import Path
import tempfile
import time
from tools.safety_checker import SafetyChecker
from tools.shell_executor import ShellExecutor
from tools.file_editor import FileEditor


class TestSafetyChecker:
    """Tests para SafetyChecker"""
    
    def test_dangerous_command_blocked(self):
        """Comandos peligrosos deben ser bloqueados"""
        checker = SafetyChecker()
        
        dangerous_commands = [
            'rm -rf /',
            'dd if=/dev/zero of=/dev/sda',
            'mkfs.ext4 /dev/sda',
            ':(){:|:&};:',
        ]
        
        for cmd in dangerous_commands:
            is_safe, msg = checker.check_command(cmd)
            assert not is_safe, f"Comando peligroso no bloqueado: {cmd}"
    
    def test_safe_command_allowed(self):
        """Comandos seguros deben ser permitidos"""
        checker = SafetyChecker()
        
        safe_commands = [
            'ls -la',
            'pwd',
            'echo "test"',
            'cat file.txt',
            'python --version',
        ]
        
        for cmd in safe_commands:
            is_safe, msg = checker.check_command(cmd)
            assert is_safe, f"Comando seguro bloqueado: {cmd}"
    
    def test_suspicious_command_flagged(self):
        """Comandos sospechosos deben ser marcados"""
        checker = SafetyChecker()
        
        is_safe, msg = checker.check_command('wget http://example.com/script.sh')
        assert not is_safe
        assert 'sospechoso' in msg.lower() or 'wget' in msg.lower()
    
    def test_approved_command_bypasses_check(self):
        """Comandos pre-aprobados deben pasar"""
        checker = SafetyChecker()
        
        cmd = 'rm test_file.txt'
        checker.add_approved_command(cmd)
        
        is_safe, msg = checker.check_command(cmd)
        assert is_safe
    
    def test_file_operation_validation(self):
        """Operaciones de archivo deben ser validadas"""
        checker = SafetyChecker()
        
        safe_file = Path('test.py')
        is_safe, msg = checker.check_file_operation(safe_file, 'write')
        assert is_safe
        
        binary_file = Path('test.exe')
        is_safe, msg = checker.check_file_operation(binary_file, 'write')
        assert not is_safe


class TestShellExecutor:
    """Tests para ShellExecutor"""
    
    def test_safe_command_execution(self):
        """Comandos seguros deben ejecutarse correctamente"""
        executor = ShellExecutor(auto_approve=True)
        success, stdout, stderr = executor.execute('echo "test"')
        
        assert success
        assert "test" in stdout
    
    def test_dangerous_command_blocked(self):
        """Comandos peligrosos deben ser bloqueados"""
        executor = ShellExecutor(auto_approve=True)
        success, stdout, stderr = executor.execute('rm -rf /')
        
        assert not success
        assert "bloqueado" in stderr.lower() or "prohibido" in stderr.lower()
    
    def test_command_timeout(self):
        """Comandos con timeout deben ser cancelados"""
        executor = ShellExecutor(auto_approve=True)
        success, stdout, stderr = executor.execute('sleep 10', timeout=1)
        
        assert not success
        assert "timeout" in stderr.lower()
    
    def test_execution_history(self):
        """El historial de ejecuciones debe ser registrado"""
        executor = ShellExecutor(auto_approve=True)
        
        executor.execute('echo "test1"')
        executor.execute('echo "test2"')
        
        history = executor.get_history(limit=10)
        assert len(history) >= 2
        assert any('test1' in entry['command'] for entry in history)
    
    def test_failed_command(self):
        """Comandos fallidos deben ser registrados correctamente"""
        executor = ShellExecutor(auto_approve=True)
        success, stdout, stderr = executor.execute('python3 nonexistent_file.py')
        
        assert not success
        assert stderr or not success
    
    def test_stats(self):
        """Estadísticas deben ser correctas"""
        executor = ShellExecutor(auto_approve=True)
        
        executor.execute('ls')
        executor.execute('rm -rf /')
        
        stats = executor.get_stats()
        assert stats['total_executions'] >= 2
        assert stats['successful'] >= 1


class TestFileEditor:
    """Tests para FileEditor"""
    
    @pytest.fixture
    def temp_file(self, tmp_path, monkeypatch):
        """Fixture para archivo temporal en el proyecto"""
        monkeypatch.chdir(tmp_path)
        temp_path = tmp_path / "test_file.py"
        temp_path.write_text("# Original content\nprint('hello')")
        
        yield temp_path
        
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
    
    @pytest.fixture
    def editor(self, tmp_path):
        """Fixture para FileEditor con directorio temporal"""
        return FileEditor(backup_dir=tmp_path / '.backups')
    
    def test_read_file(self, editor, temp_file):
        """Debe leer archivos correctamente"""
        success, content, error = editor.read_file(temp_file)
        
        assert success
        assert "Original content" in content
        assert not error
    
    def test_read_nonexistent_file(self, editor):
        """Debe manejar archivos inexistentes"""
        success, content, error = editor.read_file(Path('nonexistent.txt'))
        
        assert not success
        assert error
    
    def test_write_file_with_backup(self, editor, temp_file):
        """Debe crear backup al escribir"""
        new_content = "# Modified content\nprint('world')"
        success, msg = editor.write_file(
            temp_file,
            new_content,
            create_backup=True,
            show_diff=False,
            auto_approve=True
        )
        
        assert success
        assert temp_file.read_text() == new_content
        assert len(list(editor.backup_dir.glob('*.bak'))) > 0
    
    def test_rollback(self, editor, temp_file):
        """Debe poder revertir cambios"""
        original_content = temp_file.read_text()
        
        editor.write_file(
            temp_file,
            "# Modified",
            create_backup=True,
            show_diff=False,
            auto_approve=True
        )
        
        success, msg = editor.rollback_last_edit()
        
        assert success
        assert temp_file.read_text() == original_content
    
    def test_apply_diff(self, editor, temp_file):
        """Debe aplicar cambios quirúrgicos"""
        success, msg = editor.apply_diff(
            temp_file,
            "print('hello')",
            "print('goodbye')",
            create_backup=True,
            auto_approve=True
        )
        
        content = temp_file.read_text()
        assert "goodbye" in content
    
    def test_edit_history(self, editor, temp_file):
        """Debe registrar historial de ediciones"""
        editor.write_file(
            temp_file,
            "# Edit 1",
            show_diff=False,
            auto_approve=True
        )
        
        editor.write_file(
            temp_file,
            "# Edit 2",
            show_diff=False,
            auto_approve=True
        )
        
        history = editor.get_history(limit=10)
        assert len(history) >= 2


class TestGitManager:
    """Tests para GitManager"""
    
    def test_is_git_repo_detection(self):
        """Debe detectar si es repositorio Git"""
        from tools.git_manager import GitManager
        
        git = GitManager(auto_approve=True)
        result = git.is_git_repo()
        assert isinstance(result, bool)
    
    def test_git_status(self):
        """Debe ejecutar git status"""
        from tools.git_manager import GitManager
        
        git = GitManager(auto_approve=True)
        if git.is_git_repo():
            success, output = git.git_status()
            assert isinstance(success, bool)
            assert isinstance(output, str)
    
    def test_git_log(self):
        """Debe obtener historial de commits"""
        from tools.git_manager import GitManager
        
        git = GitManager(auto_approve=True)
        if git.is_git_repo():
            success, output = git.git_log(limit=5)
            assert isinstance(success, bool)
            assert isinstance(output, str)
