import pytest
from pathlib import Path
import time
import shutil
from utils.response_cache import ResponseCache


@pytest.fixture
def temp_cache(tmp_path):
    """Cache temporal para tests"""
    cache = ResponseCache(cache_dir=str(tmp_path / 'test_cache'), ttl_hours=1)
    yield cache
    if cache.cache_dir.exists():
        shutil.rmtree(cache.cache_dir)


def test_cache_init(temp_cache):
    """Verifica inicialización"""
    assert temp_cache.cache_dir.exists()
    assert temp_cache.stats['hits'] == 0
    assert temp_cache.stats['misses'] == 0


def test_cache_set_get(temp_cache):
    """Verifica guardado y recuperación"""
    messages = [{'role': 'user', 'content': 'test message'}]
    files = []
    
    query_hash = temp_cache._hash_query(messages, files)
    response = "This is a test response"
    
    temp_cache.set(query_hash, response)
    
    cached = temp_cache.get(query_hash)
    assert cached == response
    assert temp_cache.stats['hits'] == 1


def test_cache_miss(temp_cache):
    """Verifica cache miss"""
    result = temp_cache.get("nonexistent_hash")
    assert result is None
    assert temp_cache.stats['misses'] == 1


def test_cache_expiration(temp_cache):
    """Verifica expiración de cache"""
    short_cache = ResponseCache(
        cache_dir=str(temp_cache.cache_dir / 'short'),
        ttl_hours=0.0001
    )
    
    messages = [{'role': 'user', 'content': 'expire test'}]
    query_hash = short_cache._hash_query(messages, [])
    
    short_cache.set(query_hash, "will expire")
    
    time.sleep(1)
    
    result = short_cache.get(query_hash)
    assert result is None


def test_hash_consistency(temp_cache):
    """Verifica que el hash sea consistente"""
    messages = [{'role': 'user', 'content': 'same message'}]
    files = [Path('test.py')]
    
    hash1 = temp_cache._hash_query(messages, files)
    hash2 = temp_cache._hash_query(messages, files)
    
    assert hash1 == hash2


def test_hash_different(temp_cache):
    """Verifica que contextos diferentes generen hashes diferentes"""
    messages1 = [{'role': 'user', 'content': 'message 1'}]
    messages2 = [{'role': 'user', 'content': 'message 2'}]
    
    hash1 = temp_cache._hash_query(messages1, [])
    hash2 = temp_cache._hash_query(messages2, [])
    
    assert hash1 != hash2


def test_cache_stats(temp_cache):
    """Verifica estadísticas"""
    messages = [{'role': 'user', 'content': 'stats test'}]
    query_hash = temp_cache._hash_query(messages, [])
    
    temp_cache.get(query_hash)
    
    temp_cache.set(query_hash, "response")
    temp_cache.get(query_hash)
    
    stats = temp_cache.get_stats()
    assert stats['cache_hits'] == 1
    assert stats['cache_misses'] == 1
    assert stats['total_queries'] == 2


def test_clear_expired(temp_cache):
    """Verifica limpieza de cache expirado"""
    short_cache = ResponseCache(
        cache_dir=str(temp_cache.cache_dir / 'expire'),
        ttl_hours=0.0001
    )
    
    for i in range(3):
        messages = [{'role': 'user', 'content': f'msg {i}'}]
        hash_key = short_cache._hash_query(messages, [])
        short_cache.set(hash_key, f"response {i}")
    
    time.sleep(1)
    
    deleted = short_cache.clear_expired()
    assert deleted == 3


def test_clear_all(temp_cache):
    """Verifica limpieza total"""
    for i in range(5):
        messages = [{'role': 'user', 'content': f'msg {i}'}]
        hash_key = temp_cache._hash_query(messages, [])
        temp_cache.set(hash_key, f"response {i}")
    
    deleted = temp_cache.clear_all()
    assert deleted == 5
    assert temp_cache.stats['hits'] == 0
