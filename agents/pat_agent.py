"""
PatAgent - Agente de programación asistido por LLM.

Este módulo implementa el agente principal que maneja la lógica
de conversación, persistencia y comunicación con Ollama.
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
import logging

from config import settings
from exceptions import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    OllamaResponseError,
    MemoryReadError,
    MemoryWriteError,
    MemoryCorruptedError,
    InvalidPromptError,
    PatCodeError
)
from utils.validators import InputValidator, MemoryValidator
from utils.file_manager import FileManager
from agents.memory.memory_manager import MemoryManager, MemoryConfig

# Configurar logger
logger = logging.getLogger(__name__)


class PatAgent:
    """
    Agente de programación asistido por LLM.
    
    Este agente maneja conversaciones con el usuario, mantiene
    un historial persistente, gestiona archivos del proyecto
    y se comunica con Ollama para generar respuestas inteligentes.
    
    Attributes:
        history: Lista de mensajes de la conversación
        memory_path: Ruta al archivo de memoria persistente
        ollama_url: URL completa del endpoint de Ollama
        model: Nombre del modelo LLM a usar
        timeout: Timeout para requests a Ollama en segundos
        file_manager: Gestor de archivos del proyecto
    """
    
    def __init__(self):
        """
        Inicializa el agente PatCode.
        
        Raises:
            MemoryReadError: Si hay problemas al cargar el historial
            ConfigurationError: Si la configuración es inválida
        """
        self.memory_path: Path = settings.memory.path
        self.ollama_url: str = f"{settings.ollama.base_url}/api/generate"
        self.model: str = settings.ollama.model
        self.timeout: int = settings.ollama.timeout
        
        # Inicializar FileManager
        self.file_manager = FileManager()
        
        # Configurar MemoryManager
        memory_config = MemoryConfig(
            max_active_messages=settings.memory.max_active_messages,
            max_file_size_bytes=settings.memory.max_file_size_bytes,
            archive_dir=settings.memory.archive_directory if settings.memory.enable_summarization else None,
            ollama_url=self.ollama_url,
            summarize_model=self.model
        )
        self.memory_manager = MemoryManager(memory_config)
        
        # Crear directorio de memoria si no existe
        try:
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directorio de memoria asegurado: {self.memory_path.parent}")
        except Exception as e:
            logger.error(f"Error al crear directorio de memoria: {e}")
            raise PatCodeError(f"No se pudo crear directorio de memoria: {e}")
        
        # Cargar historial usando MemoryManager
        self.memory_manager.load_from_file(self.memory_path)
        
        # Mantener referencia a history para compatibilidad
        self.history = self.memory_manager.active_memory
        
        # Auto-cargar README si existe
        self._auto_load_readme()
        
        logger.info(
            f"PatAgent inicializado | "
            f"Modelo: {self.model} | "
            f"Mensajes activos: {len(self.memory_manager.active_memory)} | "
            f"Archivos en contexto: {len(self.file_manager.loaded_files)}"
        )
    
    def _auto_load_readme(self) -> None:
        """Intenta cargar automáticamente el README del proyecto."""
        readme_names = ['README.md', 'README.txt', 'README', 'readme.md']
        
        for readme_name in readme_names:
            readme_path = Path.cwd() / readme_name
            if readme_path.exists():
                try:
                    self.file_manager.load_file(str(readme_path))
                    logger.info(f"README cargado automáticamente: {readme_name}")
                    break
                except Exception as e:
                    logger.debug(f"No se pudo cargar {readme_name}: {e}")
    
    def _load_history(self) -> None:
        pass
    
    def _save_history(self) -> None:
        """
        Guarda el historial usando MemoryManager.
        
        Raises:
            MemoryWriteError: Si hay errores al escribir
        """
        try:
            self.memory_manager.save_to_file(self.memory_path)
        except Exception as e:
            logger.error(f"Error al guardar historial: {e}")
            raise MemoryWriteError(f"No se pudo guardar la memoria: {e}")
    
    def _build_context(self) -> str:
        """
        Construye el contexto para el LLM basado en el historial reciente y archivos cargados.
        
        Usa solo los últimos N mensajes según CONTEXT_WINDOW_SIZE
        para no sobrecargar el contexto del modelo.
        
        Returns:
            String con el contexto formateado para el LLM
        """
        full_context = self.memory_manager.get_full_context()
        
        # System prompt base
        context = (
            "Eres Pat, un asistente de programación experto y amigable.\n"
            "Ayudas a los desarrolladores con:\n"
            "- Explicaciones claras de conceptos\n"
            "- Ejemplos de código prácticos\n"
            "- Debugging y resolución de problemas\n"
            "- Mejores prácticas y patrones\n"
            "- Análisis y revisión de código\n\n"
        )
        
        # Agregar información de archivos cargados si existen
        if self.file_manager.loaded_files:
            context += "ARCHIVOS DEL PROYECTO DISPONIBLES:\n"
            for file_path, loaded_file in self.file_manager.loaded_files.items():
                lines = len(loaded_file.content.splitlines())
                context += f"- {loaded_file.path.name} ({lines} líneas)\n"
            context += "\nPuedes analizar estos archivos cuando el usuario lo pida.\n\n"
        
        # Agregar contexto completo (pasivo + activo)
        if full_context:
            context += "Conversación reciente:\n"
            for msg in full_context:
                role_display = "Usuario" if msg["role"] == "user" else "Pat"
                if msg["role"] == "system":
                    context += f"{msg['content']}\n"
                else:
                    context += f"{role_display}: {msg['content']}\n"
            context += "\n"
        
        return context
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Realiza una llamada al servidor Ollama para generar una respuesta.
        
        Args:
            prompt: Prompt completo a enviar a Ollama (incluye contexto)
            
        Returns:
            Respuesta generada por el modelo
            
        Raises:
            OllamaConnectionError: Si no se puede conectar con Ollama
            OllamaTimeoutError: Si la respuesta tarda más del timeout
            OllamaModelNotFoundError: Si el modelo no está disponible
            OllamaResponseError: Si la respuesta es inválida
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            logger.debug(f"Enviando request a Ollama: {self.ollama_url}")
            logger.debug(f"Modelo: {self.model}, Timeout: {self.timeout}s")
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=self.timeout
            )
            
            # Manejar códigos de error específicos
            if response.status_code == 404:
                logger.error(f"Modelo '{self.model}' no encontrado")
                raise OllamaModelNotFoundError(
                    f"El modelo '{self.model}' no está disponible en Ollama.\n"
                    f"Descárgalo con: ollama pull {self.model}"
                )
            
            # Verificar otros errores HTTP
            response.raise_for_status()
            
            # Parsear respuesta
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Respuesta JSON inválida: {e}")
                raise OllamaResponseError("La respuesta de Ollama no es JSON válido")
            
            # Extraer texto de respuesta
            answer = result.get("response", "")
            
            if not answer:
                logger.warning("Ollama devolvió respuesta vacía")
                return "Lo siento, no pude generar una respuesta. Intenta reformular tu pregunta."
            
            logger.debug(f"Respuesta recibida: {len(answer)} caracteres")
            return answer
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout después de {self.timeout}s")
            raise OllamaTimeoutError(
                f"Ollama no respondió en {self.timeout} segundos.\n"
                f"Posibles soluciones:\n"
                f"- Aumenta REQUEST_TIMEOUT en .env\n"
                f"- Verifica que Ollama no esté sobrecargado\n"
                f"- Prueba con un modelo más pequeño"
            )
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión: {e}")
            raise OllamaConnectionError(
                "No se pudo conectar con Ollama.\n"
                "Verifica que esté corriendo: ollama serve"
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en request HTTP: {e}")
            raise OllamaConnectionError(f"Error al comunicarse con Ollama: {e}")
    
    def ask(self, prompt: str) -> str:
        """
        Procesa una pregunta del usuario y devuelve la respuesta del asistente.
        
        Este método:
        1. Valida el prompt
        2. Lo agrega al historial
        3. Construye el contexto (incluyendo archivos)
        4. Llama a Ollama
        5. Guarda la respuesta
        6. Persiste el historial
        
        Args:
            prompt: Pregunta o comando del usuario
            
        Returns:
            Respuesta generada por el asistente
            
        Raises:
            InvalidPromptError: Si el prompt no es válido
            OllamaConnectionError: Si hay problemas con Ollama
            OllamaTimeoutError: Si Ollama no responde a tiempo
            MemoryWriteError: Si no se puede guardar el historial
        """
        # 1. Validar input
        try:
            validated_prompt = InputValidator.validate_prompt(prompt)
        except InvalidPromptError as e:
            logger.warning(f"Prompt inválido rechazado: {e}")
            raise
        
        # 2. Agregar pregunta al historial usando MemoryManager
        self.memory_manager.add_message("user", validated_prompt)
        logger.debug(f"Pregunta agregada al historial: '{validated_prompt[:50]}...'")
        
        try:
            # 3. Construir contexto (ahora incluye archivos)
            context = self._build_context()
            
            # Si hay archivos cargados Y el usuario pregunta sobre código específico,
            # agregar el contenido del archivo relevante
            files_content = ""
            if self.file_manager.loaded_files:
                # Detectar si el usuario menciona un archivo específico
                prompt_lower = validated_prompt.lower()
                for file_path, loaded_file in self.file_manager.loaded_files.items():
                    file_name_lower = loaded_file.path.name.lower()
                    # Si menciona el archivo o pide analizar/revisar código
                    if (file_name_lower in prompt_lower or 
                        any(word in prompt_lower for word in ['analiza', 'analizar', 'revisa', 'revisar', 'código', 'codigo', 'archivo', 'main', 'config'])):
                        # Solo agregar archivos mencionados o relevantes
                        if file_name_lower in prompt_lower or 'main.py' in file_name_lower:
                            files_content += f"\n=== Contenido de {loaded_file.path.name} ===\n"
                            files_content += loaded_file.content[:5000]  # Limitar a 5000 caracteres
                            if len(loaded_file.content) > 5000:
                                files_content += "\n... (archivo truncado por tamaño)"
                            files_content += "\n\n"
                            break  # Solo un archivo por consulta
            
            full_prompt = f"{context}\n{files_content}\nUsuario: {validated_prompt}\nPat:"
            
            # 4. Llamar a Ollama
            answer = self._call_ollama(full_prompt)
            
            # 5. Agregar respuesta al historial usando MemoryManager
            self.memory_manager.add_message("assistant", answer)
            logger.debug(f"Respuesta agregada al historial: '{answer[:50]}...'")
            
            # 6. Guardar memoria
            self._save_history()
            
            return answer
            
        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError) as e:
            # Si falla, revertir el último mensaje del usuario
            if self.memory_manager.active_memory:
                self.memory_manager.active_memory.pop()
            logger.error(f"Error al procesar pregunta, historial revertido: {e}")
            raise
            
        except Exception as e:
            # Error inesperado
            if self.memory_manager.active_memory:
                self.memory_manager.active_memory.pop()
            logger.exception("Error inesperado al procesar pregunta")
            raise PatCodeError(f"Error inesperado: {e}")
    
    def clear_history(self) -> None:
        """
        Limpia completamente el historial de conversación.
        
        Raises:
            MemoryWriteError: Si no se puede guardar el historial vacío
        """
        logger.info("Limpiando historial...")
        self.memory_manager.clear_all()
        self._save_history()
        logger.info("Historial limpiado exitosamente")
    
    def get_stats(self) -> Dict[str, any]:
        """
        Obtiene estadísticas sobre el estado actual del agente.
        
        Returns:
            Diccionario con estadísticas
        """
        file_stats = self.file_manager.get_stats()
        memory_stats = self.memory_manager.get_stats()
        
        return {
            "total_messages": memory_stats['total_context'],
            "active_messages": memory_stats['active_messages'],
            "passive_summaries": memory_stats['passive_summaries'],
            "user_messages": sum(1 for msg in self.memory_manager.active_memory if msg["role"] == "user"),
            "assistant_messages": sum(1 for msg in self.memory_manager.active_memory if msg["role"] == "assistant"),
            "model": self.model,
            "memory_path": str(self.memory_path),
            "loaded_files": file_stats['total_files'],
            "files_size_kb": file_stats['total_size_kb'],
            "files_usage_percent": file_stats['usage_percent']
        }
    
    def export_history(self, output_path: Path) -> None:
        """
        Exporta el historial a un archivo específico.
        
        Args:
            output_path: Ruta donde exportar el historial
            
        Raises:
            MemoryWriteError: Si no se puede escribir el archivo
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory_manager.get_full_context(), f, indent=2, ensure_ascii=False)
            logger.info(f"Historial exportado a: {output_path}")
        except Exception as e:
            logger.error(f"Error al exportar historial: {e}")
            raise MemoryWriteError(f"No se pudo exportar el historial: {e}")