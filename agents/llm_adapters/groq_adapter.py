import time
from typing import Dict, List, Generator, Optional
from datetime import datetime, timedelta
from collections import deque

from agents.llm_adapters.base_adapter import BaseLLMAdapter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def can_proceed(self) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def add_request(self):
        self.requests.append(datetime.now())
    
    def time_until_available(self) -> float:
        if self.can_proceed():
            return 0.0
        
        if not self.requests:
            return 0.0
        
        oldest = self.requests[0]
        cutoff = oldest + timedelta(seconds=self.time_window)
        wait_time = (cutoff - datetime.now()).total_seconds()
        
        return max(0.0, wait_time)


class GroqAdapter(BaseLLMAdapter):
    
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-70b-versatile",
        timeout: int = 30,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        super().__init__("groq")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.rate_limiter = RateLimiter(max_requests=30, time_window=60)
        
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key, timeout=self.timeout)
                logger.info(f"Groq adapter inicializado con modelo {self.model}")
            except ImportError:
                logger.warning("Librería 'groq' no está instalada. Instala con: pip install groq")
            except Exception as e:
                logger.error(f"Error al inicializar Groq client: {e}")
    
    def is_available(self) -> bool:
        if not self.api_key:
            logger.debug("Groq: no API key configurada")
            return False
        
        if not self.client:
            logger.debug("Groq: client no inicializado")
            return False
        
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.debug(f"Groq no disponible: {e}")
            return False
    
    def _wait_for_rate_limit(self):
        wait_time = self.rate_limiter.time_until_available()
        if wait_time > 0:
            logger.warning(f"Rate limit alcanzado, esperando {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role in ["user", "assistant", "system"]:
                converted.append({"role": role, "content": content})
        
        return converted
    
    def generate(self, messages: List[Dict], **kwargs) -> str:
        if not self.is_available():
            raise RuntimeError("Groq adapter no está disponible")
        
        self._wait_for_rate_limit()
        
        start_time = time.time()
        
        try:
            converted_messages = self._convert_messages(messages)
            
            if not converted_messages:
                converted_messages = [{"role": "user", "content": str(messages)}]
            
            self.rate_limiter.add_request()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=converted_messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=False
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            response_time = time.time() - start_time
            self._update_stats(success=True, response_time=response_time, tokens=tokens_used)
            
            logger.debug(f"Groq response: {len(answer)} chars, {tokens_used} tokens, {response_time:.2f}s")
            
            return answer
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(success=False, response_time=response_time)
            
            logger.error(f"Error en Groq generate: {e}")
            raise RuntimeError(f"Groq error: {str(e)}")
    
    def stream_generate(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        if not self.is_available():
            raise RuntimeError("Groq adapter no está disponible")
        
        self._wait_for_rate_limit()
        
        try:
            converted_messages = self._convert_messages(messages)
            
            if not converted_messages:
                converted_messages = [{"role": "user", "content": str(messages)}]
            
            self.rate_limiter.add_request()
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=converted_messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            self._update_stats(success=True)
            
        except Exception as e:
            self._update_stats(success=False)
            logger.error(f"Error en Groq stream_generate: {e}")
            raise RuntimeError(f"Groq streaming error: {str(e)}")
