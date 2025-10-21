"""Registry para auto-discovery de plugins"""

import importlib
import pkgutil
from pathlib import Path
from typing import List, Type
from .base import Plugin, PluginManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PluginRegistry:
    
    @staticmethod
    def discover_plugins(plugin_dir: Path = None) -> List[Type[Plugin]]:
        if plugin_dir is None:
            plugin_dir = Path(__file__).parent / "builtin"
        
        discovered = []
        
        if not plugin_dir.exists():
            logger.warning(f"Directorio de plugins no existe: {plugin_dir}")
            return discovered
        
        for importer, modname, ispkg in pkgutil.iter_modules([str(plugin_dir)]):
            try:
                module = importlib.import_module(f"plugins.builtin.{modname}")
                
                for name, obj in module.__dict__.items():
                    if (
                        isinstance(obj, type) and
                        issubclass(obj, Plugin) and
                        obj is not Plugin
                    ):
                        discovered.append(obj)
                        logger.debug(f"Plugin descubierto: {name}")
            
            except Exception as e:
                logger.error(f"Error cargando plugin {modname}: {e}")
        
        return discovered
    
    @staticmethod
    def load_plugins(manager: PluginManager, plugin_dir: Path = None):
        plugin_classes = PluginRegistry.discover_plugins(plugin_dir)
        
        for plugin_class in plugin_classes:
            try:
                plugin_instance = plugin_class()
                manager.register(plugin_instance)
            except Exception as e:
                logger.error(f"Error instanciando plugin {plugin_class.__name__}: {e}")
        
        logger.info(f"Cargados {len(plugin_classes)} plugins")
