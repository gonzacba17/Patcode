"""
Tests para el formateador de salida.
"""
import pytest
from cli.formatter import OutputFormatter, Colors

def test_formatter_initialization():
    formatter = OutputFormatter()
    assert formatter.terminal_width > 0
    assert formatter.use_colors == True

def test_formatter_no_colors():
    formatter = OutputFormatter(use_colors=False)
    assert formatter.use_colors == False

def test_format_table():
    formatter = OutputFormatter(use_colors=False)
    
    headers = ["Name", "Age", "City"]
    rows = [
        ["Alice", "30", "NYC"],
        ["Bob", "25", "LA"]
    ]
    
    table = formatter.format_table(headers, rows)
    
    assert "Name" in table
    assert "Alice" in table
    assert "│" in table
    assert "┌" in table
    assert "└" in table

def test_format_info_box():
    formatter = OutputFormatter(use_colors=False)
    
    box = formatter.format_info_box("Test", "This is a test", box_type="info")
    
    assert "Test" in box
    assert "This is a test" in box
    assert "╭" in box
    assert "╰" in box
    assert "💡" in box

def test_format_success_box():
    formatter = OutputFormatter(use_colors=False)
    
    box = formatter.format_success("Operation successful")
    
    assert "Operation successful" in box
    assert "✅" in box

def test_format_error_box():
    formatter = OutputFormatter(use_colors=False)
    
    box = formatter.format_error("An error occurred")
    
    assert "An error occurred" in box
    assert "❌" in box

def test_format_warning_box():
    formatter = OutputFormatter(use_colors=False)
    
    box = formatter.format_warning("This is a warning")
    
    assert "This is a warning" in box
    assert "⚠️" in box

def test_format_code_block():
    formatter = OutputFormatter(use_colors=False)
    
    code = "def hello():\n    print('world')"
    formatted = formatter.format_code_block(code, "python")
    
    assert "python" in formatted
    assert "def hello()" in formatted
    assert "╭" in formatted
    assert "╰" in formatted

def test_format_progress():
    formatter = OutputFormatter()
    
    progress = formatter.format_progress(50, 100, "Test")
    
    assert "50%" in progress
    assert "50/100" in progress

def test_format_response_with_code():
    formatter = OutputFormatter(use_colors=False)
    
    text = "Here is code:\n```python\ndef test():\n    pass\n```"
    formatted = formatter.format_response(text)
    
    assert "def test():" in formatted

def test_format_response_with_heading():
    formatter = OutputFormatter(use_colors=False)
    
    text = "# Main Heading\n## Sub Heading"
    formatted = formatter.format_response(text)
    
    assert "Main Heading" in formatted
    assert "Sub Heading" in formatted

def test_color_method():
    formatter = OutputFormatter(use_colors=True)
    
    colored = formatter._color("test", Colors.RED)
    assert "\033[" in colored
    assert "test" in colored

def test_color_method_disabled():
    formatter = OutputFormatter(use_colors=False)
    
    colored = formatter._color("test", Colors.RED)
    assert colored == "test"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
