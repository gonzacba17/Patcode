import subprocess
from rich.console import Console

console = Console()

def run_tests():
    console.print("🧪 Ejecutando pruebas...")
    result = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
    console.print(result.stdout)
    if result.returncode == 0:
        console.print("[green]✅ Todas las pruebas pasaron correctamente.[/green]")
    else:
        console.print("[red]❌ Algunas pruebas fallaron.[/red]")
    return result.stdout
    return result.stdout        