# agents/tool_agent.py
import requests
import json

class ToolAgent:
    """Agente con capacidad de usar herramientas"""
    
    def __init__(self, model="llama3.2:latest"):
        self.model = model
        self.tools = self._register_tools()
    
    def _register_tools(self):
        """Registra todas las herramientas disponibles"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Lee el contenido de un archivo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta del archivo a leer"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edita una parte de un archivo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "old_content": {"type": "string"},
                            "new_content": {"type": "string"}
                        },
                        "required": ["path", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Ejecuta un comando de terminal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
    
    def ask(self, prompt: str):
        """Envía prompt con herramientas disponibles"""
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "tools": self.tools,
                "stream": False
            }
        )
        
        result = response.json()
        message = result['message']
        
        # Si el modelo quiere usar una herramienta
        if 'tool_calls' in message:
            for tool_call in message['tool_calls']:
                function_name = tool_call['function']['name']
                arguments = tool_call['function']['arguments']
                
                # Ejecutar la herramienta
                result = self._execute_tool(function_name, arguments)
                
                # Continuar la conversación con el resultado
                return self._continue_with_result(prompt, result)
        
        return message['content']
    
    def _execute_tool(self, function_name: str, arguments: dict):
        """Ejecuta una herramienta específica"""
        from tools.file_operations import FileOperations
        from tools.shell_operations import ShellOperations
        
        if function_name == "read_file":
            return FileOperations.read_file(arguments['path'])
        elif function_name == "edit_file":
            return FileOperations.edit_file(
                arguments['path'],
                arguments['old_content'],
                arguments['new_content']
            )
        elif function_name == "run_command":
            stdout, stderr, code = ShellOperations.run_command(arguments['command'])
            return f"Output: {stdout}\nError: {stderr}\nCode: {code}"