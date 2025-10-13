from datetime import datetime
import platform
import os
from typing import Dict, Any


class SystemTools:
    """Herramientas de información del sistema"""
    
    def __init__(self):
        pass
    
    def get_current_datetime(self) -> Dict[str, str]:
        """
        Obtiene la fecha y hora actual.
        
        Returns:
            Dict con fecha, hora y formato completo
        """
        now = datetime.now()
        
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "day_name": now.strftime("%A"),
            "formatted": now.strftime("%A, %d de %B de %Y - %H:%M:%S")
        }
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Obtiene información del sistema operativo.
        
        Returns:
            Dict con información del sistema
        """
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "cwd": os.getcwd()
        }


# ============================================================================
# MEJORA 2: Actualizar Tool Agent con System Tools y Mejor System Prompt
# ============================================================================
# Archivo: agents/tool_agent.py (ACTUALIZADO)
# ============================================================================

import requests
import json
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import sys

# Importar las herramientas
sys.path.append(str(Path(__file__).parent.parent))
from tools.file_operations import FileOperations
from tools.shell_operations import ShellOperations
from tools.git_operations import GitOperations
from tools.system_tools import SystemTools


# System Prompt mejorado
SYSTEM_PROMPT = """Eres PatCode, un asistente de programación experto y autónomo que trabaja como un ingeniero senior.

IDENTIDAD:
- Eres preciso, metódico y profesional
- Siempre ejecutas las acciones que te piden, no solo explicas cómo hacerlas
- Cuando te piden crear algo, lo creas directamente
- Cuando te piden información del sistema (fecha, hora), usas las herramientas apropiadas

REGLAS DE ORO:
1. USA LAS HERRAMIENTAS: Si te piden hacer algo, usa las herramientas disponibles
2. EJECUTA, NO EXPLIQUES: No digas "puedes hacer X", simplemente hazlo
3. VERIFICA: Después de crear/modificar algo, confirma que funcionó
4. SÉ ESPECÍFICO: Cuando uses herramientas, usa los parámetros correctos

HERRAMIENTAS DISPONIBLES:
- read_file(path): Lee un archivo
- write_file(path, content): Escribe/sobrescribe un archivo
- edit_file(path, old_content, new_content): Edita parte de un archivo
- create_file(path, content): Crea un nuevo archivo
- list_files(directory, pattern): Lista archivos (directory=".", pattern="*.py")
- run_command(command): Ejecuta comando shell
- run_tests(test_path): Ejecuta pytest
- git_status(): Estado del repositorio
- git_diff(): Cambios no commiteados
- git_commit(message): Crear commit
- get_datetime(): Obtener fecha y hora actual
- get_system_info(): Información del sistema

EJEMPLOS DE USO CORRECTO:

Usuario: "Crea un archivo con la fecha de hoy"
Tú: [Primero llamas get_datetime() para obtener la fecha]
    [Luego llamas create_file() con el contenido que incluye la fecha]
    "He creado el archivo con la fecha actual: 2025-10-13"

Usuario: "Lista los archivos Python"
Tú: [Llamas list_files con directory=".", pattern="*.py"]
    "Encontré 15 archivos Python: main.py, test.py, ..."

Usuario: "Muestra el status de git"
Tú: [Llamas git_status()]
    "Estado del repositorio: branch master, 5 archivos modificados..."

