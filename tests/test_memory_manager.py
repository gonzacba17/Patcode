"""
Tests para el sistema de gestión de memoria (MemoryManager).
"""

import pytest
import json
from pathlib import Path
from agents.memory.memory_manager import MemoryManager, MemoryConfig


@pytest.fixture
def temp_memory_dir(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    return memory_dir, archive_dir


@pytest.fixture
def memory_config(temp_memory_dir):
    memory_dir, archive_dir = temp_memory_dir
    return MemoryConfig(
        max_active_messages=5,
        max_file_size_bytes=1024,
        archive_dir=archive_dir,
        ollama_url="http://localhost:11434/api/generate",
        summarize_model="qwen2.5-coder:7b"
    )


@pytest.fixture
def memory_manager(memory_config):
    return MemoryManager(memory_config)


def test_add_message(memory_manager):
    memory_manager.add_message("user", "Hola")
    
    assert len(memory_manager.active_memory) == 1
    assert memory_manager.active_memory[0]["role"] == "user"
    assert memory_manager.active_memory[0]["content"] == "Hola"


def test_rotation_when_exceeds_limit(memory_manager, monkeypatch):
    def mock_summarize(messages):
        return "Resumen de mensajes"
    
    monkeypatch.setattr(memory_manager, '_summarize_messages', mock_summarize)
    
    for i in range(10):
        memory_manager.add_message("user", f"Mensaje {i}")
    
    assert len(memory_manager.active_memory) <= memory_manager.config.max_active_messages
    assert len(memory_manager.passive_memory) > 0


def test_get_full_context(memory_manager):
    memory_manager.add_message("user", "Pregunta")
    memory_manager.add_message("assistant", "Respuesta")
    
    full_context = memory_manager.get_full_context()
    
    assert len(full_context) >= 2


def test_get_active_context(memory_manager):
    memory_manager.add_message("user", "Test")
    
    active_context = memory_manager.get_active_context()
    
    assert len(active_context) == 1
    assert active_context[0]["content"] == "Test"


def test_clear_all(memory_manager):
    memory_manager.add_message("user", "Test")
    memory_manager.clear_all()
    
    assert len(memory_manager.active_memory) == 0
    assert len(memory_manager.passive_memory) == 0


def test_save_and_load(memory_manager, temp_memory_dir):
    memory_dir, _ = temp_memory_dir
    memory_file = memory_dir / "test_memory.json"
    
    memory_manager.add_message("user", "Test message")
    memory_manager.add_message("assistant", "Test response")
    
    memory_manager.save_to_file(memory_file)
    
    assert memory_file.exists()
    
    new_manager = MemoryManager(memory_manager.config)
    new_manager.load_from_file(memory_file)
    
    assert len(new_manager.active_memory) == 2


def test_archive_when_file_too_large(memory_manager, temp_memory_dir):
    memory_dir, archive_dir = temp_memory_dir
    memory_file = memory_dir / "large_memory.json"
    
    with open(memory_file, 'w') as f:
        large_data = [{"role": "user", "content": "x" * 500}] * 10
        json.dump(large_data, f)
    
    memory_manager.add_message("user", "New message")
    memory_manager.save_to_file(memory_file)
    
    archives = list(archive_dir.glob("memory_archive_*.json"))
    assert len(archives) > 0 or memory_file.stat().st_size < memory_manager.config.max_file_size_bytes


def test_get_stats(memory_manager):
    memory_manager.add_message("user", "Test1")
    memory_manager.add_message("assistant", "Test2")
    
    stats = memory_manager.get_stats()
    
    assert stats["active_messages"] == 2
    assert stats["total_context"] >= 2


def test_load_from_nonexistent_file(memory_manager, temp_memory_dir):
    memory_dir, _ = temp_memory_dir
    nonexistent_file = memory_dir / "nonexistent.json"
    
    memory_manager.load_from_file(nonexistent_file)
    
    assert len(memory_manager.active_memory) == 0


def test_switch_context(memory_manager, temp_memory_dir):
    memory_dir, _ = temp_memory_dir
    
    context_file = memory_manager.switch_context("project_x", memory_dir)
    
    assert context_file.name == "memory_project_x.json"
    assert context_file.parent == memory_dir
