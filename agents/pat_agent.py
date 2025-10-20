"""
PatAgent - Agente de programación asistido por LLM.

Este módulo implementa el agente principal que maneja la lógica
de conversación, persistencia y comunicación con Ollama.
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional

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
from utils.response_cache import ResponseCache
from utils.logger import setup_logger
from utils.retry import retry_with_backoff
from config.model_selector import get_model_selector
from agents.memory.memory_manager import MemoryManager, MemoryConfig
from rag.embeddings import EmbeddingGenerator
from rag.vector_store import VectorStore
from rag.code_indexer import CodeIndexer
from rag.retriever import ContextRetriever
from agents.llm_manager import LLMManager

logger = setup_logger(__name__)


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
    
    def __init__(
        self,
        llm_manager: Optional[LLMManager] = None,
        file_manager: Optional[FileManager] = None,
        cache: Optional[ResponseCache] = None,
        model_selector = None
    ):
        """
        Inicializa el agente PatCode con Dependency Injection.
        
        Args:
            llm_manager: Gestor de LLMs (opcional, se crea por defecto)
            file_manager: Gestor de archivos (opcional, se crea por defecto)
            cache: Sistema de caché (opcional, se crea por defecto)
            model_selector: Selector de modelos (opcional, se crea por defecto)
        
        Raises:
            MemoryReadError: Si hay problemas al cargar el historial
            ConfigurationError: Si la configuración es inválida
        """
        self.memory_path: Path = settings.memory.path
        self.ollama_url: str = f"{settings.ollama.base_url}/api/generate"
        self.model: str = settings.ollama.model
        self.timeout: int = settings.ollama.timeout
        
        self.llm_manager = llm_manager or LLMManager(settings.llm)
        self.file_manager = file_manager or FileManager()
        self.cache = cache or ResponseCache(cache_dir='.patcode_cache', ttl_hours=24)
        self.model_selector = model_selector or get_model_selector()
        
        # Log info del modelo
        model_info = self.model_selector.get_model_info(self.model)
        if model_info:
            logger.info(f"Usando modelo: {model_info}")
        
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
        
        # Sistema RAG
        try:
            self.embedding_gen = EmbeddingGenerator()
            self.vector_store = VectorStore()
            self.code_indexer = CodeIndexer(self.vector_store, self.embedding_gen)
            self.retriever = ContextRetriever(self.vector_store, self.embedding_gen)
            logger.info("Sistema RAG inicializado")
        except Exception as e:
            logger.warning(f"No se pudo inicializar sistema RAG: {e}")
            self.embedding_gen = None
            self.vector_store = None
            self.code_indexer = None
            self.retriever = None
        
        # Auto-cargar README si existe
        self._auto_load_readme()
        
        logger.info(
            f"PatAgent inicializado | "
            f"LLM Provider: {self.llm_manager.get_current_provider()} | "
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
    
    def _build_context(self, max_tokens: int = 4000) -> str:
        """
        Construye el contexto para el LLM con límite de tokens.
        
        Prioridad: system prompt > archivos > RAG > memoria conversacional
        Usa conteo aproximado: 1 token ≈ 4 caracteres
        
        Args:
            max_tokens: Límite máximo de tokens (default: 4000)
        
        Returns:
            String con el contexto formateado y acotado
        """
        parts = []
        total_chars = 0
        max_chars = max_tokens * 4
        
        system_prompt = (
            "Eres Pat, un asistente de programación experto y amigable.\n"
            "Ayudas a los desarrolladores con:\n"
            "- Explicaciones claras de conceptos\n"
            "- Ejemplos de código prácticos\n"
            "- Debugging y resolución de problemas\n"
            "- Mejores prácticas y patrones\n"
            "- Análisis y revisión de código\n\n"
        )
        parts.append(system_prompt)
        total_chars += len(system_prompt)
        
        if self.file_manager.loaded_files and total_chars < max_chars:
            files_context = "ARCHIVOS DEL PROYECTO DISPONIBLES:\n"
            for file_path, loaded_file in self.file_manager.loaded_files.items():
                lines = len(loaded_file.content.splitlines())
                file_info = f"- {loaded_file.path.name} ({lines} líneas)\n"
                
                if total_chars + len(file_info) < max_chars:
                    files_context += file_info
                    total_chars += len(file_info)
                else:
                    break
            
            files_context += "\nPuedes analizar estos archivos cuando el usuario lo pida.\n\n"
            parts.append(files_context)
            total_chars += len(files_context)
        
        full_context = self.memory_manager.get_full_context()
        if full_context and total_chars < max_chars:
            conv_context = "Conversación reciente:\n"
            for msg in reversed(full_context):
                role_display = "Usuario" if msg["role"] == "user" else "Pat"
                if msg["role"] == "system":
                    msg_text = f"{msg['content']}\n"
                else:
                    msg_text = f"{role_display}: {msg['content']}\n"
                
                if total_chars + len(msg_text) < max_chars:
                    conv_context = msg_text + conv_context
                    total_chars += len(msg_text)
                else:
                    conv_context = "[... conversación truncada ...]\n" + conv_context
                    break
            
            parts.append(conv_context)
        
        final_context = "".join(parts)
        
        if len(final_context) > max_chars:
            logger.warning(f"Contexto truncado: {len(final_context)} chars > {max_chars} límite")
            final_context = final_context[:max_chars] + "\n[... contexto truncado por límite de tokens ...]"
        
        logger.debug(f"Contexto construido: ~{len(final_context) // 4} tokens estimados")
        return final_context
    
    def _get_response(self, messages: List[Dict]) -> str:
        return self.llm_manager.generate(messages)
    
    @retry_with_backoff(
        max_attempts=3,
        initial_delay=1.0,
        exceptions=(requests.exceptions.RequestException, TimeoutError)
    )
    def _call_ollama(self, prompt: str) -> str:
        """
        Realiza una llamada al servidor Ollama para generar una respuesta con cache.
        
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
        query_hash = self.cache._hash_query(
            self.memory_manager.active_memory,
            list(self.file_manager.loaded_files.values())
        )
        
        if self.model_selector.should_use_cache(self.model):
            cached_response = self.cache.get(query_hash)
            
            if cached_response:
                logger.info("💾 Usando respuesta cacheada")
                return cached_response
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.ollama.temperature
            }
        }
        
        try:
            logger.debug(f"Enviando request a Ollama: {self.ollama_url}")
            logger.debug(f"Modelo: {self.model}, Timeout: {self.timeout}s")
            
            response = requests.post(
                self.ollama_url,
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
                return "Lo siento, no pude generar una respuesta. Intenta reformular tu pregunta."
            
            self.cache.set(
                query_hash,
                answer,
                metadata={
                    'model': self.model,
                    'timestamp': result.get('created_at'),
                    'eval_count': result.get('eval_count')
                }
            )
            
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
    
    def process_command(self, user_input: str) -> Optional[str]:
        if user_input == '!index':
            if not self.code_indexer:
                return "Sistema RAG no disponible"
            stats = self.code_indexer.index_project()
            return f"✅ Proyecto indexado:\n" \
                   f"  - Archivos procesados: {stats['files_processed']}\n" \
                   f"  - Chunks creados: {stats['chunks_indexed']}\n" \
                   f"  - Archivos omitidos: {stats['files_skipped']}"
        
        elif user_input.startswith('!index '):
            if not self.code_indexer:
                return "Sistema RAG no disponible"
            filepath = Path(user_input[7:].strip())
            chunks = self.code_indexer.index_file(filepath)
            return f"✅ {filepath} indexado ({chunks} chunks)"
        
        elif user_input.startswith('!search '):
            if not self.embedding_gen or not self.vector_store:
                return "Sistema RAG no disponible"
            query = user_input[8:].strip()
            query_emb = self.embedding_gen.generate_embedding(query)
            results = self.vector_store.search(query_emb, top_k=5)
            
            if not results:
                return "No se encontraron resultados"
            
            output = ["🔍 Resultados de búsqueda:\n"]
            for i, r in enumerate(results, 1):
                output.append(
                    f"{i}. {r['filepath']} (L{r['start_line']}-{r['end_line']}) "
                    f"- Similitud: {r['similarity']:.2f}"
                )
            return '\n'.join(output)
        
        elif user_input.startswith('!related '):
            if not self.retriever:
                return "Sistema RAG no disponible"
            filepath = user_input[9:].strip()
            related = self.retriever.retrieve_related_code(filepath, top_k=5)
            
            if not related:
                return "No se encontró código relacionado"
            
            output = [f"🔗 Código relacionado a {filepath}:\n"]
            for i, r in enumerate(related, 1):
                output.append(
                    f"{i}. {r['filepath']} (L{r['start_line']}-{r['end_line']}) "
                    f"- Similitud: {r['similarity']:.2f}"
                )
            return '\n'.join(output)
        
        elif user_input == '!rag-stats':
            if not self.vector_store:
                return "Sistema RAG no disponible"
            stats = self.vector_store.get_stats()
            return f"📊 Estadísticas RAG:\n" \
                   f"  - Documentos: {stats['total_documents']}\n" \
                   f"  - Archivos: {stats['total_files']}\n" \
                   f"  - Por tipo: {stats['by_chunk_type']}"
        
        elif user_input == '!clear-index':
            if not self.vector_store or not self.embedding_gen:
                return "Sistema RAG no disponible"
            self.vector_store.clear()
            self.embedding_gen.clear_cache()
            return "✅ Índice RAG limpiado"
        
        return None
    
    def _validate_prompt(self, prompt: str) -> str:
        """
        Valida el prompt del usuario.
        
        Args:
            prompt: Prompt a validar
            
        Returns:
            Prompt validado
            
        Raises:
            InvalidPromptError: Si el prompt no es válido
        """
        try:
            validated_prompt = InputValidator.validate_prompt(prompt)
            logger.debug(f"Prompt validado: '{validated_prompt[:50]}...'")
            return validated_prompt
        except InvalidPromptError as e:
            logger.warning(f"Prompt inválido rechazado: {e}")
            raise
    
    def _get_rag_context(self, prompt: str) -> str:
        """
        Recupera contexto del sistema RAG.
        
        Args:
            prompt: Prompt del usuario
            
        Returns:
            Contexto RAG o cadena vacía
        """
        if not self.retriever:
            return ""
        
        try:
            rag_context = self.retriever.retrieve_context(prompt, top_k=3)
            logger.debug(f"Contexto RAG recuperado: {len(rag_context)} chars")
            return rag_context
        except Exception as e:
            logger.warning(f"Error recuperando contexto RAG: {e}")
            return ""
    
    def _get_files_context(self, prompt: str) -> str:
        """
        Recupera contenido de archivos relevantes.
        
        Args:
            prompt: Prompt del usuario
            
        Returns:
            Contenido de archivos o cadena vacía
        """
        if not self.file_manager.loaded_files:
            return ""
        
        files_content = ""
        prompt_lower = prompt.lower()
        
        for file_path, loaded_file in self.file_manager.loaded_files.items():
            file_name_lower = loaded_file.path.name.lower()
            
            if (file_name_lower in prompt_lower or 
                any(word in prompt_lower for word in ['analiza', 'analizar', 'revisa', 'revisar', 'código', 'codigo', 'archivo', 'main', 'config'])):
                
                if file_name_lower in prompt_lower or 'main.py' in file_name_lower:
                    files_content += f"\n=== Contenido de {loaded_file.path.name} ===\n"
                    files_content += loaded_file.content[:5000]
                    if len(loaded_file.content) > 5000:
                        files_content += "\n... (archivo truncado por tamaño)"
                    files_content += "\n\n"
                    break
        
        logger.debug(f"Contexto de archivos: {len(files_content)} chars")
        return files_content
    
    def _call_llm(self, context: str, rag_context: str, files_content: str, prompt: str) -> str:
        """
        Llama al LLM para generar respuesta.
        
        Args:
            context: Contexto del sistema
            rag_context: Contexto RAG
            files_content: Contenido de archivos
            prompt: Prompt del usuario
            
        Returns:
            Respuesta generada
        """
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": f"{rag_context}\n{files_content}\n{prompt}"}
        ]
        
        try:
            logger.debug(f"Llamando a LLM Manager...")
            answer = self._get_response(messages)
            return answer
        except Exception as llm_error:
            logger.warning(f"LLM Manager falló, usando fallback a Ollama directo: {llm_error}")
            full_prompt = f"{context}\n{rag_context}\n{files_content}\nUsuario: {prompt}\nPat:"
            return self._call_ollama(full_prompt)
    
    def _save_response(self, answer: str) -> None:
        """
        Guarda la respuesta en el historial y persiste.
        
        Args:
            answer: Respuesta generada
        """
        self.memory_manager.add_message("assistant", answer)
        logger.debug(f"Respuesta agregada al historial: '{answer[:50]}...'")
        self._save_history()
    
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
        if prompt.startswith('!'):
            result = self.process_command(prompt)
            if result:
                return result
        
        validated_prompt = self._validate_prompt(prompt)
        
        self.memory_manager.add_message("user", validated_prompt)
        logger.debug(f"Pregunta agregada al historial: '{validated_prompt[:50]}...'")
        
        try:
            context = self._build_context()
            rag_context = self._get_rag_context(validated_prompt)
            files_content = self._get_files_context(validated_prompt)
            
            answer = self._call_llm(context, rag_context, files_content, validated_prompt)
            
            self._save_response(answer)
            
            return answer
            
        except (OllamaConnectionError, OllamaTimeoutError, OllamaModelNotFoundError) as e:
            if self.memory_manager.active_memory:
                self.memory_manager.active_memory.pop()
            logger.error(f"Error al procesar pregunta, historial revertido: {e}")
            raise
            
        except Exception as e:
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
        cache_stats = self.cache.get_stats()
        
        base_stats = {
            "total_messages": memory_stats['total_context'],
            "active_messages": memory_stats['active_messages'],
            "passive_summaries": memory_stats['passive_summaries'],
            "user_messages": sum(1 for msg in self.memory_manager.active_memory if msg["role"] == "user"),
            "assistant_messages": sum(1 for msg in self.memory_manager.active_memory if msg["role"] == "assistant"),
            "model": self.model,
            "memory_path": str(self.memory_path),
            "loaded_files": file_stats['total_files'],
            "files_size_kb": file_stats['total_size_kb'],
            "files_usage_percent": file_stats['usage_percent'],
            "cache_hits": cache_stats['cache_hits'],
            "cache_misses": cache_stats['cache_misses'],
            "cache_hit_rate": cache_stats['hit_rate'],
            "cache_size": cache_stats['cache_size']
        }
        
        model_info = self.model_selector.get_model_info(self.model)
        if model_info:
            base_stats['model_speed'] = self.model_selector.get_speed_recommendation(self.model)
            base_stats['model_ram_required'] = f"{model_info.ram_recommended}GB"
        
        return base_stats
    
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