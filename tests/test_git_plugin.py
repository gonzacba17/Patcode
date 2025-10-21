"""Tests para GitHelperPlugin"""

import pytest
import subprocess
import shutil
from pathlib import Path
from tools.plugins.git_helper_plugin import GitHelperPlugin
import platform
import os


@pytest.fixture
def safe_git_repo(tmp_path):
    """Git repo con cleanup seguro en Windows"""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Init git
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True, capture_output=True)
    
    yield repo_path
    
    # Cleanup con manejo de permisos Windows
    if platform.system() == "Windows":
        def on_rm_error(func, path, exc_info):
            os.chmod(path, 0o777)
            func(path)
        shutil.rmtree(repo_path, onerror=on_rm_error)
    else:
        shutil.rmtree(repo_path)


@pytest.fixture
def git_repo(tmp_path):
    """Crea repo Git temporal"""
    repo_dir = tmp_path / 'test_repo'
    repo_dir.mkdir()
    
    subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_dir, check=True)
    
    (repo_dir / 'test.txt').write_text('initial content')
    subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_dir, check=True)
    
    yield repo_dir
    
    # Cleanup con manejo de permisos Windows
    if repo_dir.exists():
        if platform.system() == "Windows":
            def on_rm_error(func, path, exc_info):
                os.chmod(path, 0o777)
                func(path)
            shutil.rmtree(repo_dir, onerror=on_rm_error)
        else:
            shutil.rmtree(repo_dir)


@pytest.mark.integration
def test_git_plugin_init():
    """Verifica inicialización del plugin"""
    plugin = GitHelperPlugin()
    
    assert plugin.name == "git_helper"
    assert plugin.version == "1.0.0"
    assert plugin.description
    assert plugin.author


def test_git_plugin_is_git_repo(git_repo):
    """Verifica detección de repo Git"""
    plugin = GitHelperPlugin()
    
    assert plugin._is_git_repo(git_repo) is True
    assert plugin._is_git_repo(Path('/tmp')) is False


def test_git_plugin_status_clean(git_repo):
    """Verifica status en repo limpio"""
    plugin = GitHelperPlugin()
    
    context = {
        'current_dir': git_repo,
        'args': {'action': 'status'}
    }
    
    result = plugin._handle_status(context)
    
    assert result['success'] is True
    assert 'clean' in result['result'].lower()


def test_git_plugin_status_modified(git_repo):
    """Verifica status con archivos modificados"""
    plugin = GitHelperPlugin()
    
    (git_repo / 'test.txt').write_text('modified content')
    
    context = {
        'current_dir': git_repo,
        'args': {'action': 'status'}
    }
    
    result = plugin._handle_status(context)
    
    assert result['success'] is True
    assert ('modified' in result['result'].lower() or 'staged' in result['result'].lower())
    assert ('test.txt' in result['data']['modified'] or 'test.txt' in result['data']['staged'])


def test_git_plugin_status_untracked(git_repo):
    """Verifica status con archivos sin seguimiento"""
    plugin = GitHelperPlugin()
    
    (git_repo / 'new_file.txt').write_text('new content')
    
    context = {
        'current_dir': git_repo,
        'args': {'action': 'status'}
    }
    
    result = plugin._handle_status(context)
    
    assert result['success'] is True
    assert 'untracked' in result['result'].lower()
    assert 'new_file.txt' in result['data']['untracked']


def test_git_plugin_diff(git_repo):
    """Verifica git diff"""
    plugin = GitHelperPlugin()
    
    (git_repo / 'test.txt').write_text('modified content\nline 2\n')
    
    context = {
        'current_dir': git_repo,
        'args': {'action': 'diff', 'files': []}
    }
    
    result = plugin._handle_diff(context)
    
    assert result['success'] is True
    assert result['data']['additions'] > 0


def test_git_plugin_commit(git_repo):
    """Verifica creación de commit"""
    plugin = GitHelperPlugin()
    
    (git_repo / 'test.txt').write_text('commit test')
    subprocess.run(['git', 'add', '.'], cwd=git_repo, check=True)
    
    context = {
        'current_dir': git_repo,
        'args': {
            'action': 'commit',
            'message': 'test: commit message'
        }
    }
    
    result = plugin._handle_commit(context)
    
    assert result['success'] is True
    assert 'commit creado' in result['result'].lower()


def test_git_plugin_log(git_repo):
    """Verifica git log"""
    plugin = GitHelperPlugin()
    
    context = {
        'current_dir': git_repo,
        'args': {'action': 'log', 'limit': 5}
    }
    
    result = plugin._handle_log(context)
    
    assert result['success'] is True
    assert 'Initial commit' in result['result']


def test_git_plugin_not_a_repo(safe_git_repo):
    """Verifica error cuando no es repo Git"""
    plugin = GitHelperPlugin()
    
    context = {
        'current_dir': safe_git_repo,
        'args': {'action': 'status'}
    }
    
    result = plugin.execute(context)
    
    assert result['success'] is False
    assert 'repositorio git' in result['error'].lower()