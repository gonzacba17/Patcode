"""
PatAgent - Agente principal de PatCode con capacidades agentic
"""
import json
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path

from config.settings import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_HISTORY_MESSAGES,
    STREAM_RESPONSES, REQUEST_TIMEOUT, MEMORY_FILE
)
from config.prompts import SYSTEM_PROMPT
from tools.file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from tools.shell_tools import ExecuteCommandTool, SearchFilesTool


class PatAgent:
    """
    Agente de programación con capacidades agentic
    
    Puede trabajar en dos modos:
    - Simple: Responde directamente (ask)
    - Agentic: Usa herramientas automáticamente (ask_agentic)
    """
    
    def __init__(self, model: str = OLLAMA_MODEL, verbose: bool = False):
        """
        Inicializa el agente
        
        Args:
            model: Nombre del modelo Ollama a usar
            verbose: Si es True, muestra logs detallados
        """
        self.model = model
        self.verbose = verbose
        self.history = self._load_memory()
        self.tools = self._initialize_tools()
        self.current_context = {}  # Contexto de la conversación actual
        
        # Agregar system prompt si no existe
        if not self.history or self.history[0].get("role") != "system":
            self.history.insert(0, {
                "role": "system",
                "content": SYSTEM_PROMPT
            })
        
        if self.verbose:
            print(f"🤖 PatAgent inicializado con modelo: {self.model}")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Inicializa todas las herramientas disponibles"""
        tools = {
            "read_file": ReadFileTool(),
            "write_file": WriteFileTool(),
            "list_directory": ListDirectoryTool(),
            "execute_command": ExecuteCommandTool(),
            "search_files": SearchFilesTool()
        }
        
        if self.verbose:
            print(f"🔧 {len(tools)} herramientas cargadas")
        
        return tools
    
    def _load_memory(self) -> List[Dict[str, str]]:
        """
        Carga el historial de conversación desde memoria
        
        Returns:
            Lista de mensajes del historial
        """
        try:
            if MEMORY_FILE.exists():
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if self.verbose:
                        print(f"📚 Memoria cargada: {len(history)} mensajes")
                    return history
            return []
        except Exception as e:
            print(f"⚠️ Error cargando memoria: {e}")
            return []
    
    def _save_memory(self):
        """Guarda el historial de conversación en memoria"""
        try:
            # Mantener system prompt + últimos N mensajes
            system_msg = None
            if self.history and self.history[0].get("role") == "system":
                system_msg = self.history[0]
            
            # Tomar los últimos mensajes
            recent_msgs = self.history[-MAX_HISTORY_MESSAGES:]
            
            # Asegurar que el system prompt esté primero
            if system_msg and (not recent_msgs or recent_msgs[0] != system_msg):
                self.history = [system_msg] + [m for m in recent_msgs if m != system_msg]
            else:
                self.history = recent_msgs
            
            # Guardar a archivo
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            
            if self.verbose:
                print(f"💾 Memoria guardada: {len(self.history)} mensajes")
                
        except Exception as e:
            print(f"⚠️ Error guardando memoria: {e}")
    
    def _check_ollama_connection(self) -> bool:
        """
        Verifica que Ollama esté corriendo y accesible
        
        Returns:
            True si Ollama está disponible
        """
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _call_ollama(self, prompt: str, stream: bool = STREAM_RESPONSES) -> Optional[str]:
        """
        Llama a la API de Ollama para generar una respuesta
        
        Args:
            prompt: El prompt completo a enviar
            stream: Si es True, muestra la respuesta en tiempo real
            
        Returns:
            Respuesta del modelo o None si hay error
        """
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=REQUEST_TIMEOUT,
                stream=stream
            )
            
            if stream:
                # Modo streaming: mostrar respuesta en tiempo real
                full_response = ""
                print("PatCode: ", end="", flush=True)
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            full_response += chunk
                            print(chunk, end="", flush=True)
                        except json.JSONDecodeError:
                            continue
                
                print()  # Nueva línea al final
                return full_response
            else:
                # Modo no-streaming: respuesta completa
                data = response.json()
                return data.get("response", "").strip()
                
        except requests.exceptions.Timeout:
            return "⏱️ Timeout: La solicitud tardó demasiado. Intentá con una pregunta más simple."
        except requests.exceptions.ConnectionError:
            return "🔌 Error de conexión: ¿Ollama está corriendo? Ejecutá 'ollama serve'"
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"
    
    def _build_prompt(self) -> str:
        """
        Construye el prompt completo con el historial de conversación
        
        Returns:
            String con el prompt formateado
        """
        # Excluir el system prompt del historial visible
        messages = [
            msg for msg in self.history[1:] 
            if msg.get("role") in ["user", "assistant"]
        ]
        
        prompt = ""
        for msg in messages[-MAX_HISTORY_MESSAGES:]:
            role = msg["role"].capitalize()
            content = msg["content"]
            prompt += f"{role}: {content}\n"
        
        return prompt
    
    def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una herramienta específica
        
        Args:
            tool_name: Nombre de la herramienta a ejecutar
            **kwargs: Argumentos para la herramienta
            
        Returns:
            Diccionario con el resultado de la ejecución
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Herramienta desconocida: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        if self.verbose:
            print(f"🔧 Ejecutando: {tool_name} con {kwargs}")
        
        tool = self.tools[tool_name]
        result = tool.execute(**kwargs)
        
        if self.verbose:
            status = "✅" if result.get("success") else "❌"
            print(f"{status} Resultado: {result.get('message', result.get('error'))}")
        
        return result
    
    def ask(self, user_input: str, stream: bool = STREAM_RESPONSES) -> str:
        """
        Procesa una pregunta en modo simple (sin agentic loop)
        
        Args:
            user_input: Pregunta o comando del usuario
            stream: Si mostrar la respuesta en streaming
            
        Returns:
            Respuesta del modelo
        """
        # Verificar conexión con Ollama
        if not self._check_ollama_connection():
            return "❌ Error: Ollama no está corriendo. Ejecutá 'ollama serve' en otra terminal."
        
        # Agregar mensaje del usuario al historial
        self.history.append({
            "role": "user",
            "content": user_input
        })
        
        # Construir prompt y obtener respuesta
        prompt = self._build_prompt()
        response = self._call_ollama(prompt, stream=stream)
        
        if response:
            # Agregar respuesta al historial
            self.history.append({
                "role": "assistant",
                "content": response
            })
            
            # Guardar memoria
            self._save_memory()
        
        return response if not stream else ""
    
    def ask_agentic(self, user_input: str, stream: bool = True) -> str:
        """
        Procesa una pregunta usando el agentic loop
        El agente puede usar herramientas automáticamente
        
        Args:
            user_input: Pregunta o tarea del usuario
            stream: Si mostrar respuestas en streaming
            
        Returns:
            Respuesta final del agente
        """
        # Importar aquí para evitar circular import
        from agents.agentic_loop import AgenticLoop
        
        # Verificar conexión
        if not self._check_ollama_connection():
            return "❌ Error: Ollama no está corriendo. Ejecutá 'ollama serve' en otra terminal."
        
        # Agregar mensaje del usuario al historial
        self.history.append({
            "role": "user",
            "content": user_input
        })
        
        # Ejecutar agentic loop
        loop = AgenticLoop(self, verbose=self.verbose)
        result = loop.run(user_input, stream=stream)
        
        return result
    
    def clear_history(self):
        """Limpia el historial de conversación conservando el system prompt"""
        system_msg = None
        if self.history and self.history[0].get("role") == "system":
            system_msg = self.history[0]
        
        self.history = [system_msg] if system_msg else []
        self._save_memory()
        
        print("🗑️ Historial limpiado")
    
    def list_tools(self) -> List[Dict[str, str]]:
        """
        Devuelve información de todas las herramientas disponibles
        
        Returns:
            Lista de diccionarios con nombre y descripción de cada herramienta
        """
        return [
            {
                "name": name,
                "description": tool.description
            }
            for name, tool in self.tools.items()
        ]
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        Devuelve un resumen del historial actual
        
        Returns:
            Diccionario con estadísticas del historial
        """
        user_msgs = sum(1 for msg in self.history if msg.get("role") == "user")
        assistant_msgs = sum(1 for msg in self.history if msg.get("role") == "assistant")
        
        return {
            "total_messages": len(self.history),
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "model": self.model
        }
    
    def export_conversation(self, filepath: str = "conversation_export.json"):
        """
        Exporta la conversación actual a un archivo
        
        Args:
            filepath: Ruta donde guardar el export
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "model": self.model,
                    "timestamp": str(Path(filepath).stat().st_mtime),
                    "history": self.history
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Conversación exportada a: {filepath}")
        except Exception as e:
            print(f"❌ Error exportando: {e}")