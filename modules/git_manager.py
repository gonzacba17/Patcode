from git import Repo
from rich.console import Console

console = Console()

def git_commit(message="update by PatCode"):
    repo = Repo(".")
    repo.git.add(all=True)
    repo.index.commit(message)
    console.print("✅ [cyan]Commit realizado:[/cyan]", message)

def git_status():
    repo = Repo(".")
    console.print(repo.git.status())
    return repo.git.status()    