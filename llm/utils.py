"""
Utils - FASE 2: Sistema Multi-LLM

Utilidades para el sistema LLM: Rate Limiter, Response Cache, etc.
"""

import time
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter para controlar el uso de APIs con límites.
    
    Rastrea requests por minuto y por día para evitar exceder
    los límites de los providers.
    """
    
    def __init__(self, requests_per_minute: int, requests_per_day: int):
        """
        Inicializa el rate limiter.
        
        Args:
            requests_per_minute: Límite de requests por minuto
            requests_per_day: Límite de requests por día
        """
        self.rpm_limit = requests_per_minute
        self.rpd_limit = requests_per_day
        
        self.minute_requests = deque()
        self.day_requests = deque()
    
    def can_make_request(self) -> bool:
        """
        Verifica si se puede hacer una request sin exceder límites.
        
        Returns:
            True si se puede hacer request, False si no
        """
        now = datetime.now()
        self._cleanup_old_requests(now)
        
        if len(self.minute_requests) >= self.rpm_limit:
            logger.warning(f"Rate limit RPM alcanzado: {len(self.minute_requests)}/{self.rpm_limit}")
            return False
        
        if len(self.day_requests) >= self.rpd_limit:
            logger.warning(f"Rate limit RPD alcanzado: {len(self.day_requests)}/{self.rpd_limit}")
            return False
        
        return True
    
    def record_request(self) -> None:
        """Registra que se hizo una request."""
        now = datetime.now()
        self.minute_requests.append(now)
        self.day_requests.append(now)
        
        logger.debug(f"Request recorded: RPM={len(self.minute_requests)}/{self.rpm_limit}, RPD={len(self.day_requests)}/{self.rpd_limit}")
    
    def _cleanup_old_requests(self, now: datetime) -> None:
        """
        Elimina requests que ya expiraron.
        
        Args:
            now: Timestamp actual
        """
        minute_ago = now - timedelta(minutes=1)
        day_ago = now - timedelta(days=1)
        
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()
        
        while self.day_requests and self.day_requests[0] < day_ago:
            self.day_requests.popleft()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna estado actual del rate limiter.
        
        Returns:
            Dict con información de límites
        """
        now = datetime.now()
        self._cleanup_old_requests(now)
        
        return {
            "has_limit": True,
            "rpm_remaining": self.rpm_limit - len(self.minute_requests),
            "rpm_limit": self.rpm_limit,
            "rpm_used": len(self.minute_requests),
            "rpd_remaining": self.rpd_limit - len(self.day_requests),
            "rpd_limit": self.rpd_limit,
            "rpd_used": len(self.day_requests)
        }
    
    def reset(self) -> None:
        """Resetea el rate limiter (útil para testing)."""
        self.minute_requests.clear()
        self.day_requests.clear()
        logger.info("Rate limiter reset")


class ResponseCache:
    """
    Caché simple para respuestas de LLM.
    
    Cachea respuestas basándose en el prompt para evitar
    requests duplicadas.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Inicializa el caché.
        
        Args:
            max_size: Tamaño máximo del caché
            ttl_seconds: Tiempo de vida de las entradas en segundos
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, prompt: str) -> Optional[str]:
        """
        Obtiene una respuesta del caché.
        
        Args:
            prompt: El prompt a buscar
            
        Returns:
            La respuesta cacheada o None si no existe/expiró
        """
        cache_key = self._hash_prompt(prompt)
        
        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]
        
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self.cache[cache_key]
            logger.debug(f"Cache entry expired for prompt hash: {cache_key[:16]}...")
            return None
        
        logger.info(f"Cache hit for prompt hash: {cache_key[:16]}...")
        return entry["response"]
    
    def set(self, prompt: str, response: str) -> None:
        """
        Guarda una respuesta en el caché.
        
        Args:
            prompt: El prompt
            response: La respuesta a cachear
        """
        cache_key = self._hash_prompt(prompt)
        
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
            logger.debug(f"Cache full, removed oldest entry")
        
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        logger.debug(f"Cached response for prompt hash: {cache_key[:16]}...")
    
    def clear(self) -> None:
        """Limpia el caché."""
        self.cache.clear()
        logger.info("Response cache cleared")
    
    def _hash_prompt(self, prompt: str) -> str:
        """
        Genera un hash del prompt para usar como key.
        
        Args:
            prompt: El prompt
            
        Returns:
            Hash del prompt
        """
        import hashlib
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del caché.
        
        Returns:
            Dict con estadísticas
        """
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }
