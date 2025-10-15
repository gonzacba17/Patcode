from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
import importlib.util
import inspect
import logging

logger = logging.getLogger(__name__)


class PluginInterface(ABC):
    """Interfaz estándar que todos los plugins deben implementar"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único del plugin"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Versión del plugin (semver)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción corta del plugin"""
        pass
    
    @property
    def author(self) -> str:
        """Autor del plugin (opcional)"""
        return "Unknown"
    
    @property
    def dependencies(self) -> List[str]:
        """Lista de dependencias Python requeridas"""
        return []
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la funcionalidad del plugin
        
        Args:
            context: {
                'agent': PatAgent instance,
                'files': List[Path] - archivos cargados,
                'user_input': str - input del usuario,
                'config': Settings - configuración global,
                'current_dir': Path - directorio actual,
                'args': Dict[str, Any] - argumentos adicionales
            }
        
        Returns:
            {
                'success': bool,
                'result': str - resultado o mensaje,
                'error': Optional[str] - mensaje de error si falló,
                'data': Optional[Any] - datos adicionales
            }
        """
        pass
    
    def validate_dependencies(self) -> bool:
        """Valida que las dependencias estén instaladas"""
        if not self.dependencies:
            return True
        
        for dep in self.dependencies:
            try:
                __import__(dep)
            except ImportError:
                logger.warning(f"Plugin {self.name}: dependencia faltante '{dep}'")
                return False
        
        return True
    
    def on_load(self):
        """Hook llamado cuando el plugin se carga (opcional)"""
        pass
    
    def on_unload(self):
        """Hook llamado cuando el plugin se descarga (opcional)"""
        pass


class PluginManager:
    """Gestor de plugins con auto-descubrimiento"""
    
    def __init__(self, plugins_dir: str = 'tools/plugins'):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginInterface] = {}
        self.failed_plugins: Dict[str, str] = {}
        
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self._discover_plugins()
    
    def _discover_plugins(self):
        """Auto-descubre plugins en el directorio"""
        logger.info(f"Buscando plugins en {self.plugins_dir}")
        
        if not self.plugins_dir.exists():
            logger.warning(f"Directorio de plugins no existe: {self.plugins_dir}")
            return
        
        for plugin_file in self.plugins_dir.glob('*_plugin.py'):
            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                logger.error(f"Error cargando plugin {plugin_file.name}: {e}")
                self.failed_plugins[plugin_file.stem] = str(e)
        
        logger.info(f"Plugins cargados: {len(self.plugins)}")
        if self.failed_plugins:
            logger.warning(f"Plugins fallidos: {len(self.failed_plugins)}")
    
    def _load_plugin(self, plugin_path: Path):
        """Carga un plugin desde archivo"""
        logger.debug(f"Cargando plugin: {plugin_path.name}")
        
        spec = importlib.util.spec_from_file_location(
            plugin_path.stem, plugin_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        plugin_classes = []
        for item_name in dir(module):
            item = getattr(module, item_name)
            
            if (inspect.isclass(item) and 
                issubclass(item, PluginInterface) and 
                item is not PluginInterface):
                plugin_classes.append(item)
        
        if not plugin_classes:
            raise ValueError(f"No se encontró clase PluginInterface en {plugin_path.name}")
        
        if len(plugin_classes) > 1:
            logger.warning(f"Múltiples plugins en {plugin_path.name}, usando el primero")
        
        plugin_class = plugin_classes[0]
        plugin = plugin_class()
        
        if not plugin.validate_dependencies():
            raise ImportError(f"Dependencias faltantes para {plugin.name}")
        
        self.plugins[plugin.name] = plugin
        
        plugin.on_load()
        
        logger.info(f"✅ Plugin cargado: {plugin.name} v{plugin.version}")
    
    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Obtiene un plugin por nombre"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """Lista todos los plugins disponibles"""
        return [
            {
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description,
                'author': plugin.author,
                'dependencies': plugin.dependencies
            }
            for plugin in self.plugins.values()
        ]
    
    def execute_plugin(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un plugin
        
        Args:
            name: Nombre del plugin
            context: Contexto de ejecución
        
        Returns:
            Resultado de la ejecución del plugin
        """
        plugin = self.get_plugin(name)
        
        if not plugin:
            return {
                'success': False,
                'result': '',
                'error': f"Plugin '{name}' no encontrado"
            }
        
        try:
            logger.info(f"Ejecutando plugin: {name}")
            result = plugin.execute(context)
            
            if result.get('success'):
                logger.info(f"✅ Plugin {name} ejecutado correctamente")
            else:
                logger.warning(f"⚠️  Plugin {name} falló: {result.get('error')}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error ejecutando plugin {name}: {e}")
            return {
                'success': False,
                'result': '',
                'error': str(e)
            }
    
    def reload_plugin(self, name: str):
        """Recarga un plugin"""
        if name in self.plugins:
            plugin = self.plugins[name]
            plugin.on_unload()
            del self.plugins[name]
        
        plugin_file = self.plugins_dir / f"{name}_plugin.py"
        
        if plugin_file.exists():
            self._load_plugin(plugin_file)
        else:
            raise FileNotFoundError(f"Plugin file not found: {plugin_file}")
    
    def unload_plugin(self, name: str):
        """Descarga un plugin"""
        if name in self.plugins:
            plugin = self.plugins[name]
            plugin.on_unload()
            del self.plugins[name]
            logger.info(f"Plugin descargado: {name}")
        else:
            logger.warning(f"Plugin no encontrado: {name}")


_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """Obtiene instancia singleton del PluginManager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
