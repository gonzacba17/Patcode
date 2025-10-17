import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache de respuestas LLM para queries repetidas"""
    
    def __init__(self, cache_dir: str = '.patcode_cache', ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }
        self._load_stats()
    
    def _hash_query(self, messages: List[Dict], files_context: List[Path]) -> str:
        """
        Genera hash único basado en:
        - Últimos 5 mensajes de conversación
        - Nombres de archivos cargados
        """
        context = {
            'messages': [
                {'role': m.get('role'), 'content': m.get('content')[:200]}
                for m in messages[-5:]
            ],
            'files': sorted([str(f) for f in files_context])
        }
        
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]
    
    def get(self, query_hash: str) -> Optional[str]:
        """
        Recupera respuesta cacheada si existe y no expiró
        
        Returns:
            str: Respuesta cacheada o None
        """
        cache_file = self.cache_dir / f"{query_hash}.json"
        
        if not cache_file.exists():
            self.stats['misses'] += 1
            self.stats['total_queries'] += 1
            return None
        
        try:
            data = json.loads(cache_file.read_text())
            
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                logger.info(f"Cache expirado para {query_hash}")
                cache_file.unlink()
                self.stats['misses'] += 1
                self.stats['total_queries'] += 1
                return None
            
            logger.info(f"Cache HIT para {query_hash}")
            self.stats['hits'] += 1
            self.stats['total_queries'] += 1
            self._save_stats()
            
            return data['response']
        
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error leyendo cache: {e}")
            cache_file.unlink()
            self.stats['misses'] += 1
            self.stats['total_queries'] += 1
            return None
    
    def set(self, query_hash: str, response: str, metadata: Dict[str, Any] = None):
        """
        Guarda respuesta en cache con timestamp
        
        Args:
            query_hash: Hash de la query
            response: Respuesta del LLM
            metadata: Info adicional (modelo usado, tokens, etc.)
        """
        cache_file = self.cache_dir / f"{query_hash}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'response': response,
            'metadata': metadata or {}
        }
        
        try:
            cache_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Respuesta cacheada: {query_hash}")
        except Exception as e:
            logger.error(f"Error guardando cache: {e}")
    
    def clear_expired(self):
        """Limpia cache expirado"""
        deleted = 0
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name == 'cache_stats.json':
                continue
            
            try:
                data = json.loads(cache_file.read_text())
                cached_time = datetime.fromisoformat(data['timestamp'])
                
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.error(f"Error limpiando {cache_file}: {e}")
        
        logger.info(f"Cache limpiado: {deleted} archivos eliminados")
        return deleted
    
    def clear_all(self):
        """Limpia todo el cache"""
        deleted = 0
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name == 'cache_stats.json':
                continue
            cache_file.unlink()
            deleted += 1
        
        self.stats = {'hits': 0, 'misses': 0, 'total_queries': 0}
        self._save_stats()
        
        logger.info(f"Cache completo limpiado: {deleted} archivos")
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de cache"""
        total = self.stats['total_queries']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'total_queries': total,
            'cache_hits': self.stats['hits'],
            'cache_misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': self._get_cache_size()
        }
    
    def _get_cache_size(self) -> str:
        """Calcula tamaño total del cache"""
        total_bytes = sum(
            f.stat().st_size 
            for f in self.cache_dir.glob("*.json")
        )
        
        if total_bytes < 1024:
            return f"{total_bytes} B"
        elif total_bytes < 1024**2:
            return f"{total_bytes / 1024:.1f} KB"
        else:
            return f"{total_bytes / 1024**2:.1f} MB"
    
    def _load_stats(self):
        """Carga estadísticas persistentes"""
        stats_file = self.cache_dir / 'cache_stats.json'
        
        if stats_file.exists():
            try:
                self.stats = json.loads(stats_file.read_text())
            except Exception as e:
                logger.error(f"Error cargando stats: {e}")
    
    def _save_stats(self):
        """Guarda estadísticas"""
        stats_file = self.cache_dir / 'cache_stats.json'
        
        try:
            stats_file.write_text(json.dumps(self.stats, indent=2))
        except Exception as e:
            logger.error(f"Error guardando stats: {e}")
