import os
from rich.console import Console

console = Console()

def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    console.print(f"💾 [green]Archivo actualizado:[/green] {path}")
def list_files(directory):              
    try:
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        return []           