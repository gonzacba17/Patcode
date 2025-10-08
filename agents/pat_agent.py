"""
agents/pat_agent.py
Agente principal de PatCode con integración de herramientas
"""

import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Importar herramientas
try:
    from tools.file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool
    from tools.shell_tools import ExecuteCommandTool, SearchFilesTool
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


class PatAgent:
    """Agente principal que interactúa con Ollama y gestiona herramientas"""
    
    def __init__(self, model: str = "llama3.2:latest", 
                 workspace_root: str = ".",
                 memory_path: str = "agents/memory/memory.json",
                 ollama_url: str = "http://localhost:11434"):
        """
        Inicializa el agente PatCode
        
        Args:
            model: Modelo de Ollama a usar
            workspace_root: Directorio raíz del proyecto
            memory_path: Ruta al archivo de memoria
            ollama_url: URL del servidor Ollama
        """
        self.model = model
        self.workspace_root = Path(workspace_root).resolve()
        self.memory_path = Path(memory_path)
        self.ollama_url = ollama_url
        self.history = self.load_memory()
        
        # Inicializar herramientas
        self.tools = {}
        if TOOLS_AVAILABLE:
            self._init_tools()
    
    def _init_tools(self):
        """Inicializa todas las herramientas disponibles"""
        workspace = str(self.workspace_root)
        
        self.tools = {
            "read_file": ReadFileTool(workspace_root=workspace),
            "write_file": WriteFileTool(workspace_root=workspace),
            "list_directory": ListDirectoryTool(workspace_root=workspace),
            "execute_command": ExecuteCommandTool(workspace_root=workspace),
            "search_files": SearchFilesTool(workspace_root=workspace),
        }
    
    def load_memory(self) -> List[Dict[str, str]]:
        """Carga el historial de memoria desde archivo JSON"""
        try:
            if self.memory_path.exists():
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # Crear directorio si no existe
                self.memory_path.parent.mkdir(parents=True, exist_ok=True)
                return []
        except Exception as e:
            print(f"⚠️  Error cargando memoria: {e}")
            return []
    
    def save_memory(self):
        """Guarda el historial de memoria en archivo JSON"""
        try:
            # Asegurar que el directorio existe
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error guardando memoria: {e}")
    
    def ask(self, prompt: str) -> str:
        """
        Envía una pregunta al agente y obtiene respuesta
        
        Args:
            prompt: Pregunta o instrucción del usuario
            
        Returns:
            Respuesta generada por el modelo
        """
        # Agregar pregunta al historial
        self.history.append({"role": "user", "content": prompt})
        
        # Construir contexto
        context = self._build_context()
        
        # Enviar a Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": context,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "").strip()
                
                if not answer:
                    answer = "Lo siento, no pude generar una respuesta."
                
                # Agregar respuesta al historial
                self.history.append({"role": "assistant", "content": answer})
                self.save_memory()
                
                return answer
            else:
                error_msg = f"Error del servidor Ollama: {response.status_code}"
                print(f"❌ {error_msg}")
                return error_msg
        
        except requests.exceptions.ConnectionError:
            error_msg = "❌ No se pudo conectar a Ollama. ¿Está corriendo? (ollama serve)"
            print(error_msg)
            return error_msg
        except requests.exceptions.Timeout:
            error_msg = "❌ Timeout esperando respuesta de Ollama"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error inesperado: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _build_context(self) -> str:
        """
        Construye el contexto completo para enviar al modelo
        Incluye los últimos mensajes del historial
        """
        # System prompt
        system_prompt = """Eres PatCode, un asistente de programación experto.
Ayudas a desarrolladores con:
- Explicar código
- Depurar errores
- Sugerir mejoras
- Escribir código nuevo
- Responder preguntas técnicas

Sé conciso, claro y útil. Si no estás seguro de algo, dilo."""
        
        # Construir contexto con últimos mensajes
        context = f"System: {system_prompt}\n\n"
        
        # Incluir últimos 5 mensajes para mantener contexto
        recent_messages = self.history[-5:]
        for msg in recent_messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            context += f"{role}: {content}\n"
        
        return context
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una herramienta específica
        
        Args:
            tool_name: Nombre de la herramienta
            **kwargs: Parámetros para la herramienta
            
        Returns:
            Resultado de la ejecución
        """
        if not TOOLS_AVAILABLE:
            return {
                "success": False,
                "error": "Herramientas no disponibles"
            }
        
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Herramienta no encontrada: {tool_name}"
            }
        
        tool = self.tools[tool_name]
        
        try:
            result = tool.execute(**kwargs)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Error ejecutando {tool_name}: {str(e)}"
            }
    
    def list_available_tools(self) -> List[str]:
        """Retorna lista de herramientas disponibles"""
        return list(self.tools.keys()) if TOOLS_AVAILABLE else []
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una herramienta específica
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Información de la herramienta o None
        """
        if not TOOLS_AVAILABLE or tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        return {
            "name": tool_name,
            "description": tool.description if hasattr(tool, 'description') else "Sin descripción",
            "schema": tool.get_schema() if hasattr(tool, 'get_schema') else {}
        }