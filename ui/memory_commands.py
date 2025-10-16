"""
Comandos especiales para interactuar con el sistema de memoria SQLite.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

console = Console()


def handle_memory_commands(user_input: str, memory_manager) -> bool:
    """
    Maneja comandos relacionados con memoria SQLite.
    
    Args:
        user_input: Comando ingresado por el usuario
        memory_manager: Instancia de SQLiteMemoryManager
    
    Returns:
        True si el comando fue procesado, False si no
    """
    cmd_lower = user_input.lower().strip()
    
    # !memory stats - Estadísticas de la sesión actual
    if cmd_lower == '!memory stats':
        session_id = getattr(memory_manager, 'current_session_id', None)
        if not session_id:
            console.print("[yellow]No hay sesión activa[/yellow]")
            return True
        
        summary = memory_manager.get_session_summary(session_id)
        if summary:
            table = Table(title="📊 Estadísticas de esta sesión", show_header=False)
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            
            table.add_row("Session ID", session_id[:16] + "...")
            table.add_row("Mensajes", str(summary.message_count))
            table.add_row("Tokens", str(summary.total_tokens))
            table.add_row("Primera consulta", summary.first_message)
            table.add_row("Última consulta", summary.last_message)
            
            console.print(table)
        else:
            console.print("[yellow]No hay datos de esta sesión[/yellow]")
        return True
    
    # !search <query> - Buscar en el historial
    elif user_input.startswith('!search '):
        query = user_input.replace('!search ', '').strip()
        if not query:
            console.print("[yellow]Uso: !search <texto>[/yellow]")
            return True
        
        session_id = getattr(memory_manager, 'current_session_id', None)
        results = memory_manager.search_messages(query, session_id=session_id, limit=10)
        
        if results:
            console.print(f"\n[cyan]🔍 Resultados para '{query}' ({len(results)}):[/cyan]\n")
            for i, msg in enumerate(results[:5], 1):
                preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                role_icon = "👤" if msg.role == "user" else "🤖"
                console.print(f"{i}. {role_icon} [{msg.role}] {preview}")
            
            if len(results) > 5:
                console.print(f"\n[dim]... y {len(results) - 5} resultados más[/dim]")
        else:
            console.print(f"[yellow]No se encontraron resultados para '{query}'[/yellow]")
        
        return True
    
    # !sessions - Listar todas las sesiones
    elif cmd_lower == '!sessions':
        sessions = memory_manager.get_all_sessions()
        
        if not sessions:
            console.print("[yellow]No hay sesiones guardadas[/yellow]")
            return True
        
        table = Table(title=f"📂 Sesiones disponibles ({len(sessions)})", show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Session ID", style="cyan")
        table.add_column("Mensajes", style="green", justify="right")
        table.add_column("Tokens", style="blue", justify="right")
        
        for i, session in enumerate(sessions[:15], 1):
            summary = memory_manager.get_session_summary(session)
            if summary:
                table.add_row(
                    str(i),
                    session[:16] + "...",
                    str(summary.message_count),
                    str(summary.total_tokens)
                )
        
        console.print(table)
        
        if len(sessions) > 15:
            console.print(f"\n[dim]Mostrando 15 de {len(sessions)} sesiones[/dim]")
        
        return True
    
    # !memory global - Estadísticas globales
    elif cmd_lower == '!memory global':
        stats = memory_manager.get_stats()
        
        panel_content = f"""
[cyan]Total de mensajes:[/cyan] {stats['total_messages']}
[cyan]Total de sesiones:[/cyan] {stats['total_sessions']}
[cyan]Total de tokens:[/cyan] {stats['total_tokens']}
[cyan]Tamaño de DB:[/cyan] {stats['db_size_kb']:.2f} KB

[dim]Primer mensaje:[/dim] {stats['first_message']}
[dim]Último mensaje:[/dim] {stats['last_message']}
        """
        
        console.print(Panel(panel_content, title="📈 Estadísticas Globales", border_style="green"))
        return True
    
    # !memory export - Exportar sesión actual
    elif cmd_lower == '!memory export':
        session_id = getattr(memory_manager, 'current_session_id', None)
        if not session_id:
            console.print("[yellow]No hay sesión activa[/yellow]")
            return True
        
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        export_path = export_dir / f"session_{session_id[:8]}.json"
        
        try:
            memory_manager.export_session(session_id, export_path)
            console.print(f"[green]✓ Sesión exportada a: {export_path}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error al exportar: {e}[/red]")
        
        return True
    
    # !memory help - Ayuda de comandos de memoria
    elif cmd_lower == '!memory help':
        help_text = """
[bold cyan]Comandos de Memoria SQLite:[/bold cyan]

[yellow]!memory stats[/yellow]     - Ver estadísticas de la sesión actual
[yellow]!memory global[/yellow]    - Ver estadísticas globales de la BD
[yellow]!memory export[/yellow]    - Exportar sesión actual a JSON
[yellow]!search <texto>[/yellow]   - Buscar mensajes por contenido
[yellow]!sessions[/yellow]          - Listar todas las sesiones guardadas
[yellow]!memory help[/yellow]      - Mostrar esta ayuda

[dim]Ejemplo: !search "crear función" para buscar mensajes sobre funciones[/dim]
        """
        console.print(Panel(help_text, border_style="cyan"))
        return True
    
    return False
