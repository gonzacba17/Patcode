"""
Sistema de Tool Calling para PatCode
Permite que el LLM decida automáticamente qué funciones ejecutar
"""
import json
import subprocess
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
import re

class Tool:
    """Representa una herramienta que el LLM puede invocar"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function
    
    def to_dict(self) -> Dict:
        """Convierte la herramienta a formato para el LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Ejecuta la herramienta con los parámetros dados"""
        try:
            result = self.function(**kwargs)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class ToolRegistry:
    """Registro de herramientas disponibles para el LLM"""
    
    def __init__(self, file_manager=None):
        self.tools: Dict[str, Tool] = {}
        self.file_manager = file_manager
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Registra herramientas por defecto"""
        
        # Tool: Leer archivo
        self.register(Tool(
            name="read_file",
            description="Lee el contenido de un archivo del proyecto. Usa esto cuando necesites ver el código de un archivo específico.",
            parameters={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Ruta del archivo a leer (ej: 'main.py', 'src/utils.py')"
                    }
                },
                "required": ["filepath"]
            },
            function=self._read_file
        ))
        
        # Tool: Listar archivos
        self.register(Tool(
            name="list_files",
            description="Lista archivos del proyecto que coincidan con un patrón. Útil para explorar la estructura del proyecto.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Patrón glob (ej: '*.py', 'src/**/*.js')",
                        "default": "*"
                    }
                },
                "required": []
            },
            function=self._list_files
        ))
        
        # Tool: Buscar en archivos
        self.register(Tool(
            name="search_in_files",
            description="Busca un texto o patrón en los archivos del proyecto. Útil para encontrar dónde se usa una función o variable.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto o patrón regex a buscar"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Patrón de archivos donde buscar (ej: '*.py')",
                        "default": "*.py"
                    }
                },
                "required": ["query"]
            },
            function=self._search_in_files
        ))
        
        # Tool: Ejecutar comando
        self.register(Tool(
            name="run_command",
            description="Ejecuta un comando del sistema (pytest, black, ruff, etc). Solo comandos seguros preaprobados.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Comando a ejecutar (ej: 'pytest tests/', 'black main.py')"
                    }
                },
                "required": ["command"]
            },
            function=self._run_command
        ))
        
        # Tool: Analizar proyecto
        self.register(Tool(
            name="analyze_project",
            description="Analiza la estructura completa del proyecto: archivos, líneas de código, lenguajes, dependencias.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            function=self._analyze_project
        ))
        
        # Tool: Escribir archivo
        self.register(Tool(
            name="write_file",
            description="Crea o modifica un archivo. IMPORTANTE: Requiere confirmación del usuario antes de aplicar cambios.",
            parameters={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Ruta del archivo a crear/modificar"
                    },
                    "content": {
                        "type": "string",
                        "description": "Contenido completo del archivo"
                    }
                },
                "required": ["filepath", "content"]
            },
            function=self._write_file
        ))
    
    def register(self, tool: Tool):
        """Registra una nueva herramienta"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Obtiene una herramienta por nombre"""
        return self.tools.get(name)
    
    def get_tools_description(self) -> str:
        """Retorna descripción de todas las herramientas para el LLM"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(tools_list)
    
    def get_tools_json(self) -> List[Dict]:
        """Retorna herramientas en formato JSON para el LLM"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    # Implementaciones de herramientas
    
    def _read_file(self, filepath: str) -> str:
        """Lee un archivo"""
        if not self.file_manager:
            return "Error: FileManager no disponible"
        
        try:
            data = self.file_manager.read_file(filepath)
            return f"Archivo: {data['name']}\nLíneas: {data['lines']}\n\n{data['content']}"
        except Exception as e:
            return f"Error leyendo archivo: {str(e)}"
    
    def _list_files(self, pattern: str = "*") -> str:
        """Lista archivos"""
        if not self.file_manager:
            return "Error: FileManager no disponible"
        
        try:
            files = self.file_manager.list_files(pattern)
            if not files:
                return f"No se encontraron archivos con patrón: {pattern}"
            return f"Archivos encontrados ({len(files)}):\n" + "\n".join(f"  • {f}" for f in files)
        except Exception as e:
            return f"Error listando archivos: {str(e)}"
    
    def _search_in_files(self, query: str, file_pattern: str = "*.py") -> str:
        """Busca en archivos"""
        if not self.file_manager:
            return "Error: FileManager no disponible"
        
        try:
            files = self.file_manager.list_files(file_pattern)
            results = []
            
            for filepath in files:
                try:
                    data = self.file_manager.read_file(filepath)
                    content = data['content']
                    
                    # Buscar líneas que contengan el query
                    for i, line in enumerate(content.split('\n'), 1):
                        if re.search(query, line, re.IGNORECASE):
                            results.append(f"{filepath}:{i}: {line.strip()}")
                except:
                    continue
            
            if not results:
                return f"No se encontró '{query}' en archivos {file_pattern}"
            
            return f"Resultados de búsqueda para '{query}':\n" + "\n".join(results[:20])
        except Exception as e:
            return f"Error buscando: {str(e)}"
    
    def _run_command(self, command: str) -> str:
        """Ejecuta un comando del sistema"""
        # Whitelist de comandos seguros
        ALLOWED_COMMANDS = ['pytest', 'black', 'ruff', 'mypy', 'git', 'python', 'node', 'npm']
        
        cmd_parts = command.split()
        if not cmd_parts or cmd_parts[0] not in ALLOWED_COMMANDS:
            return f"Error: Comando '{cmd_parts[0] if cmd_parts else 'vacío'}' no permitido. Permitidos: {', '.join(ALLOWED_COMMANDS)}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = f"Comando: {command}\n"
            output += f"Exit code: {result.returncode}\n\n"
            
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return output
        except subprocess.TimeoutExpired:
            return f"Error: El comando tardó más de 30 segundos"
        except Exception as e:
            return f"Error ejecutando comando: {str(e)}"
    
    def _analyze_project(self) -> str:
        """Analiza el proyecto"""
        if not self.file_manager:
            return "Error: FileManager no disponible"
        
        try:
            stats = self.file_manager.analyze_project()
            
            output = "📊 Análisis del Proyecto\n"
            output += "=" * 60 + "\n"
            output += f"Total de archivos: {stats['total_files']}\n"
            output += f"Total de líneas: {stats['total_lines']:,}\n\n"
            
            output += "🗣️ Lenguajes detectados:\n"
            for lang, data in stats['languages'].items():
                output += f"  • {lang}: {data['files']} archivos, {data['lines']:,} líneas\n"
            
            output += "\n📝 Archivos por tipo:\n"
            for ext, count in stats['files_by_type'].items():
                output += f"  • {ext}: {count} archivos\n"
            
            return output
        except Exception as e:
            return f"Error analizando proyecto: {str(e)}"
    
    def _write_file(self, filepath: str, content: str) -> str:
        """Escribe un archivo (con confirmación)"""
        if not self.file_manager:
            return "Error: FileManager no disponible"
        
        try:
            success = self.file_manager.write_file(filepath, content, preview=True)
            if success:
                return f"✅ Archivo {filepath} guardado exitosamente"
            else:
                return f"❌ Usuario canceló la escritura de {filepath}"
        except Exception as e:
            return f"Error escribiendo archivo: {str(e)}"


