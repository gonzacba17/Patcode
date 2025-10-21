"""Gestor de caché inteligente para respuestas LLM"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class CacheEntry:
    key: str
    prompt: str
    response: str
    context_hash: str
    timestamp: float
    hits: int = 0
    model: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        return cls(**data)
    
    def is_expired(self, ttl_seconds: int) -> bool:
        age = time.time() - self.timestamp
        return age > ttl_seconds

class CacheManager:
    
    def __init__(
        self,
        cache_path: Path,
        max_entries: int = 1000,
        ttl_seconds: int = 86400,
        similarity_threshold: float = 0.85
    ):
        self.cache_path = Path(cache_path)
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.similarity_threshold = similarity_threshold
        
        self.cache: Dict[str, CacheEntry] = {}
        
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_from_disk()
        
        logger.info(f"CacheManager inicializado: {len(self.cache)} entradas")
    
    def _generate_key(self, prompt: str, context: List[str]) -> str:
        combined = prompt + "|".join(context)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _generate_context_hash(self, context: List[str]) -> str:
        return hashlib.sha256("|".join(context).encode()).hexdigest()
    
    def get(
        self,
        prompt: str,
        context: List[str],
        model: str = ""
    ) -> Optional[str]:
        key = self._generate_key(prompt, context)
        
        if key in self.cache:
            entry = self.cache[key]
            
            if entry.is_expired(self.ttl_seconds):
                logger.debug(f"Cache entry expirado: {key[:8]}")
                del self.cache[key]
                self.stats["misses"] += 1
                return None
            
            if model and entry.model != model:
                self.stats["misses"] += 1
                return None
            
            entry.hits += 1
            self.stats["hits"] += 1
            logger.info(f"Cache HIT: {key[:8]} (hits: {entry.hits})")
            return entry.response
        
        similar = self._find_similar(prompt, context, model)
        if similar:
            self.stats["hits"] += 1
            return similar.response
        
        self.stats["misses"] += 1
        return None
    
    def set(
        self,
        prompt: str,
        response: str,
        context: List[str],
        model: str = "",
        metadata: Dict[str, Any] = None
    ):
        key = self._generate_key(prompt, context)
        context_hash = self._generate_context_hash(context)
        
        entry = CacheEntry(
            key=key,
            prompt=prompt,
            response=response,
            context_hash=context_hash,
            timestamp=time.time(),
            model=model,
            metadata=metadata or {}
        )
        
        self.cache[key] = entry
        logger.debug(f"Cache SET: {key[:8]}")
        
        if len(self.cache) > self.max_entries:
            self._evict_lru()
        
        if len(self.cache) % 10 == 0:
            self._save_to_disk()
    
    def _find_similar(
        self,
        prompt: str,
        context: List[str],
        model: str = ""
    ) -> Optional[CacheEntry]:
        context_hash = self._generate_context_hash(context)
        best_match = None
        best_similarity = 0.0
        
        prompt_words = set(prompt.lower().split())
        
        for entry in self.cache.values():
            if entry.context_hash != context_hash:
                continue
            
            if model and entry.model != model:
                continue
            
            if entry.is_expired(self.ttl_seconds):
                continue
            
            entry_words = set(entry.prompt.lower().split())
            similarity = self._jaccard_similarity(prompt_words, entry_words)
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = entry
        
        if best_match:
            logger.info(f"Cache SIMILAR HIT: {best_similarity:.2f}")
            best_match.hits += 1
        
        return best_match
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _evict_lru(self):
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: (x[1].hits, x[1].timestamp)
        )
        
        evict_count = max(1, int(self.max_entries * 0.1))
        
        for key, _ in sorted_entries[:evict_count]:
            del self.cache[key]
            self.stats["evictions"] += 1
        
        logger.info(f"Cache eviction: {evict_count} entradas removidas")
    
    def clear(self):
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._save_to_disk()
        logger.info("Caché limpiado completamente")
    
    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )
        
        return {
            "entries": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "evictions": self.stats["evictions"],
            "size_mb": self._calculate_size_mb()
        }
    
    def _calculate_size_mb(self) -> float:
        if not self.cache_path.exists():
            return 0.0
        
        return self.cache_path.stat().st_size / (1024 * 1024)
    
    def _load_from_disk(self):
        if not self.cache_path.exists():
            return
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry_dict in data.get("entries", []):
                entry = CacheEntry.from_dict(entry_dict)
                
                if not entry.is_expired(self.ttl_seconds):
                    self.cache[entry.key] = entry
            
            if "stats" in data:
                self.stats.update(data["stats"])
            
            logger.info(f"Caché cargado desde disco: {len(self.cache)} entradas")
        
        except Exception as e:
            logger.error(f"Error cargando caché: {e}")
    
    def _save_to_disk(self):
        try:
            data = {
                "entries": [entry.to_dict() for entry in self.cache.values()],
                "stats": self.stats,
                "saved_at": datetime.now().isoformat()
            }
            
            temp_path = self.cache_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_path.replace(self.cache_path)
            logger.debug("Caché guardado a disco")
        
        except Exception as e:
            logger.error(f"Error guardando caché: {e}")
    
    def cleanup_expired(self):
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired(self.ttl_seconds)
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Limpiadas {len(expired_keys)} entradas expiradas")
        
        self._save_to_disk()
    
    def __del__(self):
        self._save_to_disk()
