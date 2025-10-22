import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from agents.llm_adapters.base_adapter import BaseLLMAdapter, LLMStats
from agents.llm_adapters.ollama_adapter import OllamaAdapter
from agents.llm_adapters.groq_adapter import GroqAdapter, RateLimiter
from agents.llm_adapters.openai_adapter import OpenAIAdapter
from agents.llm_manager import LLMManager
from config.settings import LLMSettings


class TestBaseLLMAdapter:
    
    def test_stats_initialization(self):
        stats = LLMStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
    
    def test_stats_to_dict(self):
        stats = LLMStats(total_requests=10, successful_requests=8, failed_requests=2)
        stats_dict = stats.to_dict()
        
        assert stats_dict['total_requests'] == 10
        assert stats_dict['successful_requests'] == 8
        assert stats_dict['failed_requests'] == 2
        assert stats_dict['success_rate'] == 0.8


class TestRateLimiter:
    
    def test_initial_can_proceed(self):
        limiter = RateLimiter(max_requests=5, time_window=60)
        assert limiter.can_proceed() is True
    
    def test_rate_limit_reached(self):
        limiter = RateLimiter(max_requests=2, time_window=60)
        
        limiter.add_request()
        assert limiter.can_proceed() is True
        
        limiter.add_request()
        assert limiter.can_proceed() is False
    
    def test_time_until_available(self):
        limiter = RateLimiter(max_requests=1, time_window=60)
        limiter.add_request()
        
        wait_time = limiter.time_until_available()
        assert wait_time > 0
        assert wait_time <= 60


class TestOllamaAdapter:
    
    def test_initialization(self):
        adapter = OllamaAdapter(
            base_url="http://localhost:11434",
            model="qwen2.5-coder:1.5b"
        )
        
        assert adapter.name == "ollama"
        assert adapter.model == "qwen2.5-coder:1.5b"
        assert adapter.base_url == "http://localhost:11434"
    
    @patch('requests.get')
    def test_is_available_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'qwen2.5-coder:1.5b'}
            ]
        }
        mock_get.return_value = mock_response
        
        adapter = OllamaAdapter(model="qwen2.5-coder:1.5b")
        assert adapter.is_available() is True
    
    @patch('requests.get')
    def test_is_available_connection_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        adapter = OllamaAdapter()
        assert adapter.is_available() is False
    
    @patch('requests.post')
    def test_generate_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Test response',
            'eval_count': 100
        }
        mock_post.return_value = mock_response
        
        adapter = OllamaAdapter()
        
        with patch.object(adapter, 'is_available', return_value=True):
            messages = [{"role": "user", "content": "Hello"}]
            response = adapter.generate(messages)
            
            assert response == 'Test response'
            assert adapter.stats.total_requests == 1
            assert adapter.stats.successful_requests == 1


class TestGroqAdapter:
    
    def test_initialization_without_key(self):
        adapter = GroqAdapter(api_key="")
        assert adapter.name == "groq"
        assert adapter.client is None
    
    def test_is_available_without_key(self):
        adapter = GroqAdapter(api_key="")
        assert adapter.is_available() is False
    
    def test_initialization_with_key(self):
        import sys
        from unittest.mock import MagicMock
        
        mock_groq_module = MagicMock()
        mock_client = Mock()
        mock_groq_module.Groq = Mock(return_value=mock_client)
        
        with patch.dict('sys.modules', {'groq': mock_groq_module}):
            adapter = GroqAdapter(api_key="test-key-123")
            
            assert adapter.api_key == "test-key-123"
            assert adapter.client is not None


class TestOpenAIAdapter:
    
    def test_initialization_without_key(self):
        adapter = OpenAIAdapter(api_key="")
        assert adapter.name == "openai"
        assert adapter.client is None
    
    def test_is_available_without_key(self):
        adapter = OpenAIAdapter(api_key="")
        assert adapter.is_available() is False


class TestLLMManager:
    
    def test_initialization(self):
        config = LLMSettings(
            default_provider="ollama",
            groq_api_key="",
            openai_api_key=""
        )
        
        manager = LLMManager(config)
        
        assert 'ollama' in manager.adapters
        assert manager.current_provider is not None
    
    def test_get_available_providers(self):
        config = LLMSettings(
            default_provider="ollama",
            groq_api_key="",
            openai_api_key=""
        )
        
        manager = LLMManager(config)
        
        with patch.object(manager.adapters['ollama'], 'is_available', return_value=True):
            available = manager.get_available_providers()
            assert 'ollama' in available
    
    def test_switch_provider_success(self):
        config = LLMSettings(
            default_provider="ollama",
            groq_api_key="test-key"
        )
        
        manager = LLMManager(config)
        
        with patch.object(manager.adapters['groq'], 'is_available', return_value=True):
            success = manager.switch_provider('groq')
            assert success is True
            assert manager.current_provider == 'groq'
    
    def test_switch_provider_not_available(self):
        config = LLMSettings(
            default_provider="ollama",
            groq_api_key=""
        )
        
        manager = LLMManager(config)
        success = manager.switch_provider('groq')
        
        assert success is False
    
    def test_fallback_on_error(self):
        config = LLMSettings(
            default_provider="groq",
            auto_fallback=True,
            fallback_order=["groq", "ollama"],
            groq_api_key="test-key"
        )
        
        manager = LLMManager(config)
        
        with patch.object(manager.adapters['groq'], 'generate', side_effect=Exception("Groq error")):
            with patch.object(manager.adapters['ollama'], 'is_available', return_value=True):
                with patch.object(manager.adapters['ollama'], 'generate', return_value="Fallback response"):
                    messages = [{"role": "user", "content": "Test"}]
                    response = manager.generate(messages)
                    
                    assert response == "Fallback response"
                    assert manager.current_provider == "ollama"
    
    def test_get_stats(self):
        config = LLMSettings(default_provider="ollama")
        manager = LLMManager(config)
        
        stats = manager.get_stats()
        
        assert 'current_provider' in stats
        assert 'available_providers' in stats
        assert 'provider_stats' in stats
        assert 'auto_fallback' in stats
    
    def test_test_provider(self):
        config = LLMSettings(default_provider="ollama")
        manager = LLMManager(config)
        
        with patch.object(manager.adapters['ollama'], 'is_available', return_value=True):
            with patch.object(manager.adapters['ollama'], 'generate', return_value="Test response"):
                result = manager.test_provider('ollama')
                
                assert result['provider'] == 'ollama'
                assert result['available'] is True
                assert 'test_success' in result


class TestLLMManagerIntegration:
    
    def test_no_fallback_when_disabled(self):
        config = LLMSettings(
            default_provider="groq",
            auto_fallback=False,
            groq_api_key="test-key"
        )
        
        manager = LLMManager(config)
        
        with patch.object(manager.adapters['groq'], 'generate', side_effect=Exception("Error")):
            with pytest.raises(RuntimeError):
                messages = [{"role": "user", "content": "Test"}]
                manager.generate(messages)
    
    def test_all_providers_fail(self):
        config = LLMSettings(
            default_provider="groq",
            auto_fallback=True,
            fallback_order=["groq", "ollama"],
            groq_api_key="test-key"
        )
        
        manager = LLMManager(config)
        
        with patch.object(manager.adapters['groq'], 'generate', side_effect=Exception("Groq error")):
            with patch.object(manager.adapters['ollama'], 'is_available', return_value=False):
                with pytest.raises(RuntimeError) as exc_info:
                    messages = [{"role": "user", "content": "Test"}]
                    manager.generate(messages)
                
                assert "No hay providers de fallback disponibles" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
