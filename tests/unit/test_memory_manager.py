import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from agents.memory.memory_manager import MemoryManager, MemoryConfig


class TestMemoryManager:
    
    @pytest.fixture
    def memory_config(self):
        return MemoryConfig(
            max_active_messages=50,
            max_file_size_bytes=1024 * 1024,
            archive_dir=None,
            ollama_url="http://localhost:11434",
            summarize_model="codellama"
        )
    
    def test_memory_manager_initialization(self, memory_config):
        manager = MemoryManager(memory_config)
        assert len(manager.active_memory) == 0
        assert len(manager.passive_summaries) == 0
    
    def test_add_message(self, memory_config):
        manager = MemoryManager(memory_config)
        manager.add_message("user", "test message")
        
        assert len(manager.active_memory) == 1
        assert manager.active_memory[0]["role"] == "user"
        assert manager.active_memory[0]["content"] == "test message"
    
    def test_get_full_context(self, memory_config):
        manager = MemoryManager(memory_config)
        manager.add_message("user", "message 1")
        manager.add_message("assistant", "response 1")
        
        context = manager.get_full_context()
        assert len(context) == 2
    
    def test_clear_all(self, memory_config):
        manager = MemoryManager(memory_config)
        manager.add_message("user", "test")
        manager.clear_all()
        
        assert len(manager.active_memory) == 0
        assert len(manager.passive_summaries) == 0
    
    def test_get_stats(self, memory_config):
        manager = MemoryManager(memory_config)
        manager.add_message("user", "test")
        
        stats = manager.get_stats()
        assert stats["active_messages"] == 1
        assert stats["passive_summaries"] == 0
        assert "total_context" in stats
