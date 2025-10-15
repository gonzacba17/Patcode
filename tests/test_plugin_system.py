import pytest
from pathlib import Path
import shutil
from tools.plugin_system import PluginInterface, PluginManager


class DummyPlugin(PluginInterface):
    """Plugin de prueba"""
    
    @property
    def name(self) -> str:
        return "dummy"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Plugin de prueba"
    
    def execute(self, context):
        return {
            'success': True,
            'result': 'Dummy executed',
            'data': context
        }


@pytest.fixture
def temp_plugins_dir(tmp_path):
    """Directorio temporal para plugins"""
    plugins_dir = tmp_path / 'plugins'
    plugins_dir.mkdir()
    
    plugin_code = '''
from tools.plugin_system import PluginInterface

class TestPlugin(PluginInterface):
    @property
    def name(self):
        return "test_plugin"
    
    @property
    def version(self):
        return "0.1.0"
    
    @property
    def description(self):
        return "Test plugin"
    
    def execute(self, context):
        return {'success': True, 'result': 'OK'}
'''
    
    (plugins_dir / 'test_plugin.py').write_text(plugin_code)
    
    yield plugins_dir
    
    if plugins_dir.exists():
        shutil.rmtree(plugins_dir)


def test_plugin_interface():
    """Verifica interfaz de plugin"""
    plugin = DummyPlugin()
    
    assert plugin.name == "dummy"
    assert plugin.version == "1.0.0"
    assert plugin.description == "Plugin de prueba"
    assert plugin.validate_dependencies() == True


def test_plugin_execute():
    """Verifica ejecución de plugin"""
    plugin = DummyPlugin()
    
    context = {'test': 'data'}
    result = plugin.execute(context)
    
    assert result['success'] == True
    assert result['result'] == 'Dummy executed'
    assert result['data'] == context


def test_plugin_manager_init(temp_plugins_dir):
    """Verifica inicialización del manager"""
    manager = PluginManager(plugins_dir=str(temp_plugins_dir))
    
    assert manager.plugins_dir == temp_plugins_dir
    assert isinstance(manager.plugins, dict)


def test_plugin_manager_discover(temp_plugins_dir):
    """Verifica descubrimiento de plugins"""
    manager = PluginManager(plugins_dir=str(temp_plugins_dir))
    
    assert 'test_plugin' in manager.plugins
    assert manager.plugins['test_plugin'].version == "0.1.0"


def test_plugin_manager_get(temp_plugins_dir):
    """Verifica obtención de plugin"""
    manager = PluginManager(plugins_dir=str(temp_plugins_dir))
    
    plugin = manager.get_plugin('test_plugin')
    assert plugin is not None
    assert plugin.name == 'test_plugin'
    
    plugin = manager.get_plugin('nonexistent')
    assert plugin is None


def test_plugin_manager_list(temp_plugins_dir):
    """Verifica listado de plugins"""
    manager = PluginManager(plugins_dir=str(temp_plugins_dir))
    
    plugins = manager.list_plugins()
    assert len(plugins) == 1
    assert plugins[0]['name'] == 'test_plugin'
    assert 'version' in plugins[0]
    assert 'description' in plugins[0]


def test_plugin_manager_execute(temp_plugins_dir):
    """Verifica ejecución vía manager"""
    manager = PluginManager(plugins_dir=str(temp_plugins_dir))
    
    context = {'test': 'data'}
    result = manager.execute_plugin('test_plugin', context)
    
    assert result['success'] == True
    assert result['result'] == 'OK'


def test_plugin_manager_execute_not_found(temp_plugins_dir):
    """Verifica error con plugin inexistente"""
    manager = PluginManager(plugins_dir=str(temp_plugins_dir))
    
    result = manager.execute_plugin('nonexistent', {})
    
    assert result['success'] == False
    assert 'no encontrado' in result['error'].lower()


def test_plugin_dependencies():
    """Verifica validación de dependencias"""
    
    class PluginWithDeps(PluginInterface):
        @property
        def name(self):
            return "test"
        
        @property
        def version(self):
            return "1.0.0"
        
        @property
        def description(self):
            return "Test"
        
        @property
        def dependencies(self):
            return ['nonexistent_package_xyz']
        
        def execute(self, context):
            return {'success': True}
    
    plugin = PluginWithDeps()
    assert plugin.validate_dependencies() == False
