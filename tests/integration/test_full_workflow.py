import pytest
from unittest.mock import Mock, patch
from agents.pat_agent import PatAgent


class TestFullWorkflow:
    
    @pytest.fixture
    def mock_llm_manager(self):
        mock = Mock()
        mock.generate.return_value = "Test response from LLM"
        mock.get_current_provider.return_value = "ollama"
        return mock
    
    @pytest.fixture
    def agent_with_mocks(self, mock_llm_manager):
        from utils.file_manager import FileManager
        from utils.response_cache import ResponseCache
        
        file_manager = FileManager()
        cache = ResponseCache(cache_dir='.test_cache', ttl_hours=1)
        
        agent = PatAgent(
            llm_manager=mock_llm_manager,
            file_manager=file_manager,
            cache=cache
        )
        return agent
    
    def test_ask_returns_response(self, agent_with_mocks):
        response = agent_with_mocks.ask("test question")
        assert response is not None
        assert isinstance(response, str)
    
    def test_ask_saves_to_history(self, agent_with_mocks):
        initial_count = len(agent_with_mocks.memory_manager.active_memory)
        agent_with_mocks.ask("test question")
        final_count = len(agent_with_mocks.memory_manager.active_memory)
        
        assert final_count > initial_count
    
    def test_clear_history_works(self, agent_with_mocks):
        agent_with_mocks.ask("test question")
        agent_with_mocks.clear_history()
        
        assert len(agent_with_mocks.memory_manager.active_memory) == 0
