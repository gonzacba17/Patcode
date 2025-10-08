"""
Parser para extraer y procesar llamadas a herramientas
"""
import re
import json
from typing import Optional, Dict, Any, List


class ToolParser:
    """
    Parser inteligente que detecta cuando el modelo quiere usar herramientas
    Soporta múltiples formatos de tool calls
    """
    
    # Patrones regex para diferentes formatos
    JSON_PATTERN = r'\{[^}]*"tool":\s*"([^"]+)"[^}]*\}'
    XML_PATTERN = r'<tool_call>\s*<tool>([^<]+)</tool>.*?</tool_call>'
    FUNCTION_PATTERN = r'(\w+)\((.*?)\)'
    
    @staticmethod
    def extract_tool_call(text: str) -> Optional[Dict[str, Any]]:
        """
        Intenta extraer una llamada a herramienta del texto del modelo
        
        Soporta múltiples formatos:
        - JSON: {"tool": "read_file", "arguments": {"path": "main.py"}}
        - XML: <tool_call><tool>read_file</tool><path>main.py</path></tool_call>
        - Function: read_file(path="main.py")
        
        Args:
            text: Texto generado por el modelo
            
        Returns:
            Dict con 'tool', 'arguments' y 'thought' o None si no encuentra
        """
        
        # 1. Intentar formato JSON (preferido)
        json_result = ToolParser._parse_json_format(text)
        if json_result:
            return json_result
        
        # 2. Intentar formato XML
        xml_result = ToolParser._parse_xml_format(text)
        if xml_result:
            return xml_result
        
        # 3. Intentar formato de función
        func_result = ToolParser._parse_function_format(text)
        if func_result:
            return func_result
        
        return None
    
    @staticmethod
    def _parse_json_format(text: str) -> Optional[Dict[str, Any]]:
        """Parsea formato JSON"""
        try:
            # Buscar objeto JSON en el texto
            json_match = re.search(ToolParser.JSON_PATTERN, text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                return {
                    "tool": data.get("tool"),
                    "arguments": data.get("arguments", data.get("args", {})),
                    "thought": data.get("thought", data.get("reasoning", ""))
                }
        except (json.JSONDecodeError, KeyError):
            pass
        
        return None
    
    @staticmethod
    def _parse_xml_format(text: str) -> Optional[Dict[str, Any]]:
        """Parsea formato XML"""
        try:
            xml_match = re.search(ToolParser.XML_PATTERN, text, re.DOTALL | re.IGNORECASE)
            if xml_match:
                tool_name = xml_match.group(1).strip()
                full_match = xml_match.group(0)
                
                # Extraer argumentos de tags XML
                args = {}
                arg_pattern = r'<(\w+)>([^<]+)</\1>'
                for match in re.finditer(arg_pattern, full_match):
                    arg_name = match.group(1)
                    arg_value = match.group(2).strip()
                    if arg_name not in ['tool', 'tool_call']:
                        args[arg_name] = arg_value
                
                return {
                    "tool": tool_name,
                    "arguments": args,
                    "thought": ""
                }
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def _parse_function_format(text: str) -> Optional[Dict[str, Any]]:
        """Parsea formato de función Python"""
        try:
            # Buscar patrones como: tool_name(arg1="val1", arg2="val2")
            func_match = re.search(ToolParser.FUNCTION_PATTERN, text)
            if func_match:
                tool_name = func_match.group(1)
                args_str = func_match.group(2)
                
                # Parsear argumentos
                args = {}
                if args_str:
                    # Dividir por comas respetando strings
                    parts = []
                    current = ""
                    in_string = False
                    
                    for char in args_str:
                        if char in ['"', "'"]:
                            in_string = not in_string
                        elif char == ',' and not in_string:
                            parts.append(current.strip())
                            current = ""
                            continue
                        current += char
                    
                    if current.strip():
                        parts.append(current.strip())
                    
                    # Procesar cada parte
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            args[key] = value
                
                return {
                    "tool": tool_name,
                    "arguments": args,
                    "thought": ""
                }
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def should_use_tool(text: str, available_tools: List[str] = None) -> bool:
        """
        Determina si el texto indica que se debería usar una herramienta
        
        Args:
            text: Texto del modelo
            available_tools: Lista de herramientas disponibles (opcional)
            
        Returns:
            True si el texto sugiere uso de herramientas
        """
        text_lower = text.lower()
        
        # 1. Menciones explícitas de herramientas
        if available_tools:
            for tool in available_tools:
                if tool.lower() in text_lower:
                    return True
        
        # 2. Palabras clave que indican acciones con archivos
        action_indicators = [
            # Lectura
            r'\b(leer|ver|mostrar|abrir|revisar|consultar)\s+(el\s+)?(archivo|código)',
            r'\b(necesito|voy a|debo)\s+(ver|leer|revisar)',
            
            # Escritura
            r'\b(escribir|crear|guardar|generar|modificar)\s+(un\s+)?(archivo|código)',
            r'\b(voy a crear|crearemos|generaremos)',
            
            # Listado
            r'\b(listar|mostrar|ver)\s+(los\s+)?(archivos|carpetas|directorio)',
            r'\b(qué archivos|cuáles archivos)',
            
            # Ejecución
            r'\b(ejecutar|correr|run|compilar)\s+',
            
            # Búsqueda
            r'\b(buscar|encontrar|search|grep)\s+',
            
            # Frases indicativas
            r'primero\s+(veo|leo|reviso|verifico)',
            r'déjame\s+(ver|revisar|leer)',
        ]
        
        for pattern in action_indicators:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    @staticmethod
    def extract_file_path(text: str) -> Optional[str]:
        """
        Intenta extraer una ruta de archivo mencionada en el texto
        
        Args:
            text: Texto donde buscar la ruta
            
        Returns:
            Ruta del archivo o None
        """
        # Extensiones de archivo comunes
        extensions = r'(py|js|ts|jsx|tsx|java|cpp|c|h|hpp|cs|rb|php|go|rs|swift|kt|' \
                    r'json|yaml|yml|xml|html|css|scss|sass|md|txt|sh|bash|sql)'
        
        # Patrones para detectar rutas
        patterns = [
            # Entre comillas: "path/to/file.py"
            rf'["\']([^"\']+\.{extensions})["\']',
            
            # Sin comillas: path/to/file.py
            rf'\b([a-zA-Z0-9_/.-]+\.{extensions})\b',
            
            # Después de "archivo": archivo main.py
            rf'archivo\s+["\']?([^"\'\\s]+\.{extensions})["\']?',
            
            # Después de palabras clave
            rf'(?:leer|ver|abrir|escribir|crear|modificar)\s+["\']?([^"\'\\s]+\.{extensions})["\']?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # El grupo 1 contiene la ruta
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_directory_path(text: str) -> Optional[str]:
        """
        Intenta extraer una ruta de directorio mencionada en el texto
        
        Args:
            text: Texto donde buscar la ruta
            
        Returns:
            Ruta del directorio o None
        """
        patterns = [
            # Entre comillas
            r'["\']([^"\']+/)["\']',
            
            # Después de palabras clave
            r'(?:carpeta|directorio|folder)\s+["\']?([^"\'\\s]+)["\']?',
            
            # Ruta relativa
            r'\b(\./[a-zA-Z0-9_/-]+)\b',
            r'\b(\.\./[a-zA-Z0-9_/-]+)\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                path = match.group(1)
                # Asegurar que termine en /
                if not path.endswith('/'):
                    path += '/'
                return path
        
        return None
    
    @staticmethod
    def is_confirmation_needed(text: str) -> bool:
        """
        Determina si el modelo está pidiendo confirmación antes de actuar
        
        Args:
            text: Texto del modelo
            
        Returns:
            True si detecta que pide confirmación
        """
        confirmation_patterns = [
            r'\b(querés|quieres|deseas)\s+que',
            r'\b(confirmar|confirmás|confirmas)\b',
            r'\b(seguir adelante|proceder|continuar)\b',
            r'\bte parece\b',
            r'\bestás de acuerdo\b',
            r'\b(ok|okay)\s*\?',
        ]
        
        text_lower = text.lower()
        for pattern in confirmation_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False