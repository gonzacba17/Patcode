import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.llm_manager import LLMManager, RateLimiter
from exceptions import LLMRateLimitError


class TestRateLimiter:
    
    def test_rate_limiter_allows_calls_under_limit(self):
        limiter = RateLimiter(max_calls=3, period=60)
        
        @limiter
        def test_func():
            return "success"
        
        assert test_func() == "success"
        assert test_func() == "success"
        assert test_func() == "success"
    
    def test_rate_limiter_blocks_calls_over_limit(self):
        limiter = RateLimiter(max_calls=2, period=60)
        
        @limiter
        def test_func():
            return "success"
        
        test_func()
        test_func()
        
        with pytest.raises(LLMRateLimitError):
            test_func()


class TestLLMManager:
    
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.ollama_url = "http://localhost:11434"
        config.ollama_model = "codellama"
        config.ollama_timeout = 60
        config.temperature = 0.7
        config.max_tokens = 2000
        config.groq_api_key = None
        config.openai_api_key = None
        config.default_provider = "ollama"
        config.fallback_order = ["ollama"]
        config.auto_fallback = True
        return config
    
    def test_llm_manager_initialization(self, mock_config):
        with patch('agents.llm_manager.OllamaAdapter'):
            manager = LLMManager(mock_config)
            assert manager.current_provider is not None
            assert 'ollama' in manager.adapters
    
    def test_generate_calls_adapter(self, mock_config):
        with patch('agents.llm_manager.OllamaAdapter') as MockAdapter:
            mock_adapter = Mock()
            mock_adapter.generate.return_value = "test response"
            MockAdapter.return_value = mock_adapter
            
            manager = LLMManager(mock_config)
            manager.current_provider = 'ollama'
            manager.adapters['ollama'] = mock_adapter
            
            messages = [{"role": "user", "content": "test"}]
            response = manager.generate(messages)
            
            assert response == "test response"
            mock_adapter.generate.assert_called_once_with(messages)
