"""
PatAgent v3.0 - Versión simplificada funcional
"""
import requests
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

from agents.file_manager import FileManager

class PatAgent:
    """Agente de IA con capacidades de archivos"""
    
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
        self.enable_file_operations = enable_file_operations
        self.enable_tools = True
        self.enable_planning = True
        
        # File operations
        self.file_manager = None
        if enable_file_operations:
            self.file_manager = FileManager(working_dir=working_dir, sandbox_mode=sandbox_mode)
        
        # System prompt
        self.system_prompt = system_prompt or "Sos PatCode v3.0, un asistente de programación experto."
        
        # Crear directorio de memoria
        os.makedirs(os.path.dirname(memory_path) or ".", exist_ok=True)
        
        # Cargar historial
        self.history = self.load_memory()
        
        # Verificar conexión
        if not self._check_ollama_connection():
            raise ConnectionError("❌ No se puede conectar con Ollama.\nAsegurate de que esté corriendo: 'ollama serve'")
    
    def _check_ollama_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def load_memory(self) -> List[Dict[str, str]]:
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    return json.load(f)[-self.max_history:]
            return []
        except:
            return []
    
    def save_memory(self):
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.history[-self.max_history:], f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def clear_memory(self):
        self.history = []
        self.save_memory()
    
    def ask(self, prompt: str, stream: bool = True) -> str:
        self.history.append({"role": "user", "content": prompt})
        
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.history[-20:])
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": stream},
                stream=stream,
                timeout=120
            )
            
            if stream:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if 'message' in data:
                            chunk = data['message'].get('content', '')
                            print(chunk, end='', flush=True)
                            full_response += chunk
                        if data.get('done'):
                            break
                print()
                self.history.append({"role": "assistant", "content": full_response})
                self.save_memory()
                return full_response
            else:
                data = response.json()
                answer = data.get("message", {}).get("content", "").strip()
                self.history.append({"role": "assistant", "content": answer})
                self.save_memory()
                return answer
        except Exception as e:
            return f"❌ Error: {e}"
    
    def read_file_command(self, filepath: str) -> str:
        if not self.file_manager:
            return "❌ File operations deshabilitadas"
        try:
            data = self.file_manager.read_file(filepath)
            output = f"\n📄 {data['name']}\n{'='*60}\nLíneas: {data['lines']}\n{'='*60}\n\n{data['content']}"
            print(output)
            return output
        except Exception as e:
            return f"❌ Error: {e}"
    
    def list_files_command(self, pattern: str = "*") -> List[str]:
        if not self.file_manager:
            return []
        try:
            files = self.file_manager.list_files(pattern)
            print(f"\n📁 Archivos ({len(files)}):")
            for f in files:
                print(f"  • {f}")
            return files
        except:
            return []
    
    def analyze_project_command(self) -> Dict:
        if not self.file_manager:
            return {}
        try:
            stats = self.file_manager.analyze_project()
            print(f"\n📊 Análisis del Proyecto\n{'='*60}")
            print(f"Total archivos: {stats['total_files']}")
            print(f"Total líneas: {stats['total_lines']:,}\n")
            print("🗣️ Lenguajes:")
            for lang, data in stats['languages'].items():
                print(f"  • {lang}: {data['files']} archivos, {data['lines']:,} líneas")
            return stats
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def get_stats(self) -> Dict:
        return {
            "total_messages": len(self.history),
            "user_messages": sum(1 for m in self.history if m['role'] == 'user'),
            "assistant_messages": sum(1 for m in self.history if m['role'] == 'assistant'),
            "memory_size_kb": os.path.getsize(self.memory_path) / 1024 if os.path.exists(self.memory_path) else 0,
            "version": "3.0",
            "features": {
                "file_operations": self.enable_file_operations,
                "tool_calling": self.enable_tools,
                "planning": self.enable_planning
            }
        }
    
    def export_conversation(self, output_path: str = "conversation_export.md"):
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# PatCode v3.0\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for msg in self.history:
                    role = "👤" if msg['role'] == 'user' else "🤖"
                    f.write(f"## {role}\n\n{msg['content']}\n\n---\n\n")
            print(f"✅ Exportado: {output_path}")
        except:
            pass