"""
Tests para el parser de comandos
"""

import unittest
import os
import tempfile
from parsers.command_parser import CommandParser


class TestCommandParser(unittest.TestCase):
    """Tests para la clase CommandParser"""
    
    def setUp(self):
        """Configuración antes de cada test"""
        self.parser = CommandParser()
    
    def test_initialization(self):
        """Test de inicialización del parser"""
        self.assertIsNotNone(self.parser)
        self.assertIsInstance(self.parser.commands, dict)
    
    def test_parse_simple_command(self):
        """Test de parseo de comando simple"""
        result = self.parser.parse("ayuda")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['command'], 'ayuda')
        self.assertEqual(result['args'], [])
    
    def test_parse_command_with_args(self):
        """Test de parseo de comando con argumentos"""
        result = self.parser.parse("leer archivo.py")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['command'], 'leer')
        self.assertIn('archivo.py', result['args'])
    
    def test_parse_command_with_multiple_args(self):
        """Test de parseo de comando con múltiples argumentos"""
        result = self.parser.parse("comparar archivo1.py archivo2.py")
        
        self.assertEqual(result['command'], 'comparar')
        self.assertEqual(len(result['args']), 2)
        self.assertIn('archivo1.py', result['args'])
        self.assertIn('archivo2.py', result['args'])
    
    def test_parse_empty_input(self):
        """Test de parseo de entrada vacía"""
        result = self.parser.parse("")
        
        self.assertIsNone(result)
    
    def test_parse_whitespace_only(self):
        """Test de parseo de solo espacios"""
        result = self.parser.parse("   ")
        
        self.assertIsNone(result)
    
    def test_parse_unknown_command(self):
        """Test de parseo de comando desconocido"""
        result = self.parser.parse("comandoinexistente")
        
        # Debería ser tratado como texto normal, no como comando
        self.assertIsNotNone(result)
    
    def test_parse_case_insensitive(self):
        """Test de parseo case-insensitive"""
        result1 = self.parser.parse("AYUDA")
        result2 = self.parser.parse("ayuda")
        result3 = self.parser.parse("AyUdA")
        
        self.assertEqual(result1['command'].lower(), result2['command'].lower())
        self.assertEqual(result2['command'].lower(), result3['command'].lower())
    
    def test_parse_with_quotes(self):
        """Test de parseo con comillas"""
        result = self.parser.parse('leer "archivo con espacios.py"')
        
        self.assertEqual(result['command'], 'leer')
        self.assertIn('archivo con espacios.py', ' '.join(result['args']))
    
    def test_parse_with_path(self):
        """Test de parseo con rutas de archivos"""
        result = self.parser.parse("leer /home/user/proyecto/main.py")
        
        self.assertEqual(result['command'], 'leer')
        self.assertIn('/home/user/proyecto/main.py', result['args'])
    
    def test_parse_with_special_chars(self):
        """Test de parseo con caracteres especiales"""
        result = self.parser.parse("buscar función_especial-123")
        
        self.assertIsNotNone(result)
        self.assertIn('función_especial-123', result['args'])
    
    def test_parse_multiline(self):
        """Test de parseo de entrada multilínea"""
        multiline_input = """explicar
        este código
        en detalle"""
        
        result = self.parser.parse(multiline_input)
        
        self.assertIsNotNone(result)
    
    def test_extract_code_blocks(self):
        """Test de extracción de bloques de código"""
        text = """
        Aquí está el código:
```python
        def hello():
            print("Hola")
    ¿Qué te parece?
    """
    
    code_blocks = self.parser.extract_code_blocks(text)
    
    self.assertGreater(len(code_blocks), 0)
    self.assertIn('def hello()', code_blocks[0])

    def test_extract_multiple_code_blocks(self):
        """Test de extracción de múltiples bloques de código"""
        text = """
        Primer bloque:
python        print("Uno")
        Segundo bloque:
javascript        console.log("Dos");
        """
        
        code_blocks = self.parser.extract_code_blocks(text)
        
        self.assertEqual(len(code_blocks), 2)