IMPORTANTE:
- Si necesitas información (fecha, archivos, etc.), PRIMERO llama a la herramienta
- Luego usa esa información en tu respuesta o en otra herramienta
- No inventes información, siempre usa las herramientas"""


class ToolAgent:
    """
    Agente inteligente con capacidad de usar herramientas.
    Utiliza function calling de Ollama para decidir qué herramienta usar.
    """
    
    def __init__(
        self,
        model: str = "llama3.2:latest",
        base_url: str = "http://localhost:11434",
        project_path: str = "."
    ):
        """
        Inicializa el agente con herramientas.
        
        Args:
            model: Modelo de Ollama a usar
            base_url: URL de la API de Ollama
            project_path: Ruta del proyecto a gestionar
        """
        self.model = model
        self.base_url = base_url
        self.project_path = project_path
        
        # Inicializar herramientas
        self.file_ops = FileOperations(project_path)
        self.shell_ops = ShellOperations(project_path)
        self.git_ops = GitOperations(project_path)
        self.sys_tools = SystemTools()
        
        # Historial de conversación
        self.history = []
        
        # Agregar system prompt
        self.history.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
        
        # Registrar herramientas disponibles
        self.tools = self._register_tools()
        self.tool_functions = self._map_tool_functions()
    
    def _register_tools(self) -> List[Dict[str, Any]]:
        """
        Registra todas las herramientas disponibles en formato OpenAI.
        Este formato es compatible con Ollama function calling.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Lee el contenido completo de un archivo del proyecto",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta relativa del archivo a leer (ej: 'main.py', 'src/utils.py')"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Escribe contenido en un archivo (crea o sobrescribe)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta relativa del archivo"
                            },
                            "content": {
                                "type": "string",
                                "description": "Contenido completo a escribir en el archivo"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edita una parte específica de un archivo existente",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta relativa del archivo a editar"
                            },
                            "old_content": {
                                "type": "string",
                                "description": "Contenido exacto a reemplazar (debe aparecer una sola vez)"
                            },
                            "new_content": {
                                "type": "string",
                                "description": "Nuevo contenido que reemplazará al anterior"
                            }
                        },
                        "required": ["path", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Crea un nuevo archivo con contenido inicial",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta relativa del nuevo archivo"
                            },
                            "content": {
                                "type": "string",
                                "description": "Contenido inicial del archivo"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "Lista archivos en un directorio con patrón opcional. Para listar archivos Python usa directory='.' y pattern='*.py'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directorio a listar, por defecto '.' (directorio actual)"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Patrón de archivos (ej: '*.py' para Python, '*.js' para JavaScript, '*' para todos)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Ejecuta un comando de shell/terminal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Comando a ejecutar (ej: 'pytest', 'python main.py')"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": "Ejecuta los tests del proyecto con pytest",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "test_path": {
                                "type": "string",
                                "description": "Ruta específica de test (opcional, si no se provee ejecuta todos)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_status",
                    "description": "Muestra el estado actual del repositorio Git",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_diff",
                    "description": "Muestra los cambios no commiteados en el repositorio",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_commit",
                    "description": "Crea un commit con todos los cambios actuales",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Mensaje descriptivo del commit"
                            }
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_datetime",
                    "description": "Obtiene la fecha y hora actual del sistema",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_info",
                    "description": "Obtiene información del sistema operativo y entorno",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    def _map_tool_functions(self) -> Dict[str, Callable]:
        """
        Mapea nombres de herramientas a funciones ejecutables.
        """
        return {
            "read_file": lambda args: self.file_ops.read_file(args["path"]),
            "write_file": lambda args: self.file_ops.write_file(args["path"], args["content"]),
            "edit_file": lambda args: self.file_ops.edit_file(
                args["path"], 
                args["old_content"], 
                args["new_content"]
            ),
            "create_file": lambda args: self.file_ops.create_file(
                args["path"], 
                args.get("content", "")
            ),
            "list_files": lambda args: self.file_ops.list_files(
                args.get("directory", "."),
                args.get("pattern", "*")
            ),
            "run_command": lambda args: self.shell_ops.run_command(args["command"]),
            "run_tests": lambda args: self.shell_ops.run_tests(args.get("test_path")),
            "git_status": lambda args: self.git_ops.status(),
            "git_diff": lambda args: self.git_ops.diff(),
            "git_commit": lambda args: self.git_ops.commit(args["message"]),
            "get_datetime": lambda args: self.sys_tools.get_current_datetime(),
            "get_system_info": lambda args: self.sys_tools.get_system_info()
        }
    
    def _execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Ejecuta una herramienta específica.
        
        Args:
            function_name: Nombre de la función
            arguments: Argumentos para la función
            
        Returns:
            Resultado de la ejecución
        """
        if function_name not in self.tool_functions:
            return f"Error: Herramienta '{function_name}' no encontrada"
        
        try:
            result = self.tool_functions[function_name](arguments)
            return result
        except Exception as e:
            return f"Error al ejecutar {function_name}: {str(e)}"
    
    def _call_ollama(self, messages: List[Dict], use_tools: bool = True) -> Dict:
        """
        Llama a la API de Ollama con o sin herramientas.
        
        Args:
            messages: Lista de mensajes de conversación
            use_tools: Si True, incluye herramientas disponibles
            
        Returns:
            Respuesta de Ollama
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        if use_tools:
            payload["tools"] = self.tools
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def ask(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Procesa un mensaje del usuario, permitiendo múltiples llamadas a herramientas.
        
        Args:
            user_message: Mensaje/instrucción del usuario
            max_iterations: Máximo número de iteraciones de tool calling
            
        Returns:
            Respuesta final del agente
        """
        # Agregar mensaje del usuario al historial
        self.history.append({
            "role": "user",
            "content": user_message
        })
        
        print(f"\n🤖 Procesando: {user_message}\n")
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Llamar a Ollama
            response = self._call_ollama(self.history)
            
            if "error" in response:
                error_msg = f"Error de API: {response['error']}"
                self.history.append({
                    "role": "assistant",
                    "content": error_msg
                })
                return error_msg
            
            message = response.get("message", {})
            
            # Si no hay tool calls, retornar la respuesta
            if "tool_calls" not in message or not message["tool_calls"]:
                assistant_content = message.get("content", "")
                self.history.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                return assistant_content
            
            # Procesar tool calls
            self.history.append(message)
            
            for tool_call in message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                
                print(f"🔧 Ejecutando: {function_name}({arguments})")
                
                # Ejecutar herramienta
                result = self._execute_tool(function_name, arguments)
                
                # Convertir resultado a string legible
                if isinstance(result, dict):
                    result_str = json.dumps(result, indent=2, ensure_ascii=False)
                elif isinstance(result, tuple):
                    result_str = str(result)
                elif isinstance(result, list):
                    result_str = "\n".join(str(item) for item in result[:20])  # Limitar a 20 items
                    if len(result) > 20:
                        result_str += f"\n... y {len(result) - 20} más"
                else:
                    result_str = str(result)
                
                # Limitar longitud para display
                display_result = result_str[:200] + "..." if len(result_str) > 200 else result_str
                print(f"✓ Resultado: {display_result}\n")
                
                # Agregar resultado al historial
                self.history.append({
                    "role": "tool",
                    "content": result_str
                })
        
        # Si llegamos al límite de iteraciones
        final_response = "He completado las acciones solicitadas."
        self.history.append({
            "role": "assistant",
            "content": final_response
        })
        return final_response
    
    def reset_conversation(self):
        """Reinicia el historial de conversación."""
        self.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT
        }]
        print("💭 Conversación reiniciada")