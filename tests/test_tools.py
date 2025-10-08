"""
Tests para las herramientas y utilidades
"""

import unittest
import os
import tempfile
import json
from utils.validators import (
    validate_file_path,
    validate_directory_path,
    validate_command,
    validate_model_name,
    validate_url,
    validate_port,
    validate_file_extension,
    validate_json_string,
    validate_config,
    sanitize_input
)
from utils.formatters import (
    format_code,
    format_response,
    format_error,
    format_table,
    truncate_text
)
from utils.colors import Colors, colorize


class TestValidators(unittest.TestCase):
    """Tests para los validadores"""
    
    def test_validate_file_path_valid(self):
        """Test de validación de ruta de archivo válida"""
        valid, error = validate_file_path("main.py")
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    def test_validate_file_path_empty(self):
        """Test de validación de ruta vacía"""
        valid, error = validate_file_path("")
        self.assertFalse(valid)
        self.assertNotEqual(error, "")
    
    def test_validate_file_path_invalid_chars(self):
        """Test de validación con caracteres inválidos"""
        valid, error = validate_file_path("archivo<invalido>.py")
        self.assertFalse(valid)
        self.assertIn("inválidos", error)
    
    def test_validate_directory_path_valid(self):
        """Test de validación de directorio válido"""
        valid, error = validate_directory_path("./utils")
        self.assertTrue(valid)
    
    def test_validate_command_valid(self):
        """Test de validación de comando válido"""
        valid, error = validate_command("ls -la")
        self.assertTrue(valid)
    
    def test_validate_command_dangerous(self):
        """Test de validación de comando peligroso"""
        valid, error = validate_command("rm -rf /")
        self.assertFalse(valid)
        self.assertIn("peligroso", error)
    
    def test_validate_command_sudo_rm(self):
        """Test de validación de sudo rm"""
        valid, error = validate_command("sudo rm archivo.txt")
        self.assertFalse(valid)
    
    def test_validate_model_name_valid(self):
        """Test de validación de nombre de modelo válido"""
        valid, error = validate_model_name("llama3.2:latest")
        self.assertTrue(valid)
    
    def test_validate_model_name_without_tag(self):
        """Test de validación de modelo sin tag"""
        valid, error = validate_model_name("llama3.2")
        self.assertTrue(valid)
    
    def test_validate_model_name_invalid(self):
        """Test de validación de nombre de modelo inválido"""
        valid, error = validate_model_name("Modelo Inválido!")
        self.assertFalse(valid)
    
    def test_validate_url_valid(self):
        """Test de validación de URL válida"""
        valid, error = validate_url("http://localhost:11434")
        self.assertTrue(valid)
    
    def test_validate_url_https(self):
        """Test de validación de URL HTTPS"""
        valid, error = validate_url("https://api.example.com")
        self.assertTrue(valid)
    
    def test_validate_url_invalid(self):
        """Test de validación de URL inválida"""
        valid, error = validate_url("esto no es una url")
        self.assertFalse(valid)
    
    def test_validate_port_valid(self):
        """Test de validación de puerto válido"""
        valid, error = validate_port(8080)
        self.assertTrue(valid)
    
    def test_validate_port_string(self):
        """Test de validación de puerto como string"""
        valid, error = validate_port("5000")
        self.assertTrue(valid)
    
    def test_validate_port_invalid_low(self):
        """Test de validación de puerto muy bajo"""
        valid, error = validate_port(0)
        self.assertFalse(valid)
    
    def test_validate_port_invalid_high(self):
        """Test de validación de puerto muy alto"""
        valid, error = validate_port(99999)
        self.assertFalse(valid)
    
    def test_validate_port_reserved(self):
        """Test de validación de puerto reservado"""
        valid, error = validate_port(80)
        self.assertTrue(valid)
        self.assertIn("reservado", error)
    
    def test_validate_file_extension_valid(self):
        """Test de validación de extensión válida"""
        valid, error = validate_file_extension("script.py", [".py", ".pyw"])
        self.assertTrue(valid)
    
    def test_validate_file_extension_invalid(self):
        """Test de validación de extensión inválida"""
        valid, error = validate_file_extension("archivo.txt", [".py"])
        self.assertFalse(valid)
    
    def test_validate_file_extension_no_extension(self):
        """Test de validación sin extensión"""
        valid, error = validate_file_extension("archivo", [".py"])
        self.assertFalse(valid)
    
    def test_validate_json_string_valid(self):
        """Test de validación de JSON válido"""
        json_str = '{"key": "value", "number": 123}'
        valid, error = validate_json_string(json_str)
        self.assertTrue(valid)
    
    def test_validate_json_string_invalid(self):
        """Test de validación de JSON inválido"""
        json_str = '{esto no es json válido}'
        valid, error = validate_json_string(json_str)
        self.assertFalse(valid)
    
    def test_validate_config_valid(self):
        """Test de validación de configuración válida"""
        config = {"model": "llama3.2", "port": 11434}
        required = ["model", "port"]
        valid, error = validate_config(config, required)
        self.assertTrue(valid)
    
    def test_validate_config_missing_keys(self):
        """Test de validación de configuración con claves faltantes"""
        config = {"model": "llama3.2"}
        required = ["model", "port", "host"]
        valid, error = validate_config(config, required)
        self.assertFalse(valid)
        self.assertIn("port", error)
    
    def test_sanitize_input_normal(self):
        """Test de sanitización de entrada normal"""
        sanitized = sanitize_input("Hola mundo")
        self.assertEqual(sanitized, "Hola mundo")
    
    def test_sanitize_input_with_control_chars(self):
        """Test de sanitización con caracteres de control"""
        sanitized = sanitize_input("Hola\x00mundo\x1f")
        self.assertNotIn("\x00", sanitized)
        self.assertNotIn("\x1f", sanitized)
    
    def test_sanitize_input_too_long(self):
        """Test de sanitización de entrada muy larga"""
        long_input = "a" * 2000
        sanitized = sanitize_input(long_input, max_length=1000)
        self.assertEqual(len(sanitized), 1000)
    
    def test_sanitize_input_whitespace(self):
        """Test de sanitización de espacios"""
        sanitized = sanitize_input("  texto con espacios  ")
        self.assertEqual(sanitized, "texto con espacios")


