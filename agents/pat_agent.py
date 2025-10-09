import requests
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

class PatAgent:
    """Agente de IA para PatCode con mejoras robustas"""
    
    def __init__(
        self, 
        model: str = "llama3.2:latest", 
        memory_path: str = "memory/memory.json",
        max_history: int = 50,
        system_prompt: Optional[str] = None
    ):
        self.model = model
        self.memory_path = memory_path
        self.max_history = max_history
        self.base_url = "http://localhost:11434"
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Crear directorio de memoria si no existe
        os.makedirs(os.path.dirname(memory_path) or ".", exist_ok=True)
        
        # Cargar historial
        self.history = self.load_memory()
        
        # Verificar conexión con Ollama
        if not self._check_ollama_connection():
            raise ConnectionError(
                "❌ No se puede conectar con Ollama.\n"
                "Asegurate de que esté corriendo: 'ollama serve'"
            )
    
    def _default_system_prompt(self) -> str:
        """System prompt por defecto para PatCode"""
        return """Sos PatCode, un asistente de programación experto y amigable.

Características:
- Explicás conceptos de forma clara y concisa
- Proporcionás ejemplos de código prácticos
- Sugerís mejores prácticas
- Ayudás a debuggear problemas
- Usás un tono cercano (vos argentino)
- Siempre incluís código funcional cuando es relevante

Cuando te pidan código:
1. Explicá brevemente qué hace
2. Mostrá el código con comentarios
3. Agregá notas sobre posibles mejoras"""
    
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
                    # Limitar al max_history más reciente
                    return history[-self.max_history:]
            return []
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error cargando memoria: {e}")
            return []
    
    def save_memory(self):
        """Guarda el historial en el archivo JSON"""
        try:
            # Mantener solo max_history mensajes
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
        print("🧹 Memoria limpiada")
    
    def ask(self, prompt: str, stream: bool = True) -> str:
        """
        Envía un prompt al modelo y obtiene la respuesta
        
        Args:
            prompt: Pregunta o instrucción del usuario
            stream: Si es True, imprime la respuesta en tiempo real
        
        Returns:
            Respuesta completa del modelo
        """
        # Agregar mensaje del usuario al historial
        self.history.append({"role": "user", "content": prompt})
        
        try:
            # Preparar mensajes para la API de chat
            messages = self._build_messages()
            
            # Llamada a la API con streaming
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
                    
                    # Ollama envía done: true al terminar
                    if data.get('done', False):
                        break
            
            print()  # Nueva línea al terminar
            
            # Guardar respuesta completa en el historial
            self.history.append({"role": "assistant", "content": full_response})
            self.save_memory()
            
            return full_response
            
        except Exception as e:
            print(f"\n⚠️  Error en streaming: {e}")
            return full_response
    
    def _build_messages(self) -> List[Dict[str, str]]:
        """Construye la lista de mensajes para la API de chat"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Agregar historial (últimos N mensajes para no saturar contexto)
        context_limit = 20  # Últimos 10 intercambios
        recent_history = self.history[-context_limit:]
        messages.extend(recent_history)
        
        return messages
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de uso"""
        return {
            "total_messages": len(self.history),
            "user_messages": sum(1 for m in self.history if m['role'] == 'user'),
            "assistant_messages": sum(1 for m in self.history if m['role'] == 'assistant'),
            "memory_size_kb": os.path.getsize(self.memory_path) / 1024 if os.path.exists(self.memory_path) else 0
        }
    
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