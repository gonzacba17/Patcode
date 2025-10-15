import psutil
import platform
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """Perfil de un modelo LLM"""
    name: str
    ram_min: int
    ram_recommended: int
    speed: str
    use_cases: List[str]
    parameters: str
    
    def __repr__(self):
        return f"{self.name} ({self.parameters}, {self.speed})"


class ModelSelector:
    """Selector automático de modelos según hardware"""
    
    MODELS = {
        'llama3.2:1b': ModelProfile(
            name='llama3.2:1b',
            ram_min=4,
            ram_recommended=6,
            speed='fast',
            use_cases=['quick_questions', 'simple_explanations', 'chat'],
            parameters='1B'
        ),
        'llama3.2:3b': ModelProfile(
            name='llama3.2:3b',
            ram_min=8,
            ram_recommended=12,
            speed='balanced',
            use_cases=['general', 'coding', 'analysis', 'refactor'],
            parameters='3B'
        ),
        'codellama:7b': ModelProfile(
            name='codellama:7b',
            ram_min=12,
            ram_recommended=16,
            speed='balanced',
            use_cases=['coding', 'debugging', 'architecture'],
            parameters='7B'
        ),
        'codellama:13b': ModelProfile(
            name='codellama:13b',
            ram_min=16,
            ram_recommended=24,
            speed='deep',
            use_cases=['refactor', 'analyze', 'complex_debugging'],
            parameters='13B'
        ),
        'mistral:7b': ModelProfile(
            name='mistral:7b',
            ram_min=12,
            ram_recommended=16,
            speed='balanced',
            use_cases=['general', 'coding', 'documentation'],
            parameters='7B'
        )
    }
    
    def __init__(self):
        self.system_info = self._detect_hardware()
    
    def _detect_hardware(self) -> Dict:
        """Detecta hardware del sistema"""
        memory = psutil.virtual_memory()
        
        info = {
            'total_ram_gb': memory.total / (1024**3),
            'available_ram_gb': memory.available / (1024**3),
            'cpu_count': psutil.cpu_count(logical=True),
            'platform': platform.system(),
            'machine': platform.machine()
        }
        
        logger.info(f"Hardware detectado: {info}")
        return info
    
    def recommend_model(self, use_case: str = 'general') -> str:
        """
        Recomienda modelo basado en hardware y caso de uso
        
        Args:
            use_case: 'quick_questions', 'general', 'coding', 'refactor', etc.
        
        Returns:
            str: Nombre del modelo recomendado
        """
        available_ram = self.system_info['available_ram_gb']
        
        suitable_models = []
        for model_name, profile in self.MODELS.items():
            if profile.ram_min <= available_ram * 0.8:
                suitable_models.append((model_name, profile))
        
        if not suitable_models:
            logger.warning("RAM insuficiente para modelos estándar")
            return 'llama3.2:1b'
        
        filtered = [
            (name, prof) for name, prof in suitable_models
            if use_case in prof.use_cases
        ]
        
        if not filtered:
            filtered = [
                (name, prof) for name, prof in suitable_models
                if 'general' in prof.use_cases
            ]
        
        if not filtered:
            filtered = suitable_models
        
        filtered.sort(key=lambda x: x[1].ram_recommended, reverse=True)
        
        recommended = filtered[0][0]
        logger.info(f"Modelo recomendado: {recommended} para {use_case}")
        
        return recommended
    
    def get_model_info(self, model_name: str) -> Optional[ModelProfile]:
        """Obtiene información de un modelo"""
        return self.MODELS.get(model_name)
    
    def list_compatible_models(self) -> List[str]:
        """Lista modelos compatibles con el hardware actual"""
        available_ram = self.system_info['available_ram_gb']
        
        compatible = [
            name for name, profile in self.MODELS.items()
            if profile.ram_min <= available_ram * 0.8
        ]
        
        return compatible
    
    def get_speed_recommendation(self, model_name: str) -> str:
        """Retorna recomendación de velocidad para un modelo"""
        profile = self.get_model_info(model_name)
        
        if not profile:
            return "unknown"
        
        available_ram = self.system_info['available_ram_gb']
        
        if available_ram < profile.ram_recommended:
            return f"⚠️  {profile.speed} (RAM limitada, puede ser lento)"
        elif available_ram >= profile.ram_recommended * 1.5:
            return f"⚡ {profile.speed} (optimal)"
        else:
            return f"✅ {profile.speed}"
    
    def should_use_cache(self, model_name: str) -> bool:
        """Determina si se debe usar cache agresivamente"""
        profile = self.get_model_info(model_name)
        
        if not profile:
            return True
        
        return profile.speed in ['balanced', 'deep']


_selector = None

def get_model_selector() -> ModelSelector:
    """Obtiene instancia singleton de ModelSelector"""
    global _selector
    if _selector is None:
        _selector = ModelSelector()
    return _selector
