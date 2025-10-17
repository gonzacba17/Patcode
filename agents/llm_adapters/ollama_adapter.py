import time
import json
import requests
from typing import Dict, List, Generator

from agents.llm_adapters.base_adapter import BaseLLMAdapter
from exceptions import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    OllamaResponseError
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:1.5b",
        timeout: int = 30,
        temperature: float = 0.7,
        num_ctx: int = 4096,
        num_predict: int = 512,
        num_gpu: int = 1
    ):
        super().__init__("ollama")
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.num_gpu = num_gpu
        
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        
        logger.info(f"Ollama adapter inicializado: {self.base_url} | Modelo: {self.model}")
    
    def is_available(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code != 200:
                logger.debug(f"Ollama no disponible: status {response.status_code}")
                return False
            
            models_data = response.json()
            available_models = [m['name'] for m in models_data.get('models', [])]
            
            model_available = any(
                self.model in m or m.startswith(self.model.split(':')[0])
                for m in available_models
            )
            
            if not model_available:
                logger.debug(f"Modelo {self.model} no encontrado en Ollama")
                logger.debug(f"Modelos disponibles: {available_models}")
                return False
            
            return True
            
        except requests.exceptions.ConnectionError:
            logger.debug("No se pudo conectar a Ollama")
            return False
        except Exception as e:
            logger.debug(f"Error verificando disponibilidad de Ollama: {e}")
            return False
    
    def _build_prompt_from_messages(self, messages: List[Dict]) -> str:
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(content)
            elif role == "user":
                prompt_parts.append(f"Usuario: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Asistente: {content}")
        
        return "\n".join(prompt_parts)
    
    def generate(self, messages: List[Dict], **kwargs) -> str:
        if not self.is_available():
            raise OllamaConnectionError(
                f"Ollama no está disponible en {self.base_url}\n"
                "Verifica que esté corriendo: ollama serve"
            )
        
        start_time = time.time()
        
        try:
            if isinstance(messages, str):
                prompt = messages
            elif isinstance(messages, list):
                prompt = self._build_prompt_from_messages(messages)
            else:
                prompt = str(messages)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.temperature),
                    "num_ctx": kwargs.get('num_ctx', self.num_ctx),
                    "num_predict": kwargs.get('num_predict', self.num_predict),
                    "num_gpu": kwargs.get('num_gpu', self.num_gpu)
                }
            }
            
            logger.debug(f"Ollama request: {self.generate_url} | Modelo: {self.model}")
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                logger.error(f"Modelo '{self.model}' no encontrado")
                raise OllamaModelNotFoundError(
                    f"El modelo '{self.model}' no está disponible en Ollama.\n"
                    f"Descárgalo con: ollama pull {self.model}"
                )
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Respuesta JSON inválida: {e}")
                raise OllamaResponseError("La respuesta de Ollama no es JSON válido")
            
            answer = result.get("response", "")
            
            if not answer:
                logger.warning("Ollama devolvió respuesta vacía")
                answer = "Lo siento, no pude generar una respuesta. Intenta reformular tu pregunta."
            
            response_time = time.time() - start_time
            eval_count = result.get('eval_count', 0)
            
            self._update_stats(success=True, response_time=response_time, tokens=eval_count)
            
            logger.debug(f"Ollama response: {len(answer)} chars, {eval_count} tokens, {response_time:.2f}s")
            
            return answer
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            self._update_stats(success=False, response_time=response_time)
            
            logger.error(f"Timeout después de {self.timeout}s")
            raise OllamaTimeoutError(
                f"Ollama no respondió en {self.timeout} segundos.\n"
                f"Posibles soluciones:\n"
                f"- Aumenta el timeout en la configuración\n"
                f"- Verifica que Ollama no esté sobrecargado\n"
                f"- Prueba con un modelo más pequeño"
            )
            
        except requests.exceptions.ConnectionError as e:
            self._update_stats(success=False)
            logger.error(f"Error de conexión: {e}")
            raise OllamaConnectionError(
                f"No se pudo conectar con Ollama en {self.base_url}.\n"
                "Verifica que esté corriendo: ollama serve"
            )
            
        except (OllamaModelNotFoundError, OllamaResponseError):
            self._update_stats(success=False)
            raise
            
        except Exception as e:
            self._update_stats(success=False)
            logger.error(f"Error en Ollama generate: {e}")
            raise RuntimeError(f"Ollama error: {str(e)}")
    
    def stream_generate(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        if not self.is_available():
            raise OllamaConnectionError(
                f"Ollama no está disponible en {self.base_url}\n"
                "Verifica que esté corriendo: ollama serve"
            )
        
        try:
            if isinstance(messages, str):
                prompt = messages
            elif isinstance(messages, list):
                prompt = self._build_prompt_from_messages(messages)
            else:
                prompt = str(messages)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get('temperature', self.temperature),
                    "num_ctx": kwargs.get('num_ctx', self.num_ctx),
                    "num_predict": kwargs.get('num_predict', self.num_predict),
                    "num_gpu": kwargs.get('num_gpu', self.num_gpu)
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            yield chunk['response']
                    except json.JSONDecodeError:
                        continue
            
            self._update_stats(success=True)
            
        except Exception as e:
            self._update_stats(success=False)
            logger.error(f"Error en Ollama stream_generate: {e}")
            raise RuntimeError(f"Ollama streaming error: {str(e)}")
