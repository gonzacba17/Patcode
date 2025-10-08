import typer
from rich.console import Console
from modules.ai_agent import ask_ollama
from modules.code_manager import read_file, write_file
from modules.git_manager import git_commit, git_status
from modules.test_runner import run_tests
from modules.analyzer import analyze_code

app = typer.Typer()
console = Console()

@app.command()
def chat(prompt: str, model: str = "llama3"):
    """Habla con PatCode en lenguaje natural."""
    console.print(f"🤖 [bold cyan]PatCode[/bold cyan] analizando tu instrucción...")
    respuesta = ask_ollama(prompt, model)
    console.print(respuesta)

@app.command()
def analyze(path: str):
    """Analiza un archivo Python."""
    analyze_code(path)

@app.command()
def edit(path: str, prompt: str, model: str = "llama3"):
    """Pide a PatCode que edite un archivo según tu prompt."""
    code = read_file(path)
    if not code:
        console.print("[red]Archivo no encontrado.[/red]")
        return
    final_prompt = f"Editá el siguiente código según lo que pido:\n\n{prompt}\n\n---\n{code}"
    new_code = ask_ollama(final_prompt, model)
    write_file(path, new_code)

@app.command()
def test():
    """Ejecuta los tests del proyecto."""
    run_tests()

@app.command()
def git(message: str = "update by PatCode"):
    """Realiza un commit rápido."""
    git_commit(message)

@app.command()
def status():
    """Muestra el estado del repositorio."""
    git_status()

if __name__ == "__main__":
    app()