class TestFormatters(unittest.TestCase):
    """Tests para los formateadores"""
    
    def test_format_code_simple(self):
        """Test de formateo de código simple"""
        code = "def hello():\n    print('Hola')"
        formatted = format_code(code)
        
        self.assertIn("hello", formatted)
        self.assertIn("print", formatted)
    
    def test_format_code_with_line_numbers(self):
        """Test de formateo con números de línea"""
        code = "line1\nline2\nline3"
        formatted = format_code(code)
        
        # Debería tener números de línea
        self.assertIn("1", formatted)
        self.assertIn("2", formatted)
        self.assertIn("3", formatted)
    
    def test_format_response_plain_text(self):
        """Test de formateo de respuesta de texto plano"""
        response = "Esta es una respuesta simple"
        formatted = format_response(response)
        
        self.assertIn("respuesta simple", formatted)
    
    def test_format_response_with_code_block(self):
        """Test de formateo de respuesta con bloque de código"""
        response = "Aquí está el código:\n```python\nprint('test')\n```"
        formatted = format_response(response)
        
        self.assertIn("print", formatted)
    
    def test_format_error_simple(self):
        """Test de formateo de error simple"""
        error = "Error: Archivo no encontrado"
        formatted = format_error(error)
        
        self.assertIn("Error", formatted)
        self.assertIn("Archivo no encontrado", formatted)
    
    def test_format_error_multiline(self):
        """Test de formateo de error multilínea"""
        error = "Error:\nLínea 1\nLínea 2"
        formatted = format_error(error)
        
        self.assertIn("Línea 1", formatted)
        self.assertIn("Línea 2", formatted)
    
    def test_format_table_simple(self):
        """Test de formateo de tabla simple"""
        headers = ["Nombre", "Edad"]
        rows = [["Juan", "30"], ["María", "25"]]
        
        table = format_table(headers, rows)
        
        self.assertIn("Nombre", table)
        self.assertIn("Edad", table)
        self.assertIn("Juan", table)
        self.assertIn("María", table)
    
    def test_format_table_empty(self):
        """Test de formateo de tabla vacía"""
        headers = ["Col1", "Col2"]
        rows = []
        
        table = format_table(headers, rows)
        
        self.assertIn("Col1", table)
        self.assertIn("Col2", table)
    
    def test_truncate_text_short(self):
        """Test de truncamiento de texto corto"""
        text = "Texto corto"
        truncated = truncate_text(text, max_length=100)
        
        self.assertEqual(text, truncated)
    
    def test_truncate_text_long(self):
        """Test de truncamiento de texto largo"""
        text = "a" * 200
        truncated = truncate_text(text, max_length=50)
        
        self.assertEqual(len(truncated), 50)
        self.assertTrue(truncated.endswith("..."))
    
    def test_truncate_text_custom_suffix(self):
        """Test de truncamiento con sufijo personalizado"""
        text = "a" * 100
        truncated = truncate_text(text, max_length=20, suffix="[...]")
        
        self.assertTrue(truncated.endswith("[...]"))


class TestColors(unittest.TestCase):
    """Tests para el sistema de colores"""
    
    def test_colorize_simple(self):
        """Test de colorización simple"""
        colored = colorize("Test", Colors.RED)
        
        self.assertIn("Test", colored)
        self.assertIn(Colors.RED, colored)
        self.assertIn(Colors.RESET, colored)
    
    def test_colorize_with_style(self):
        """Test de colorización con estilo"""
        colored = colorize("Test", Colors.GREEN, Colors.BOLD)
        
        self.assertIn(Colors.GREEN, colored)
        self.assertIn(Colors.BOLD, colored)
    
    def test_colorize_with_background(self):
        """Test de colorización con fondo"""
        colored = colorize("Test", Colors.WHITE, bg_color=Colors.BG_BLUE)
        
        self.assertIn(Colors.WHITE, colored)
        self.assertIn(Colors.BG_BLUE, colored)
    
    def test_colors_class_attributes(self):
        """Test de atributos de la clase Colors"""
        self.assertIsNotNone(Colors.RED)
        self.assertIsNotNone(Colors.GREEN)
        self.assertIsNotNone(Colors.BLUE)
        self.assertIsNotNone(Colors.YELLOW)
        self.assertIsNotNone(Colors.BOLD)
        self.assertIsNotNone(Colors.RESET)


class TestFileOperations(unittest.TestCase):
    """Tests para operaciones con archivos"""
    
    def setUp(self):
        """Crear archivo temporal para tests"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py')
        self.temp_file.write("print('Hello World')")
        self.temp_file.close()
    
    def tearDown(self):
        """Eliminar archivo temporal"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_file_exists(self):
        """Test de existencia de archivo"""
        self.assertTrue(os.path.exists(self.temp_file.name))
    
    def test_file_extension(self):
        """Test de extensión de archivo"""
        _, ext = os.path.splitext(self.temp_file.name)
        self.assertEqual(ext, '.py')
    
    def test_read_file_content(self):
        """Test de lectura de contenido"""
        with open(self.temp_file.name, 'r') as f:
            content = f.read()
        
        self.assertIn("Hello World", content)


def run_tests():
    """Ejecuta todos los tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()