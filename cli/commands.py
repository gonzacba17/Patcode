"""
Sistema de comandos slash para PatCode CLI.
"""
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Command:
    name: str
    handler: Callable
    description: str
    usage: str
    aliases: List[str] = None
    requires_args: bool = False
    category: str = "general"
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []

class CommandRegistry:
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.categories: Dict[str, List[Command]] = {}
        self._register_core_commands()
        logger.info("CommandRegistry inicializado")
    
    def register(self, command: Command):
        self.commands[command.name] = command
        
        for alias in command.aliases:
            self.commands[alias] = command
        
        if command.category not in self.categories:
            self.categories[command.category] = []
        self.categories[command.category].append(command)
        
        logger.debug(f"Comando registrado: /{command.name}")
    
    def execute(self, command_str: str, context: Any) -> str:
        parts = command_str.strip().split(maxsplit=1)
        cmd_name = parts[0][1:]
        args = parts[1] if len(parts) > 1 else ""
        
        command = self.commands.get(cmd_name)
        
        if not command:
            return f"❌ Comando desconocido: /{cmd_name}\nUsa /help para ver comandos disponibles"
        
        if command.requires_args and not args:
            return f"❌ {command.name} requiere argumentos\nUso: {command.usage}"
        
        try:
            return command.handler(context, args)
        except Exception as e:
            logger.error(f"Error ejecutando /{cmd_name}: {str(e)}")
            return f"❌ Error: {str(e)}"
    
    def get_help(self, command_name: Optional[str] = None) -> str:
        if command_name:
            command = self.commands.get(command_name)
            if not command:
                return f"❌ Comando no encontrado: /{command_name}"
            
            help_text = [
                f"# /{command.name}",
                f"\n{command.description}",
                f"\n**Uso:** {command.usage}"
            ]
            
            if command.aliases:
                help_text.append(f"\n**Aliases:** {', '.join('/' + a for a in command.aliases)}")
            
            return '\n'.join(help_text)
        
        help_text = ["# 📚 PatCode - Comandos Disponibles\n"]
        
        for category, commands in sorted(self.categories.items()):
            help_text.append(f"\n## {category.upper()}")
            
            unique_commands = {}
            for cmd in commands:
                if cmd.name not in unique_commands:
                    unique_commands[cmd.name] = cmd
            
            for cmd in unique_commands.values():
                help_text.append(f"  /{cmd.name:<20} - {cmd.description}")
        
        help_text.append("\n💡 Tip: Usa /help <comando> para ver detalles de un comando específico")
        
        return '\n'.join(help_text)
    
    def _register_core_commands(self):
        
        self.register(Command(
            name="help",
            handler=lambda ctx, args: self.get_help(args.strip() if args else None),
            description="Muestra ayuda de comandos",
            usage="/help [comando]",
            aliases=["h", "?"],
            category="general"
        ))
        
        self.register(Command(
            name="clear",
            handler=lambda ctx, args: self._handle_clear(ctx),
            description="Limpia historial de conversación",
            usage="/clear",
            aliases=["cls"],
            category="general"
        ))
        
        self.register(Command(
            name="exit",
            handler=lambda ctx, args: "exit",
            description="Salir de PatCode",
            usage="/exit",
            aliases=["quit", "q"],
            category="general"
        ))
        
        self.register(Command(
            name="reset",
            handler=lambda ctx, args: self._handle_reset(ctx),
            description="Resetear sesión completa",
            usage="/reset",
            category="general"
        ))
        
        self.register(Command(
            name="files",
            handler=lambda ctx, args: self._handle_files(ctx, args),
            description="Lista archivos del proyecto",
            usage="/files [pattern]",
            category="context"
        ))
        
        self.register(Command(
            name="tree",
            handler=lambda ctx, args: self._handle_tree(ctx, args),
            description="Muestra árbol de directorios",
            usage="/tree [depth]",
            category="context"
        ))
        
        self.register(Command(
            name="tokens",
            handler=lambda ctx, args: self._handle_tokens(ctx),
            description="Muestra uso de tokens",
            usage="/tokens",
            category="context"
        ))
        
        self.register(Command(
            name="stats",
            handler=lambda ctx, args: self._handle_stats(ctx),
            description="Estadísticas de la sesión",
            usage="/stats",
            category="context"
        ))
        
        self.register(Command(
            name="read",
            handler=lambda ctx, args: self._handle_read(ctx, args),
            description="Lee un archivo",
            usage="/read <filepath>",
            requires_args=True,
            category="files"
        ))
        
        self.register(Command(
            name="diff",
            handler=lambda ctx, args: self._handle_diff(ctx, args),
            description="Muestra diferencias en archivo",
            usage="/diff [filepath]",
            category="files"
        ))
        
        self.register(Command(
            name="git",
            handler=lambda ctx, args: self._handle_git(ctx, args),
            description="Operaciones Git",
            usage="/git <subcommand>",
            requires_args=True,
            category="git"
        ))
        
        self.register(Command(
            name="index",
            handler=lambda ctx, args: self._handle_index(ctx, args),
            description="Indexa proyecto para RAG",
            usage="/index [path]",
            category="rag"
        ))
        
        self.register(Command(
            name="search",
            handler=lambda ctx, args: self._handle_search(ctx, args),
            description="Búsqueda semántica en código",
            usage="/search <query>",
            requires_args=True,
            category="rag"
        ))
        
        self.register(Command(
            name="related",
            handler=lambda ctx, args: self._handle_related(ctx, args),
            description="Muestra código relacionado",
            usage="/related <filepath>",
            requires_args=True,
            category="rag"
        ))
    
    def _handle_clear(self, ctx) -> str:
        if hasattr(ctx, 'clear_history'):
            ctx.clear_history()
            return "✅ Historial limpiado"
        return "✅ Historial limpiado"
    
    def _handle_reset(self, ctx) -> str:
        if hasattr(ctx, 'clear_history'):
            ctx.clear_history()
        if hasattr(ctx, 'vector_store'):
            ctx.vector_store.clear()
        return "✅ Sesión reseteada completamente"
    
    def _handle_files(self, ctx, pattern: str) -> str:
        import fnmatch
        
        files = []
        for path in Path('.').rglob('*'):
            if path.is_file():
                if not pattern or fnmatch.fnmatch(str(path), f"*{pattern}*"):
                    files.append(str(path))
        
        if not files:
            return "No se encontraron archivos"
        
        return "📁 Archivos:\n" + '\n'.join(f"  - {f}" for f in sorted(files)[:50])
    
    def _handle_tree(self, ctx, depth_str: str) -> str:
        depth = int(depth_str) if depth_str.strip().isdigit() else 2
        
        def build_tree(path: Path, prefix: str = "", current_depth: int = 0):
            if current_depth >= depth:
                return []
            
            items = []
            try:
                children = sorted(path.iterdir())
                for i, child in enumerate(children):
                    is_last = i == len(children) - 1
                    items.append(f"{prefix}{'└── ' if is_last else '├── '}{child.name}")
                    
                    if child.is_dir() and not child.name.startswith('.'):
                        extension = "    " if is_last else "│   "
                        items.extend(build_tree(child, prefix + extension, current_depth + 1))
            except PermissionError:
                pass
            
            return items
        
        tree = ["📂 " + Path.cwd().name] + build_tree(Path('.'))
        return '\n'.join(tree[:100])
    
    def _handle_tokens(self, ctx) -> str:
        if hasattr(ctx, 'memory_manager'):
            messages = ctx.memory_manager.get_full_context()
            total_chars = sum(len(m['content']) for m in messages)
            approx_tokens = total_chars // 4
            
            return f"📊 Uso de Tokens:\n" \
                   f"  - Mensajes en memoria: {len(messages)}\n" \
                   f"  - Caracteres totales: {total_chars:,}\n" \
                   f"  - Tokens aprox: {approx_tokens:,}"
        return "No hay datos de tokens disponibles"
    
    def _handle_stats(self, ctx) -> str:
        stats = []
        
        if hasattr(ctx, 'memory_manager') and ctx.memory_manager:
            try:
                messages = ctx.memory_manager.get_full_context()
                stats.append(f"💬 Mensajes: {len(messages)}")
            except:
                pass
        
        if hasattr(ctx, 'vector_store') and ctx.vector_store:
            try:
                rag_stats = ctx.vector_store.get_stats()
                stats.append(f"📚 Documentos indexados: {rag_stats['total_documents']}")
            except:
                pass
        
        if hasattr(ctx, 'file_manager') and ctx.file_manager:
            try:
                stats.append(f"📝 Archivos cargados: {len(ctx.file_manager.loaded_files)}")
            except:
                pass
        
        if not stats:
            stats.append("No hay estadísticas disponibles")
        
        return "📊 Estadísticas de Sesión:\n" + '\n'.join(f"  - {s}" for s in stats)
    
    def _handle_read(self, ctx, filepath: str) -> str:
        if hasattr(ctx, 'file_manager'):
            try:
                ctx.file_manager.load_file(filepath)
                loaded_file = ctx.file_manager.loaded_files.get(filepath)
                if loaded_file:
                    content = loaded_file.content[:1000]
                    return f"📄 {filepath}:\n```\n{content}\n{'...' if len(loaded_file.content) > 1000 else ''}\n```"
            except Exception as e:
                return f"❌ Error leyendo archivo: {str(e)}"
        return "File manager no disponible"
    
    def _handle_diff(self, ctx, filepath: str) -> str:
        return "Diff no implementado aún"
    
    def _handle_git(self, ctx, args: str) -> str:
        parts = args.split(maxsplit=1)
        subcmd = parts[0]
        subcmd_args = parts[1] if len(parts) > 1 else ""
        
        if subcmd == "status":
            return "Git status - no implementado"
        elif subcmd == "diff":
            return "Git diff - no implementado"
        elif subcmd == "log":
            return "Git log - no implementado"
        elif subcmd == "commit":
            if not subcmd_args:
                return "❌ Uso: /git commit <mensaje>"
            return "Git commit - no implementado"
        else:
            return f"❌ Subcomando desconocido: {subcmd}\nDisponibles: status, diff, log, commit"
    
    def _handle_index(self, ctx, path: str) -> str:
        if not hasattr(ctx, 'code_indexer'):
            return "❌ RAG no disponible"
        
        if path:
            try:
                chunks = ctx.code_indexer.index_file(Path(path))
                return f"✅ {path} indexado ({chunks} chunks)"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        else:
            try:
                stats = ctx.code_indexer.index_project()
                return f"✅ Proyecto indexado:\n" \
                       f"  - Archivos: {stats['files_processed']}\n" \
                       f"  - Chunks: {stats['chunks_indexed']}"
            except Exception as e:
                return f"❌ Error: {str(e)}"
    
    def _handle_search(self, ctx, query: str) -> str:
        if not hasattr(ctx, 'retriever'):
            return "❌ RAG no disponible"
        
        try:
            context = ctx.retriever.retrieve_context(query, top_k=5)
            return context
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _handle_related(self, ctx, filepath: str) -> str:
        if not hasattr(ctx, 'retriever'):
            return "❌ RAG no disponible"
        
        try:
            related = ctx.retriever.retrieve_related_code(filepath, top_k=5)
            
            if not related:
                return "No se encontró código relacionado"
            
            output = [f"🔗 Código relacionado a {filepath}:\n"]
            for i, r in enumerate(related, 1):
                output.append(
                    f"{i}. {r['filepath']} (L{r['start_line']}-{r['end_line']}) "
                    f"- Similitud: {r['similarity']:.2f}"
                )
            return '\n'.join(output)
        except Exception as e:
            return f"❌ Error: {str(e)}"


command_registry = CommandRegistry()
