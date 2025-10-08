"""
parsers/command_parser.py
Parser de comandos para PatCode
"""

import re
from typing import Dict, Any, Optional, List


class CommandParser:
    """
    Parser para interpretar comandos del usuario
    Identifica comandos especiales y extrae parámetros
    """
    
    def __init__(self):
        """Inicializa el parser con comandos conocidos"""
        self.commands = {
            "/help": self._parse_help,
            "/clear": self._parse_clear,
            "/exit": self._parse_exit,
            "/quit": self._parse_exit,
            "/tools": self._parse_tools,
            "/history": self._parse_history,
            "/reset": self._parse_reset,
            "/context": self._parse_context,
            "/analyze": self._parse_analyze,
            "/read": self._parse_read,
            "/write": self._parse_write,
            "/list": self._parse_list,
            "/run": self._parse_run,
            "/search": self._parse_search,
        }
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parsea el texto de entrada
        
        Args:
            text: Texto a parsear
            
        Returns:
            Dict con:
                - type: 'command' o 'query'
                - command: nombre del comando (si es comando)
                - params: parámetros del comando
                - original: texto original
        """
        text = text.strip()
        
        if not text:
            return {
                "type": "empty",
                "original": text
            }
        
        # Verificar si es un comando
        if text.startswith('/'):
            return self._parse_command(text)
        
        # Si no es comando, es una query normal
        return {
            "type": "query",
            "text": text,
            "original": text
        }
    
    def _parse_command(self, text: str) -> Dict[str, Any]:
        """Parsea un comando específico"""
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Buscar handler del comando
        if command in self.commands:
            result = self.commands[command](args)
            result["original"] = text
            return result
        
        # Comando no reconocido
        return {
            "type": "command",
            "command": "unknown",
            "params": {"text": args},
            "original": text
        }
    
    def _parse_help(self, args: str) -> Dict[str, Any]:
        """Parsea comando /help"""
        return {
            "type": "command",
            "command": "help",
            "params": {"topic": args.strip() if args else None}
        }
    
    def _parse_clear(self, args: str) -> Dict[str, Any]:
        """Parsea comando /clear"""
        return {
            "type": "command",
            "command": "clear",
            "params": {}
        }
    
    def _parse_exit(self, args: str) -> Dict[str, Any]:
        """Parsea comando /exit o /quit"""
        return {
            "type": "command",
            "command": "exit",
            "params": {}
        }
    
    def _parse_tools(self, args: str) -> Dict[str, Any]:
        """Parsea comando /tools"""
        return {
            "type": "command",
            "command": "tools",
            "params": {"category": args.strip() if args else None}
        }
    
    def _parse_history(self, args: str) -> Dict[str, Any]:
        """Parsea comando /history"""
        limit = 10
        if args.strip().isdigit():
            limit = int(args.strip())
        
        return {
            "type": "command",
            "command": "history",
            "params": {"limit": limit}
        }
    
    def _parse_reset(self, args: str) -> Dict[str, Any]:
        """Parsea comando /reset"""
        return {
            "type": "command",
            "command": "reset",
            "params": {}
        }
    
    def _parse_context(self, args: str) -> Dict[str, Any]:
        """Parsea comando /context"""
        return {
            "type": "command",
            "command": "context",
            "params": {}
        }
    
    def _parse_analyze(self, args: str) -> Dict[str, Any]:
        """Parsea comando /analyze <file>"""
        return {
            "type": "command",
            "command": "analyze",
            "params": {"file_path": args.strip()}
        }
    
    def _parse_read(self, args: str) -> Dict[str, Any]:
        """Parsea comando /read <file>"""
        return {
            "type": "command",
            "command": "read_file",
            "params": {"file_path": args.strip()}
        }
    
    def _parse_write(self, args: str) -> Dict[str, Any]:
        """Parsea comando /write <file> <content>"""
        parts = args.split(maxsplit=1)
        file_path = parts[0] if parts else ""
        content = parts[1] if len(parts) > 1 else ""
        
        return {
            "type": "command",
            "command": "write_file",
            "params": {
                "file_path": file_path,
                "content": content
            }
        }
    
    def _parse_list(self, args: str) -> Dict[str, Any]:
        """Parsea comando /list [directory]"""
        return {
            "type": "command",
            "command": "list_directory",
            "params": {"directory": args.strip() if args else "."}
        }
    
    def _parse_run(self, args: str) -> Dict[str, Any]:
        """Parsea comando /run <command>"""
        return {
            "type": "command",
            "command": "execute_command",
            "params": {"command": args.strip()}
        }
    
    def _parse_search(self, args: str) -> Dict[str, Any]:
        """Parsea comando /search <pattern>"""
        return {
            "type": "command",
            "command": "search_files",
            "params": {"pattern": args.strip()}
        }
    
    def is_command(self, text: str) -> bool:
        """
        Verifica si el texto es un comando
        
        Args:
            text: Texto a verificar
            
        Returns:
            True si es comando, False si no
        """
        return text.strip().startswith('/')
    
    def list_commands(self) -> List[str]:
        """
        Retorna lista de comandos disponibles
        
        Returns:
            Lista de nombres de comandos
        """
        return list(self.commands.keys())
    
    def get_command_help(self, command: str) -> Optional[str]:
        """
        Obtiene ayuda para un comando específico
        
        Args:
            command: Nombre del comando
            
        Returns:
            String de ayuda o None
        """
        help_texts = {
            "/help": "Muestra ayuda general o de un comando específico",
            "/clear": "Limpia la pantalla",
            "/exit": "Sale del programa",
            "/quit": "Sale del programa",
            "/tools": "Lista herramientas disponibles",
            "/history": "Muestra historial de conversación",
            "/reset": "Reinicia la memoria del agente",
            "/context": "Muestra información del proyecto actual",
            "/analyze": "Analiza un archivo específico",
            "/read": "Lee el contenido de un archivo",
            "/write": "Escribe contenido en un archivo",
            "/list": "Lista archivos en un directorio",
            "/run": "Ejecuta un comando de shell",
            "/search": "Busca archivos por patrón",
        }
        return help_texts.get(command)
    
    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Extrae bloques de código del texto (formato markdown)
        
        Args:
            text: Texto que puede contener bloques de código
            
        Returns:
            Lista de diccionarios con 'language' y 'code'
        """
        code_blocks = []
        
        # Patrón para bloques de código markdown: ```language\ncode\n```
        pattern = r'```(\w*)\n(.*?)\n```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2)
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks
    
    def extract_file_paths(self, text: str) -> List[str]:
        """
        Extrae rutas de archivos del texto
        
        Args:
            text: Texto que puede contener rutas
            
        Returns:
            Lista de rutas encontradas
        """
        paths = []
        
        # Patrones comunes de rutas
        patterns = [
            r'["\']([^"\']+\.[a-zA-Z]{2,4})["\']',  # "file.py" o 'file.js'
            r'`([^`]+\.[a-zA-Z]{2,4})`',            # `file.py`
            r'\b([\w/\\.-]+\.[a-zA-Z]{2,4})\b',     # file.py o path/to/file.js
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                path = match.group(1)
                if path not in paths:
                    paths.append(path)
        
        return paths