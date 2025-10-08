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
        valid, error = validate_file_path("main.py")
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_file_path_empty(self):
        valid, error = validate_file_path("")
        self.assertFalse(valid)
        self.assertTrue(error)

    def test_validate_file_path_invalid_chars(self):
        valid, error = validate_file_path("archivo<invalido>.py")
        self.assertFalse(valid)
        self.assertTrue("inválido" in error.lower() or "invalid" in error.lower())

    def test_validate_directory_path_valid(self):
        valid, error = validate_directory_path("./utils")
        self.assertTrue(valid)

    def test_validate_command_valid(self):
        valid, error = validate_command("ls -la")
        self.assertTrue(valid)

    def test_validate_command_dangerous(self):
        valid, error = validate_command("rm -rf /")
        self.assertFalse(valid)
        self.assertTrue("peligroso" in error.lower() or "dangerous" in error.lower())

    def test_validate_command_sudo_rm(self):
        valid, error = validate_command("sudo rm archivo.txt")
        self.assertFalse(valid)

    def test_validate_model_name_valid(self):
        valid, error = validate_model_name("llama3.2:latest")
        self.assertTrue(valid)

    def test_validate_model_name_without_tag(self):
        valid, error = validate_model_name("llama3.2")
        self.assertTrue(valid)

    def test_validate_model_name_invalid(self):
        valid, error = validate_model_name("Modelo Inválido!")
        self.assertFalse(valid)

    def test_validate_url_valid(self):
        valid, error = validate_url("http://localhost:11434")
        self.assertTrue(valid)

    def test_validate_url_https(self):
        valid, error = validate_url("https://api.example.com")
        self.assertTrue(valid)

    def test_validate_url_invalid(self):
        valid, error = validate_url("esto no es una url")
        self.assertFalse(valid)

    def test_validate_port_valid(self):
        valid, error = validate_port(8080)
        self.assertTrue(valid)

    def test_validate_port_string(self):
        valid, error = validate_port("5000")
        self.assertTrue(valid)

    def test_validate_port_invalid_low(self):
        valid, error = validate_port(0)
        self.assertFalse(valid)

    def test_validate_port_invalid_high(self):
        valid, error = validate_port(99999)
        self.assertFalse(valid)

    def test_validate_port_reserved(self):
        valid, error = validate_port(80)
        self.assertTrue(valid)
        self.assertTrue("reservado" in error.lower() or "reserved" in error.lower())

    def test_validate_file_extension_valid(self):
        valid, error = validate_file_extension("script.py", [".py", ".pyw"])
        self.assertTrue(valid)

    def test_validate_file_extension_invalid(self):
        valid, error = validate_file_extension("archivo.txt", [".py"])
        self.assertFalse(valid)

    def test_validate_file_extension_no_extension(self):
        valid, error = validate_file_extension("archivo", [".py"])
        self.assertFalse(valid)

    def test_validate_json_string_valid(self):
        json_str = '{"key": "value", "number": 123}'
        valid, error = validate_json_string(json_str)
        self.assertTrue(valid)

    def test_validate_json_string_invalid(self):
        json_str = '{esto no es json válido}'
        valid, error = validate_json_string(json_str)
        self.assertFalse(valid)

    def test_validate_config_valid(self):
        config = {"model": "llama3.2", "port": 11434}
        required = ["model", "port"]
        valid, error = validate_config(config, required)
        self.assertTrue(valid)

    def test_validate_config_missing_keys(self):
        config = {"model": "llama3.2"}
        required = ["model", "port", "host"]
        valid, error = validate_config(config, required)
        self.assertFalse(valid)
        for key in ["port", "host"]:
            self.assertIn(key, error.lower())

    def test_sanitize_input_normal(self):
        sanitized = sanitize_input("Hola mundo")
        self.assertEqual(sanitized, "Hola mundo")

    def test_sanitize_input_with_control_chars(self):
        sanitized = sanitize_input("Hola\x00mundo\x1f")
        self.assertNotIn("\x00", sanitized)
        self.assertNotIn("\x1f", sanitized)

    def test_sanitize_input_too_long(self):
        long_input = "a" * 2000
        sanitized = sanitize_input(long_input, max_length=1000)
        self.assertEqual(len(sanitized), 1000)

    def test_sanitize_input_whitespace(self):
        sanitized = sanitize_input("  texto con espacios  ")
        self.assertEqual(sanitized, "texto con espacios")


