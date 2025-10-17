import time
from typing import Dict, List, Generator

from agents.llm_adapters.base_adapter import BaseLLMAdapter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: int = 30,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        super().__init__("openai")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)
                logger.info(f"OpenAI adapter inicializado con modelo {self.model}")
            except ImportError:
                logger.warning("Librería 'openai' no está instalada. Instala con: pip install openai")
            except Exception as e:
                logger.error(f"Error al inicializar OpenAI client: {e}")
    
    def is_available(self) -> bool:
        if not self.api_key:
            logger.debug("OpenAI: no API key configurada")
            return False
        
        if not self.client:
            logger.debug("OpenAI: client no inicializado")
            return False
        
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.debug(f"OpenAI no disponible: {e}")
            return False
    
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
            raise RuntimeError("OpenAI adapter no está disponible")
        
        start_time = time.time()
        
        try:
            converted_messages = self._convert_messages(messages)
            
            if not converted_messages:
                converted_messages = [{"role": "user", "content": str(messages)}]
            
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
            
            logger.debug(f"OpenAI response: {len(answer)} chars, {tokens_used} tokens, {response_time:.2f}s")
            
            return answer
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(success=False, response_time=response_time)
            
            logger.error(f"Error en OpenAI generate: {e}")
            raise RuntimeError(f"OpenAI error: {str(e)}")
    
    def stream_generate(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        if not self.is_available():
            raise RuntimeError("OpenAI adapter no está disponible")
        
        try:
            converted_messages = self._convert_messages(messages)
            
            if not converted_messages:
                converted_messages = [{"role": "user", "content": str(messages)}]
            
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
            logger.error(f"Error en OpenAI stream_generate: {e}")
            raise RuntimeError(f"OpenAI streaming error: {str(e)}")
