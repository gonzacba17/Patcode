"""Clases base para el sistema de plugins"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import inspect
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PluginPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LAST = 5

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    priority: PluginPriority = PluginPriority.NORMAL
    enabled: bool = True
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class PluginContext:
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.agent = None
        self.memory = None
        self.provider = None
    
    def set(self, key: str, value: Any):
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def has(self, key: str) -> bool:
        return key in self.data

class PluginResult:
    
    def __init__(
        self,
        success: bool = True,
        data: Any = None,
        error: Optional[str] = None,
        should_continue: bool = True
    ):
        self.success = success
        self.data = data
        self.error = error
        self.should_continue = should_continue

class Plugin(ABC):
    
    def __init__(self):
        self._metadata = self.metadata()
        self._enabled = self._metadata.enabled
        logger.info(f"Plugin cargado: {self._metadata.name} v{self._metadata.version}")
    
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        pass
    
    @abstractmethod
    def can_handle(self, user_input: str, context: PluginContext) -> bool:
        pass
    
    @abstractmethod
    def execute(self, user_input: str, context: PluginContext) -> PluginResult:
        pass
    
    def on_load(self, context: PluginContext):
        pass
    
    def on_unload(self, context: PluginContext):
        pass
    
    def enable(self):
        self._enabled = True
        logger.info(f"Plugin habilitado: {self._metadata.name}")
    
    def disable(self):
        self._enabled = False
        logger.info(f"Plugin deshabilitado: {self._metadata.name}")
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    @property
    def name(self) -> str:
        return self._metadata.name

class PluginManager:
    
    def __init__(self):
        self.plugins: List[Plugin] = []
        self.context = PluginContext()
        logger.info("PluginManager inicializado")
    
    def register(self, plugin: Plugin):
        for dep in plugin._metadata.dependencies:
            if not self._has_plugin(dep):
                logger.warning(
                    f"Plugin {plugin.name} requiere {dep} pero no está disponible"
                )
        
        self.plugins.append(plugin)
        plugin.on_load(self.context)
        
        self.plugins.sort(key=lambda p: p._metadata.priority.value)
        
        logger.info(f"Plugin registrado: {plugin.name}")
    
    def unregister(self, plugin_name: str):
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.on_unload(self.context)
            self.plugins.remove(plugin)
            logger.info(f"Plugin desregistrado: {plugin_name}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None
    
    def _has_plugin(self, name: str) -> bool:
        return self.get_plugin(name) is not None
    
    def execute_chain(self, user_input: str) -> List[PluginResult]:
        results = []
        
        for plugin in self.plugins:
            if not plugin.is_enabled:
                continue
            
            try:
                if plugin.can_handle(user_input, self.context):
                    logger.debug(f"Ejecutando plugin: {plugin.name}")
                    result = plugin.execute(user_input, self.context)
                    results.append(result)
                    
                    if not result.should_continue:
                        logger.debug(f"Plugin {plugin.name} detuvo la cadena")
                        break
            
            except Exception as e:
                logger.error(f"Error en plugin {plugin.name}: {e}", exc_info=True)
                results.append(PluginResult(
                    success=False,
                    error=str(e),
                    should_continue=True
                ))
        
        return results
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": p.name,
                "version": p._metadata.version,
                "author": p._metadata.author,
                "description": p._metadata.description,
                "enabled": p.is_enabled,
                "priority": p._metadata.priority.name
            }
            for p in self.plugins
        ]
    
    def set_context(self, agent, memory, provider):
        self.context.agent = agent
        self.context.memory = memory
        self.context.provider = provider