class TestFormatters(unittest.TestCase):
    """Tests para los formateadores"""

    def test_format_code_simple(self):
        code = "def hello():\n    print('Hola')"
        formatted = format_code(code)
        self.assertIn("hello", formatted)
        self.assertIn("print", formatted)

    def test_format_code_with_line_numbers(self):
        code = "line1\nline2\nline3"
        formatted = format_code(code)
        for i in range(1, 4):
            self.assertIn(str(i), formatted)

    def test_format_response_plain_text(self):
        response = "Esta es una respuesta simple"
        formatted = format_response(response)
        self.assertIn("respuesta simple", formatted)

    def test_format_response_with_code_block(self):
        response = "Aquí está el código:\n```python\nprint('test')\n```"
        formatted = format_response(response)
        self.assertIn("print", formatted)

    def test_format_error_simple(self):
        error = "Error: Archivo no encontrado"
        formatted = format_error(error)
        self.assertIn("Error", formatted)
        self.assertIn("Archivo no encontrado", formatted)

    def test_format_error_multiline(self):
        error = "Error:\nLínea 1\nLínea 2"
        formatted = format_error(error)
        self.assertIn("Línea 1", formatted)
        self.assertIn("Línea 2", formatted)

    def test_format_table_simple(self):
        headers = ["Nombre", "Edad"]
        rows = [["Juan", "30"], ["María", "25"]]
        table = format_table(headers, rows)
        self.assertIn("Nombre", table)
        self.assertIn("Edad", table)
        self.assertIn("Juan", table)
        self.assertIn("María", table)

    def test_format_table_empty(self):
        headers = ["Col1", "Col2"]
        rows = []
        table = format_table(headers, rows)
        self.assertIn("Col1", table)
        self.assertIn("Col2", table)

    def test_truncate_text_short(self):
        text = "Texto corto"
        truncated = truncate_text(text, max_length=100)
        self.assertEqual(text, truncated)

    def test_truncate_text_long(self):
        text = "a" * 200
        truncated = truncate_text(text, max_length=50)
        self.assertEqual(len(truncated), 50)
        self.assertTrue(truncated.endswith("..."))

    def test_truncate_text_custom_suffix(self):
        text = "a" * 100
        truncated = truncate_text(text, max_length=20, suffix="[...]")
        self.assertTrue(truncated.endswith("[...]"))


class TestColors(unittest.TestCase):
    """Tests para el sistema de colores"""

    def test_colorize_simple(self):
        colored = colorize("Test", Colors.RED)
        self.assertIn("Test", colored)
        self.assertIn(Colors.RED, colored)
        self.assertIn(Colors.RESET, colored)

    def test_colorize_with_style(self):
        colored = colorize("Test", Colors.GREEN, Colors.BOLD)
        self.assertIn(Colors.GREEN, colored)
        self.assertIn(Colors.BOLD, colored)

    def test_colorize_with_background(self):
        colored = colorize("Test", Colors.WHITE, bg_color=Colors.BG_BLUE)
        self.assertIn(Colors.WHITE, colored)
        self.assertIn(Colors.BG_BLUE, colored)

    def test_colors_class_attributes(self):
        self.assertIsNotNone(Colors.RED)
        self.assertIsNotNone(Colors.GREEN)
        self.assertIsNotNone(Colors.BLUE)
        self.assertIsNotNone(Colors.YELLOW)
        self.assertIsNotNone(Colors.BOLD)
        self.assertIsNotNone(Colors.RESET)


class TestFileOperations(unittest.TestCase):
    """Tests para operaciones con archivos"""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py')
        self.temp_file.write("print('Hello World')")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_file_exists(self):
        self.assertTrue(os.path.exists(self.temp_file.name))

    def test_file_extension(self):
        _, ext = os.path.splitext(self.temp_file.name)
        self.assertEqual(ext, '.py')

    def test_read_file_content(self):
        with open(self.temp_file.name, 'r') as f:
            content = f.read()
        self.assertIn("Hello World", content)


if __name__ == '__main__':
    unittest.main()
