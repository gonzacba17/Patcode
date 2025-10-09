"""
agents/pat_agent.py
Agente principal de PatCode con integración completa de herramientas
"""

import json
import re
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
    
    def __init__(self, 
                 model: str = "qwen2.5-coder:7b",  # Modelo mejorado por defecto
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
        self.memory_file = Path(memory_path)
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
            if self.memory_file.exists():
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                self.memory_file.parent.mkdir(parents=True, exist_ok=True)
                return []
        except Exception as e:
            print(f"⚠️  Error cargando memoria: {e}")
            return []
    
    def save_memory(self):
        """Guarda el historial de memoria en archivo JSON"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
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
        # Detectar si necesita usar herramientas
        if self._should_use_tools(prompt):
            return self._ask_with_tools(prompt)
        else:
            return self._ask_simple(prompt)
    
    def _should_use_tools(self, prompt: str) -> bool:
        """Determina si el prompt requiere usar herramientas"""
        tool_keywords = [
            "archivo", "file", "leer", "read", "escribe", "write",
            "lista", "list", "directorio", "directory", "busca", "search",
            "muestra", "show", "ver", "see", "analiza", "analyze",
            "proyecto", "project", "estructura", "structure",
            "código", "code", "archivos principales", "main files",
            "resumen", "summary", "qué hace", "what does"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in tool_keywords)
    
    def _ask_with_tools(self, prompt: str) -> str:
        """Procesa pregunta con acceso a herramientas"""
        # Recopilar información del proyecto
        tool_context = self._gather_tool_context(prompt)
        
        # Construir prompt enriquecido
        enriched_prompt = self._build_enriched_prompt(prompt, tool_context)
        
        # Agregar al historial
        self.history.append({"role": "user", "content": prompt})
        
        # Obtener respuesta
        response = self._call_ollama(enriched_prompt)
        
        if response:
            self.history.append({"role": "assistant", "content": response})
            self.save_memory()
        
        return response
    
    def _ask_simple(self, prompt: str) -> str:
        """Procesa pregunta simple sin herramientas"""
        self.history.append({"role": "user", "content": prompt})
        
        context = self._build_simple_context(prompt)
        response = self._call_ollama(context)
        
        if response:
            self.history.append({"role": "assistant", "content": response})
            self.save_memory()
        
        return response
    
    def _gather_tool_context(self, prompt: str) -> str:
        """Recopila información usando herramientas"""
        parts = []
        prompt_lower = prompt.lower()
        
        # Información básica del proyecto
        if any(w in prompt_lower for w in ["estructura", "archivos", "proyecto", "resumen", "structure", "files"]):
            result = self.execute_tool("list_directory", path=".")
            if result.get("success"):
                files = result.get("files", [])
                dirs = result.get("directories", [])
                
                # Archivos importantes
                important = [f for f in files if f in [
                    "main.py", "README.md", "requirements.txt", 
                    "setup.py", "package.json", ".gitignore"
                ]]
                
                parts.append("📂 **Project Structure:**")
                parts.append(f"Location: {self.workspace_root}\n")
                
                if important:
                    parts.append("**Key Files:**")
                    for f in important:
                        parts.append(f"  - {f}")
                
                main_dirs = [d for d in dirs if not d.startswith('.') and 
                            d not in ['__pycache__', 'venv', 'env', 'node_modules']]
                if main_dirs:
                    parts.append("\n**Main Directories:**")
                    for d in main_dirs[:8]:
                        parts.append(f"  - {d}/")
                
                py_files = [f for f in files if f.endswith('.py')]
                if py_files:
                    parts.append(f"\n**Python Files:** {len(py_files)} total")
        
        # Leer README si existe
        if any(w in prompt_lower for w in ["readme", "resumen", "documentación", "summary"]):
            readme = self.execute_tool("read_file", file_path="README.md")
            if readme.get("success"):
                content = readme.get("content", "")
                parts.append("\n📄 **README.md Content:**")
                parts.append("```")
                parts.append(content[:2500] if len(content) > 2500 else content)
                parts.append("```")
        
        return "\n".join(parts) if parts else "No additional project information available."
    
    def _build_enriched_prompt(self, user_prompt: str, tool_context: str) -> str:
        """Construye prompt enriquecido con contexto de herramientas"""
        return f"""You are PatCode, an expert AI programming assistant.

CRITICAL INSTRUCTION: The following is REAL DATA from the actual project.
You MUST base your response ONLY on this information.
DO NOT invent, assume, or hallucinate any details not present below.

====================
PROJECT INFORMATION:
====================
{tool_context}
====================

USER QUESTION: {user_prompt}

RESPONSE RULES:
1. Answer based ONLY on the project information above
2. If information is insufficient, say "I don't have information about..."
3. Be specific and cite actual file names you see
4. Use markdown formatting
5. Be concise but helpful

Your response:"""
    
    def _build_simple_context(self, prompt: str) -> str:
        """Construye contexto simple para preguntas generales"""
        system = f"""You are PatCode, an expert programming assistant working in: {self.workspace_root}

You help with:
- Code explanations and architecture
- Debugging and error analysis  
- Best practices and design patterns
- Writing clean, maintainable code

Be concise, practical, and helpful."""
        
        # Incluir últimos mensajes
        recent = self.history[-3:]
        context = f"{system}\n\n"
        
        for msg in recent:
            role = msg.get("role", "").capitalize()
            content = msg.get("content", "")
            context += f"{role}: {content}\n"
        
        context += f"User: {prompt}\nAssistant:"
        
        return context
    
    def _call_ollama(self, prompt: str) -> str:
        """Realiza llamada a Ollama"""
        try:
            # Parámetros optimizados según el modelo
            options = {
                "temperature": 0.3,  # Más determinístico para código
                "num_predict": 2000,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "").strip()
                return answer if answer else "Lo siento, no pude generar una respuesta."
            else:
                return f"❌ Error del servidor Ollama: {response.status_code}"
        
        except requests.exceptions.ConnectionError:
            return "❌ No se pudo conectar a Ollama. ¿Está corriendo? (ollama serve)"
        except requests.exceptions.Timeout:
            return "❌ Timeout esperando respuesta de Ollama"
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecuta una herramienta específica"""
        if not TOOLS_AVAILABLE or tool_name not in self.tools:
            return {"success": False, "error": f"Tool not available: {tool_name}"}
        
        try:
            return self.tools[tool_name].execute(**kwargs)
        except Exception as e:
            return {"success": False, "error": f"Error executing {tool_name}: {str(e)}"}
    
    def list_available_tools(self) -> List[str]:
        """Retorna lista de herramientas disponibles"""
        return list(self.tools.keys()) if TOOLS_AVAILABLE else []
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una herramienta específica"""
        if not TOOLS_AVAILABLE or tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        return {
            "name": tool_name,
            "description": getattr(tool, 'description', "Sin descripción"),
            "schema": tool.get_schema() if hasattr(tool, 'get_schema') else {}
        }