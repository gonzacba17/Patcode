"""
PatAgent mejorado con capacidades de manejo de archivos
Versión 2.1 - Fase 1 completa
"""
import requests
import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

# Importar FileManager
from agents.file_manager import FileManager

class PatAgent:
    """Agente de IA con capacidades de manejo de archivos"""
    
    def __init__(
        self, 
        model: str = "llama3.2:latest", 
        memory_path: str = "memory/memory.json",
        max_history: int = 100,
        system_prompt: Optional[str] = None,
        enable_file_operations: bool = True,
        working_dir: str = ".",
        sandbox_mode: bool = True
    ):
        self.model = model
        self.memory_path = memory_path
        self.max_history = max_history
        self.base_url = "http://localhost:11434"
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # File operations
        self.enable_file_operations = enable_file_operations
        if enable_file_operations:
            self.file_manager = FileManager(
                working_dir=working_dir,
                sandbox_mode=sandbox_mode
            )
        
        # Crear directorio de memoria
        os.makedirs(os.path.dirname(memory_path) or ".", exist_ok=True)
        
        # Cargar historial
        self.history = self.load_memory()
        
        # Verificar conexión
        if not self._check_ollama_connection():
            raise ConnectionError(
                "❌ No se puede conectar con Ollama.\n"
                "Asegurate de que esté corriendo: 'ollama serve'"
            )
    
    def _default_system_prompt(self) -> str:
        """System prompt con capacidades de archivos"""
        base_prompt = """Sos PatCode, un asistente de programación experto y amigable.

Características:
- Explicás conceptos de forma clara y concisa
- Proporcionás ejemplos de código prácticos
- Sugerís mejores prácticas
- Ayudás a debuggear problemas
- Usás un tono cercano (vos argentino)
- Siempre incluís código funcional cuando es relevante"""
        
        if self.enable_file_operations:
            base_prompt += """

Capacidades de archivos:
- Podés leer archivos del proyecto cuando el usuario lo pida
- Podés analizar código y sugerir mejoras
- Podés crear nuevos archivos con código
- Siempre mostrás previews antes de modificar archivos existentes

Cuando el usuario mencione un archivo (ej: "mirá main.py", "analizá este código"):
1. Informale que vas a leer el archivo
2. Leé el contenido usando tus capacidades
3. Analizalo y respondé con insights útiles"""
        
        return base_prompt
    
    def _check_ollama_connection(self) -> bool:
        """Verifica que Ollama esté corriendo"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def load_memory(self) -> List[Dict[str, str]]:
        """Carga el historial desde el archivo JSON"""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    return history[-self.max_history:]
            return []
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error cargando memoria: {e}")
            return []
    
    def save_memory(self):
        """Guarda el historial en el archivo JSON"""
        try:
            trimmed_history = self.history[-self.max_history:]
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(trimmed_history, f, indent=2, ensure_ascii=False)
            self.history = trimmed_history
        except IOError as e:
            print(f"⚠️  Error guardando memoria: {e}")
    
    def clear_memory(self):
        """Limpia toda la memoria de conversación"""
        self.history = []
        self.save_memory()
    
    def _detect_file_references(self, prompt: str) -> List[str]:
        """
        Detecta referencias a archivos en el prompt
        Ej: "mirá main.py", "analizá src/app.js", "leé este archivo: test.py"
        """
        patterns = [
            r'(?:mirá|leé|analizá|revisá|abrí)\s+([^\s,]+\.\w+)',  # mirá main.py
            r'archivo[:\s]+([^\s,]+\.\w+)',  # archivo: main.py
            r'(?:en|del)\s+(?:archivo\s+)?([^\s,]+\.\w+)',  # en main.py
            r'\b([^\s/]+\.[a-z]{1,4})\b',  # extensiones comunes
        ]
        
        files = []
        for pattern in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            files.extend(matches)
        
        # Filtrar duplicados y validar que parezcan nombres de archivo
        unique_files = []
        for f in files:
            if f not in unique_files and '.' in f:
                unique_files.append(f)
        
        return unique_files
    
    def _process_file_operations(self, prompt: str) -> Optional[str]:
        """
        Procesa operaciones de archivos antes de enviar al LLM
        Retorna contexto adicional si se encontraron archivos
        """
        if not self.enable_file_operations:
            return None
        
        files = self._detect_file_references(prompt)
        if not files:
            return None
        
        context = "\n\n📁 CONTEXTO DE ARCHIVOS:\n"
        files_read = 0
        
        for filepath in files:
            try:
                print(f"📖 Leyendo {filepath}...")
                file_data = self.file_manager.read_file(filepath)
                
                context += f"\n--- Archivo: {file_data['name']} ---\n"
                context += f"Líneas: {file_data['lines']} | Tamaño: {file_data['size_bytes']} bytes\n"
                context += f"```{self._get_language_for_extension(file_data['extension'])}\n"
                context += file_data['content']
                context += "\n```\n"
                
                files_read += 1
                
            except Exception as e:
                context += f"\n⚠️ No se pudo leer {filepath}: {str(e)}\n"
        
        if files_read > 0:
            return context
        return None
    
    def _get_language_for_extension(self, ext: str) -> str:
        """Retorna el nombre del lenguaje para syntax highlighting"""
        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'jsx', '.tsx': 'tsx', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust',
            '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
            '.kt': 'kotlin', '.cs': 'csharp', '.html': 'html',
            '.css': 'css', '.json': 'json', '.yaml': 'yaml',
            '.md': 'markdown', '.sql': 'sql', '.sh': 'bash'
        }
        return lang_map.get(ext.lower(), '')
    
    def ask(self, prompt: str, stream: bool = True) -> str:
        """
        Envía un prompt al modelo (con detección de archivos)
        
        Args:
            prompt: Pregunta o instrucción del usuario
            stream: Si es True, imprime la respuesta en tiempo real
        
        Returns:
            Respuesta completa del modelo
        """
        # Detectar y procesar archivos mencionados
        file_context = self._process_file_operations(prompt)
        
        # Si hay contexto de archivos, agregarlo al prompt
        enhanced_prompt = prompt
        if file_context:
            enhanced_prompt = f"{prompt}\n{file_context}"
        
        # Agregar mensaje del usuario al historial
        self.history.append({"role": "user", "content": enhanced_prompt})
        
        try:
            messages = self._build_messages()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": stream
                },
                stream=stream,
                timeout=120
            )
            
            response.raise_for_status()
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                data = response.json()
                answer = data.get("message", {}).get("content", "").strip()
                self.history.append({"role": "assistant", "content": answer})
                self.save_memory()
                return answer
                
        except requests.exceptions.Timeout:
            error_msg = "⏱️  Timeout: el modelo tardó demasiado en responder"
            print(error_msg)
            return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Error de conexión: {str(e)}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error inesperado: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _handle_streaming_response(self, response) -> str:
        """Maneja la respuesta en streaming de Ollama"""
        full_response = ""
        
        try:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    
                    if 'message' in data:
                        chunk = data['message'].get('content', '')
                        print(chunk, end='', flush=True)
                        full_response += chunk
                    
                    if data.get('done', False):
                        break
            
            print()
            
            self.history.append({"role": "assistant", "content": full_response})
            self.save_memory()
            
            return full_response
            
        except Exception as e:
            print(f"\n⚠️  Error en streaming: {e}")
            return full_response
    
    def _build_messages(self) -> List[Dict[str, str]]:
        """Construye la lista de mensajes para la API de chat"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Contexto limitado para no saturar
        context_limit = 20
        recent_history = self.history[-context_limit:]
        messages.extend(recent_history)
        
        return messages
    
    # Comandos de archivos explícitos
    
    def read_file_command(self, filepath: str) -> str:
        """Comando explícito para leer un archivo"""
        if not self.enable_file_operations:
            return "❌ Operaciones de archivos deshabilitadas"
        
        try:
            file_data = self.file_manager.read_file(filepath)
            
            output = f"\n📄 {file_data['name']}\n"
            output += f"{'='*60}\n"
            output += f"Líneas: {file_data['lines']} | "
            output += f"Tamaño: {file_data['size_bytes']} bytes | "
            output += f"Modificado: {file_data['modified']}\n"
            output += f"{'='*60}\n\n"
            output += file_data['content']
            
            print(output)
            return output
            
        except Exception as e:
            error = f"❌ Error leyendo archivo: {str(e)}"
            print(error)
            return error
    
    def write_file_command(self, filepath: str, content: str) -> bool:
        """Comando explícito para escribir un archivo"""
        if not self.enable_file_operations:
            print("❌ Operaciones de archivos deshabilitadas")
            return False
        
        try:
            return self.file_manager.write_file(filepath, content, preview=True)
        except Exception as e:
            print(f"❌ Error escribiendo archivo: {str(e)}")
            return False
    
    def list_files_command(self, pattern: str = "*") -> List[str]:
        """Comando para listar archivos"""
        if not self.enable_file_operations:
            print("❌ Operaciones de archivos deshabilitadas")
            return []
        
        try:
            files = self.file_manager.list_files(pattern)
            print(f"\n📁 Archivos encontrados ({len(files)}):\n")
            for f in files:
                print(f"  • {f}")
            return files
        except Exception as e:
            print(f"❌ Error listando archivos: {str(e)}")
            return []
    
    def analyze_project_command(self) -> Dict:
        """Comando para analizar el proyecto"""
        if not self.enable_file_operations:
            print("❌ Operaciones de archivos deshabilitadas")
            return {}
        
        try:
            stats = self.file_manager.analyze_project()
            
            print(f"\n📊 Análisis del Proyecto\n")
            print(f"{'='*60}")
            print(f"Total de archivos: {stats['total_files']}")
            print(f"Total de líneas: {stats['total_lines']:,}")
            
            print(f"\n🗣️ Lenguajes detectados:")
            for lang, data in stats['languages'].items():
                print(f"  • {lang}: {data['files']} archivos, {data['lines']:,} líneas")
            
            print(f"\n📝 Archivos por tipo:")
            for ext, count in stats['files_by_type'].items():
                print(f"  • {ext}: {count} archivos")
            
            return stats
            
        except Exception as e:
            print(f"❌ Error analizando proyecto: {str(e)}")
            return {}
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de uso"""
        stats = {
            "total_messages": len(self.history),
            "user_messages": sum(1 for m in self.history if m['role'] == 'user'),
            "assistant_messages": sum(1 for m in self.history if m['role'] == 'assistant'),
            "memory_size_kb": os.path.getsize(self.memory_path) / 1024 if os.path.exists(self.memory_path) else 0
        }
        
        if self.enable_file_operations:
            stats['file_operations_enabled'] = True
            stats['sandbox_mode'] = self.file_manager.sandbox_mode
        
        return stats
    
    def export_conversation(self, output_path: str = "conversation_export.md"):
        """Exporta la conversación actual a un archivo Markdown"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# PatCode Conversation Export\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Model:** {self.model}\n\n")
                f.write("---\n\n")
                
                for msg in self.history:
                    role = "👤 Usuario" if msg['role'] == 'user' else "🤖 PatCode"
                    f.write(f"## {role}\n\n")
                    f.write(f"{msg['content']}\n\n")
                    f.write("---\n\n")
            
            print(f"✅ Conversación exportada a: {output_path}")
        except IOError as e:
            print(f"❌ Error exportando: {e}")