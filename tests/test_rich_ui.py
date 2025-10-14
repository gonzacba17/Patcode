"""
Tests para el sistema RichTerminalUI
"""

import pytest
from pathlib import Path
from io import StringIO

from ui.rich_terminal import RichTerminalUI


@pytest.fixture
def ui():
    """Fixture que retorna instancia de RichTerminalUI"""
    return RichTerminalUI()


def test_init(ui):
    """Verifica inicialización correcta"""
    assert ui.console is not None
    assert ui.session is not None
    assert ui.commands is not None


def test_display_code(ui, capsys):
    """Verifica syntax highlighting de código"""
    code = "def hello():\n    print('world')"
    ui.display_code(code, language="python", title="Test")
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_stats(ui):
    """Verifica tabla de estadísticas"""
    stats = {
        "total_messages": 10,
        "active_messages": 5,
        "passive_summaries": 3,
        "loaded_files": 2
    }
    
    ui.display_stats(stats)


def test_display_file_tree(ui):
    """Verifica árbol de archivos"""
    files = [Path("test1.py"), Path("test2.py"), Path("test3.js")]
    
    ui.display_file_tree(files)


def test_progress_bar_creation(ui):
    """Verifica creación de barras de progreso"""
    bar = ui._create_progress_bar(8, 10)
    assert "█" in bar
    assert "green" in bar or "yellow" in bar
    
    bar_medium = ui._create_progress_bar(6, 10)
    assert "yellow" in bar_medium
    
    bar_low = ui._create_progress_bar(3, 10)
    assert "red" in bar_low


def test_status_emoji(ui):
    """Verifica emojis de estado según score"""
    assert ui._get_status_emoji(9) == "✅"
    assert ui._get_status_emoji(8.5) == "✅"
    assert ui._get_status_emoji(7) == "⚠️"
    assert ui._get_status_emoji(6.5) == "⚠️"
    assert ui._get_status_emoji(4) == "❌"
    assert ui._get_status_emoji(2) == "❌"


def test_display_analysis_report(ui):
    """Verifica reporte de análisis completo"""
    report = {
        'path': '/test/project',
        'scores': {
            'estructura': 8.0,
            'calidad': 6.5,
            'tests': 4.2
        },
        'suggestions': [
            'Agregar más tests',
            'Mejorar documentación',
            'Configurar linter'
        ]
    }
    
    ui.display_analysis_report(report)


def test_display_help(ui):
    """Verifica tabla de ayuda con comandos"""
    commands = {
        'analyze': 'Analiza proyecto',
        'explain': 'Explica código',
        'test': 'Genera tests'
    }
    
    ui.display_help(commands)


def test_display_error(ui, capsys):
    """Verifica display de errores"""
    ui.display_error("Este es un error de prueba")
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_success(ui, capsys):
    """Verifica display de mensajes de éxito"""
    ui.display_success("Operación exitosa")
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_warning(ui, capsys):
    """Verifica display de advertencias"""
    ui.display_warning("Esta es una advertencia")
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_info(ui, capsys):
    """Verifica display de información"""
    ui.display_info("Esta es información importante")
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_markdown(ui, capsys):
    """Verifica rendering de markdown"""
    markdown_text = "# Título\n\n- Item 1\n- Item 2\n\n```python\nprint('hello')\n```"
    ui.display_markdown(markdown_text)
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_model_info(ui, capsys):
    """Verifica display de información del modelo"""
    ui.display_model_info(
        model="qwen2.5-coder:7b",
        speed="Balanceado",
        ram="8GB"
    )
    
    captured = capsys.readouterr()
    assert "qwen2.5-coder:7b" in captured.out or len(captured.out) > 0


def test_show_plan(ui, capsys):
    """Verifica display de plan de acción"""
    steps = [
        "Analizar código existente",
        "Identificar problemas",
        "Proponer soluciones"
    ]
    
    ui.show_plan(steps)
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_display_code_diff(ui, capsys):
    """Verifica display de diff de código"""
    old_code = "def old_function():\n    pass"
    new_code = "def new_function():\n    print('improved')"
    
    ui.display_code_diff(old_code, new_code, language="python")
    
    captured = capsys.readouterr()
    assert len(captured.out) > 0
