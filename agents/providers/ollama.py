"""Provider de Ollama para LLM"""

import requests
import json
from typing import Generator, Dict, Any, Optional
from .base import LLMProvider, GenerationConfig
from utils.exceptions import (
    OllamaConnectionError,
    OllamaTimeoutError,
    ModelNotFoundError
)
from utils.logger import logger
from config.settings import settings

class OllamaProvider(LLMProvider):
    """Implementación del provider para Ollama"""
    
    def __init__(
        self, 
        model_name: str = None,
        host: str = None,
        timeout: int = None
    ):
        super().__init__(model_name or settings.OLLAMA_MODEL)
        self.host = host or settings.OLLAMA_HOST
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        logger.info(f"OllamaProvider inicializado: {self.model_name} @ {self.host}")
    
    def generate(
        self, 
        prompt: str, 
        config: Optional[GenerationConfig] = None
    ) -> str  < /dev/null |  Generator[str, None, None]:
        """Genera respuesta usando Ollama"""
        config = config or GenerationConfig()
        
        if config.stream:
            return self._stream_generate(prompt, config)
        else:
            return self._blocking_generate(prompt, config)
    
    def _blocking_generate(self, prompt: str, config: GenerationConfig) -> str:
        """Generación bloqueante (espera respuesta completa)"""
        payload = self._build_payload(prompt, config, stream=False)
        
        try:
            logger.debug(f"Enviando request a Ollama: {len(prompt)} chars")
            
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            self._handle_response_errors(response)
            
            data = response.json()
            result = data.get("response", "")
            
            logger.debug(f"Respuesta recibida: {len(result)} chars")
            return result
            
        except requests.Timeout:
            raise OllamaTimeoutError(
                f"Ollama no respondió en {self.timeout}s",
                details="El modelo puede estar procesando una solicitud compleja"
            )
        
        except requests.ConnectionError:
            raise OllamaConnectionError(
                "No se puede conectar a Ollama",
                details=f"Verifica que Ollama esté corriendo en {self.host}"
            )
        
        except requests.RequestException as e:
            raise OllamaConnectionError(
                "Error al comunicarse con Ollama",
                details=str(e)
            )
    
    def _stream_generate(
        self, 
        prompt: str, 
        config: GenerationConfig
    ) -> Generator[str, None, None]:
        """Generación en streaming (chunks progresivos)"""
        payload = self._build_payload(prompt, config, stream=True)
        
        try:
            logger.debug(f"Iniciando stream con Ollama: {len(prompt)} chars")
            
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            
            self._handle_response_errors(response)
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        
                        if chunk.get("done", False):
                            logger.debug("Stream completado")
                            break
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Línea inválida en stream: {line}")
                        continue
        
        except requests.RequestException as e:
            raise OllamaConnectionError(
                "Error en streaming con Ollama",
                details=str(e)
            )
    
    def _build_payload(
        self, 
        prompt: str, 
        config: GenerationConfig,
        stream: bool
    ) -> Dict[str, Any]:
        """Construye el payload para la API de Ollama"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
        }
        
        options = {}
        if config.temperature is not None:
            options["temperature"] = config.temperature
        if config.top_p is not None:
            options["top_p"] = config.top_p
        if config.max_tokens is not None:
            options["num_predict"] = config.max_tokens
        
        if options:
            payload["options"] = options
        
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences
        
        return payload
    
    def _handle_response_errors(self, response: requests.Response):
        """Maneja errores HTTP de Ollama"""
        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Modelo '{self.model_name}' no encontrado",
                details=f"Ejecuta: ollama pull {self.model_name}"
            )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", "Error desconocido")
            except:
                error_msg = response.text
            
            raise OllamaConnectionError(
                f"Error HTTP {response.status_code}",
                details=error_msg
            )
    
    def check_health(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list[str]:
        """Lista modelos disponibles en Ollama"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise OllamaConnectionError(
                "No se pudo obtener lista de modelos",
                details=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo actual"""
        try:
            response = requests.post(
                f"{self.host}/api/show",
                json={"name": self.model_name},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"No se pudo obtener info del modelo: {e}")
            return {"name": self.model_name, "error": str(e)}
