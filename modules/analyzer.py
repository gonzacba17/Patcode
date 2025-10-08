import ast
import os
from rich.console import Console

console = Console()

def analyze_code(path):
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        ast.parse(code)
        console.print(f"✅ [green]{path} está bien formado[/green]")
    except SyntaxError as e:
        console.print(f"❌ [red]Error de sintaxis en {path}: {e}[/red]")