def test_extract_language_from_code_block(self):
    """Test de extracción del lenguaje del bloque de código"""
    text = "```python\nprint('test')\n```"
    
    result = self.parser.extract_code_blocks(text, include_language=True)
    
    self.assertIsNotNone(result)
    if len(result) > 0:
        lang_check = str(result[0]).lower() if isinstance(result[0], dict) else ''
        self.assertIn('python', lang_check)

def test_is_question(self):
    """Test de detección de preguntas"""
    questions = [
        "¿Qué es Python?",
        "Cómo funciona esto?",
        "Por qué da error",
        "¿Puedes ayudarme?"
    ]
    
    for question in questions:
        result = self.parser.is_question(question)
        msg = f"'{question}' debería ser detectada como pregunta"
        self.assertTrue(result, msg)

def test_is_not_question(self):
    """Test de detección de no-preguntas"""
    statements = [
        "Esto es una afirmación",
        "Ejecuta el código",
        "Muestra el resultado"
    ]
    
    for statement in statements:
        result = self.parser.is_question(statement)
        msg = f"'{statement}' no debería ser detectada como pregunta"
        self.assertFalse(result, msg)

def test_extract_file_paths(self):
    """Test de extracción de rutas de archivos"""
    text = "Lee el archivo main.py y utils/helpers.py"
    
    paths = self.parser.extract_file_paths(text)
    
    self.assertGreater(len(paths), 0)
    self.assertTrue(any('main.py' in path for path in paths))

def test_sanitize_input(self):
    """Test de sanitización de entrada"""
    dangerous_input = "comando && rm -rf /"
    
    sanitized = self.parser.sanitize_input(dangerous_input)
    
    # Debería remover o escapar comandos peligrosos
    self.assertNotIn('rm -rf', sanitized)

def test_parse_flags(self):
    """Test de parseo de flags"""
    result = self.parser.parse("ejecutar --verbose --debug script.py")
    
    self.assertEqual(result['command'], 'ejecutar')
    # Verificar que los flags fueron parseados
    has_verbose = any('--verbose' in str(arg) for arg in result['args'])
    self.assertTrue(has_verbose)
class TestCommandParserEdgeCases(unittest.TestCase):
    """Tests de casos extremos para CommandParser"""

    def setUp(self):
        """Configuración antes de cada test"""
        self.parser = CommandParser()

    def test_very_long_input(self):
        """Test con entrada muy larga"""
        long_input = "a" * 10000
        
        result = self.parser.parse(long_input)
        
        # Debería manejar entrada larga sin crashear
        self.assertIsNotNone(result)

    def test_special_unicode_characters(self):
        """Test con caracteres Unicode especiales"""
        unicode_input = "buscar función_española 你好 مرحبا"
        
        result = self.parser.parse(unicode_input)
        
        self.assertIsNotNone(result)

    def test_malformed_quotes(self):
        """Test con comillas mal formadas"""
        malformed = 'leer "archivo sin cerrar'
        
        result = self.parser.parse(malformed)
        
        # Debería manejar el error gracefully
        self.assertIsNotNone(result)

    def test_only_special_characters(self):
        """Test con solo caracteres especiales"""
        special = "!@#$%^&*()"
        
        result = self.parser.parse(special)
        
        self.assertIsNotNone(result)

    def test_mixed_languages(self):
        """Test con mezcla de idiomas"""
        mixed = "explica this código en español"
        
        result = self.parser.parse(mixed)
        
        self.assertIsNotNone(result)

    def test_escape_sequences(self):
        """Test con secuencias de escape"""
        escaped = "buscar \\n\\t\\r"
        
        result = self.parser.parse(escaped)
        
        self.assertIsNotNone(result)
def run_tests():
    """Ejecuta todos los tests"""
    unittest.main()
if name == 'main':
    run_tests()