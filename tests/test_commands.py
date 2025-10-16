"""
Tests para el sistema de comandos slash.
"""
import pytest
from cli.commands import command_registry, Command

def test_command_registration():
    assert 'help' in command_registry.commands
    assert 'exit' in command_registry.commands
    assert 'git' in command_registry.commands
    assert 'search' in command_registry.commands

def test_help_command():
    help_text = command_registry.get_help()
    assert '📚' in help_text
    assert '/help' in help_text
    assert 'GENERAL' in help_text

def test_help_specific_command():
    help_text = command_registry.get_help('help')
    assert '/help' in help_text
    assert 'Muestra ayuda' in help_text

def test_command_aliases():
    assert command_registry.commands['h'] == command_registry.commands['help']
    assert command_registry.commands['q'] == command_registry.commands['exit']
    assert command_registry.commands['cls'] == command_registry.commands['clear']

def test_command_execution():
    class MockContext:
        pass
    
    ctx = MockContext()
    result = command_registry.execute('/help', ctx)
    assert isinstance(result, str)
    assert len(result) > 0

def test_unknown_command():
    class MockContext:
        pass
    
    result = command_registry.execute('/unknowncommand', MockContext())
    assert '❌' in result
    assert 'desconocido' in result.lower()

def test_command_categories():
    assert 'general' in command_registry.categories
    assert 'context' in command_registry.categories
    assert 'rag' in command_registry.categories
    assert len(command_registry.categories) >= 4

def test_exit_command():
    class MockContext:
        pass
    
    result = command_registry.execute('/exit', MockContext())
    assert result == "exit"

def test_stats_command():
    class MockContext:
        def __init__(self):
            self.memory_manager = None
            self.vector_store = None
    
    result = command_registry.execute('/stats', MockContext())
    assert '📊' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
