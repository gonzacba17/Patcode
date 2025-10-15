#!/usr/bin/env python3
"""
Script de migración a v0.4.0
- Limpia cache antiguo si existe
- Valida modelos instalados en Ollama
- Genera reporte de compatibilidad
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.model_selector import get_model_selector
from utils.response_cache import ResponseCache
from rich.console import Console
from rich.table import Table
import requests


console = Console()


def check_ollama_running():
    """Verifica que Ollama esté corriendo"""
    console.print("\n[cyan]Verificando Ollama...[/cyan]")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            console.print("✅ Ollama está corriendo")
            return True
        else:
            console.print("[red]❌ Ollama no responde correctamente[/red]")
            return False
    except Exception as e:
        console.print(f"[red]❌ Error conectando con Ollama: {e}[/red]")
        console.print("[yellow]Ejecuta: ollama serve[/yellow]")
        return False


def check_ollama_models():
    """Verifica modelos instalados en Ollama"""
    console.print("\n[cyan]Verificando modelos en Ollama...[/cyan]")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        models_response = response.json()
        installed = [m['name'] for m in models_response.get('models', [])]
        
        table = Table(title="📦 Modelos Instalados")
        table.add_column("Modelo", style="cyan")
        table.add_column("Estado", justify="center")
        
        selector = get_model_selector()
        
        for model_name in selector.MODELS.keys():
            is_installed = any(model_name in m for m in installed)
            status = "✅ Instalado" if is_installed else "❌ No instalado"
            table.add_row(model_name, status)
        
        console.print(table)
        
        missing = [m for m in selector.MODELS.keys() 
                   if not any(m in inst for inst in installed)]
        
        if missing:
            console.print("\n[yellow]Modelos faltantes:[/yellow]")
            for model in missing:
                console.print(f"  ollama pull {model}")
    
    except Exception as e:
        console.print(f"[red]Error verificando Ollama: {e}[/red]")


def check_hardware_compatibility():
    """Verifica compatibilidad de hardware"""
    console.print("\n[cyan]Analizando hardware...[/cyan]")
    
    selector = get_model_selector()
    info = selector.system_info
    
    console.print(f"💻 RAM Total: {info['total_ram_gb']:.1f} GB")
    console.print(f"💾 RAM Disponible: {info['available_ram_gb']:.1f} GB")
    console.print(f"🔧 CPUs: {info['cpu_count']}")
    
    compatible = selector.list_compatible_models()
    
    console.print(f"\n✅ Modelos compatibles: {len(compatible)}")
    for model in compatible:
        console.print(f"  • {model}")
    
    console.print("\n[bold cyan]Recomendaciones:[/bold cyan]")
    console.print(f"  General: {selector.recommend_model('general')}")
    console.print(f"  Rápido: {selector.recommend_model('quick_questions')}")
    console.print(f"  Análisis: {selector.recommend_model('refactor')}")


def setup_cache():
    """Inicializa sistema de cache"""
    console.print("\n[cyan]Configurando cache...[/cyan]")
    
    cache = ResponseCache()
    
    if cache.cache_dir.exists():
        stats = cache.get_stats()
        console.print(f"📊 Cache existente: {stats['cache_size']}")
        
        if stats['total_queries'] > 0:
            console.print(f"  Total queries: {stats['total_queries']}")
            console.print(f"  Hit rate: {stats['hit_rate']}")
    else:
        console.print("✅ Cache inicializado en .patcode_cache/")


def update_gitignore():
    """Actualiza .gitignore con directorio de cache"""
    console.print("\n[cyan]Actualizando .gitignore...[/cyan]")
    
    gitignore_path = Path.cwd() / '.gitignore'
    
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        
        if '.patcode_cache/' not in content:
            with open(gitignore_path, 'a') as f:
                f.write("\n# PatCode cache\n.patcode_cache/\n")
            console.print("✅ .gitignore actualizado")
        else:
            console.print("✅ .gitignore ya contiene .patcode_cache/")
    else:
        console.print("[yellow]⚠️  .gitignore no encontrado[/yellow]")


def main():
    console.print("[bold green]🚀 Migración a PatCode v0.4.0[/bold green]\n")
    
    if not check_ollama_running():
        console.print("\n[red]⚠️  Ollama no está corriendo. Inicia Ollama primero.[/red]")
        sys.exit(1)
    
    check_ollama_models()
    check_hardware_compatibility()
    setup_cache()
    update_gitignore()
    
    console.print("\n[bold green]✅ Migración completada[/bold green]")
    console.print("\nPrueba las nuevas características:")
    console.print("  patcode chat --auto")
    console.print("  patcode models")
    console.print("  patcode cache stats")


if __name__ == '__main__':
    main()