class ToolExecutor:
    """Ejecutor de herramientas con parsing de respuestas del LLM"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def parse_tool_calls(self, llm_response: str) -> List[Dict]:
        """
        Parsea las llamadas a herramientas del LLM
        Busca patrones como: <tool>read_file(filepath="main.py")</tool>
        """
        tool_calls = []
        
        # Patrón para detectar llamadas a herramientas
        pattern = r'<tool>(\w+)\((.*?)\)</tool>'
        matches = re.findall(pattern, llm_response, re.DOTALL)
        
        for tool_name, params_str in matches:
            try:
                # Parsear parámetros (formato simple: key="value", key2="value2")
                params = {}
                param_pattern = r'(\w+)="([^"]*)"'
                param_matches = re.findall(param_pattern, params_str)
                
                for key, value in param_matches:
                    params[key] = value
                
                tool_calls.append({
                    "tool": tool_name,
                    "parameters": params
                })
            except:
                continue
        
        return tool_calls
    
    def execute_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """Ejecuta una lista de llamadas a herramientas"""
        results = []
        
        for call in tool_calls:
            tool_name = call.get("tool")
            params = call.get("parameters", {})
            
            tool = self.registry.get_tool(tool_name)
            if not tool:
                results.append({
                    "tool": tool_name,
                    "success": False,
                    "error": f"Herramienta '{tool_name}' no encontrada"
                })
                continue
            
            result = tool.execute(**params)
            result["tool"] = tool_name
            results.append(result)
        
        return results
    
    def format_results(self, results: List[Dict]) -> str:
        """Formatea los resultados para mostrar al usuario y al LLM"""
        output = "\n🔧 Resultados de herramientas:\n"
        output += "=" * 60 + "\n\n"
        
        for result in results:
            tool_name = result.get("tool", "unknown")
            output += f"Tool: {tool_name}\n"
            
            if result.get("success"):
                output += f"✅ Éxito\n"
                output += f"{result.get('result', '')}\n"
            else:
                output += f"❌ Error\n"
                output += f"{result.get('error', 'Error desconocido')}\n"
            
            output += "\n" + "-" * 60 + "\n\n"
        
        return output