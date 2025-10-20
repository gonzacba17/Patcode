import pytest
from exceptions import (
    PatCodeError,
    OllamaError, OllamaConnectionError, OllamaTimeoutError,
    OllamaModelNotFoundError, OllamaResponseError,
    ValidationError, InvalidPromptError, InvalidConfigurationError,
    PatCodeMemoryError, MemoryReadError, MemoryWriteError, MemoryCorruptedError,
    ConfigurationError,
    LLMError, LLMProviderError, LLMTimeoutError, LLMRateLimitError
)


class TestExceptionHierarchy:
    
    def test_base_exception(self):
        err = PatCodeError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"
    
    def test_ollama_errors_inherit_from_ollama_error(self):
        assert issubclass(OllamaConnectionError, OllamaError)
        assert issubclass(OllamaTimeoutError, OllamaError)
        assert issubclass(OllamaModelNotFoundError, OllamaError)
        assert issubclass(OllamaResponseError, OllamaError)
    
    def test_ollama_error_inherits_from_base(self):
        assert issubclass(OllamaError, PatCodeError)
    
    def test_validation_errors_inherit_correctly(self):
        assert issubclass(InvalidPromptError, ValidationError)
        assert issubclass(InvalidConfigurationError, ValidationError)
        assert issubclass(ValidationError, PatCodeError)
    
    def test_memory_errors_inherit_from_patcode_memory_error(self):
        assert issubclass(MemoryReadError, PatCodeMemoryError)
        assert issubclass(MemoryWriteError, PatCodeMemoryError)
        assert issubclass(MemoryCorruptedError, PatCodeMemoryError)
        assert issubclass(PatCodeMemoryError, PatCodeError)
    
    def test_llm_errors_inherit_correctly(self):
        assert issubclass(LLMProviderError, LLMError)
        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMError, PatCodeError)
    
    def test_catch_specific_exception(self):
        try:
            raise OllamaConnectionError("Cannot connect")
        except OllamaError as e:
            assert "Cannot connect" in str(e)
    
    def test_catch_base_exception(self):
        try:
            raise LLMRateLimitError("Rate limit exceeded")
        except PatCodeError as e:
            assert "Rate limit" in str(e)
