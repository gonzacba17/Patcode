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


@pytest.mark.obsolete
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
        executor = ShellExecutor()
        result = executor.execute('echo "test"')
        
        assert result.success
        assert "test" in result.stdout
    
    def test_dangerous_command_blocked(self):
        """Comandos peligrosos deben ser bloqueados"""
        executor = ShellExecutor()
        
        with pytest.raises(ValueError) as exc_info:
            executor.execute('rm -rf /')
        
        assert "Dangerous command" in str(exc_info.value)
    
    def test_command_timeout(self):
        """Comandos con timeout deben ser cancelados"""
        import subprocess
        from unittest.mock import patch
        
        executor = ShellExecutor()
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('echo', 1)):
            result = executor.execute('echo "test"', timeout=1)
        
        assert result is not None, "Result should not be None"
        assert not result.success, f"Command should fail due to timeout, got success={result.success}"
        assert 'timed out' in result.stderr.lower(), f"Expected 'timed out' in stderr, got: {result.stderr}"
        assert result.exit_code == -1, f"Exit code should be -1 for timeout, got {result.exit_code}"
    
    def test_execution_history(self):
        """El historial de ejecuciones debe ser registrado"""
        executor = ShellExecutor()
        
        executor.execute('echo "test1"')
        executor.execute('echo "test2"')
        
        history = executor.get_command_history()
        assert len(history) >= 2
        assert any('test1' in entry['command'] for entry in history)
    
    def test_failed_command(self):
        """Comandos fallidos deben ser registrados correctamente"""
        executor = ShellExecutor()
        result = executor.execute('python3 nonexistent_file.py')
        
        assert not result.success
        assert result.stderr or not result.success
    
    def test_stats(self):
        """Test execution statistics - cross platform"""
        import platform
        
        executor = ShellExecutor()
        is_windows = platform.system() == "Windows"
        
        print(f"\n=== TEST STATS DEBUG ===")
        print(f"Platform: {platform.system()}")
        print(f"Is Windows: {is_windows}")
        
        if is_windows:
            cmd1 = 'echo test'
            print(f"Command 1 (Windows): {cmd1}")
        else:
            cmd1 = 'echo "test"'
            print(f"Command 1 (Unix): {cmd1}")
        
        result1 = executor.execute(cmd1)
        print(f"Result 1: success={result1.success}, exit_code={result1.exit_code}")
        
        if is_windows:
            cmd2 = 'format C:'
            print(f"Command 2 (Windows - should block): {cmd2}")
        else:
            cmd2 = 'rm -rf /'
            print(f"Command 2 (Unix - should block): {cmd2}")
        
        try:
            result2 = executor.execute(cmd2)
            print(f"Result 2: success={result2.success}")
        except ValueError as e:
            print(f"Result 2: blocked with ValueError: {e}")
        
        stats = executor.get_stats()
        print(f"\n=== STATS ===")
        print(f"Stats dict: {stats}")
        
        assert stats['total_commands'] >= 1, f"Expected at least 1 total command, got {stats['total_commands']}"
        assert stats['successful'] >= 1, f"Expected at least 1 successful command, got {stats['successful']}"


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
        
        git = GitManager()
        result = git.is_git_repo()
        assert isinstance(result, bool)
    
    def test_git_status(self):
        """Debe ejecutar git status"""
        from tools.git_manager import GitManager
        
        git = GitManager()
        if git.is_git_repo():
            success, output = git.git_status()
            assert isinstance(success, bool)
            assert isinstance(output, str)
    
    def test_git_log(self):
        """Debe obtener historial de commits"""
        from tools.git_manager import GitManager
        
        git = GitManager()
        if git.is_git_repo():
            success, output = git.git_log(limit=5)
            assert isinstance(success, bool)
            assert isinstance(output, str)
