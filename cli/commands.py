"""
Sistema de comandos slash para PatCode CLI.
"""
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from pathlib import Path
from datetime import datetime

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
        
        self.register(Command(
            name="llm",
            handler=lambda ctx, args: self._handle_llm(ctx, args),
            description="Gestión de providers LLM",
            usage="/llm <providers|switch|stats|test> [args]",
            requires_args=True,
            category="llm"
        ))
        
        self.register(Command(
            name="msearch",
            handler=lambda ctx, args: self._handle_memory_search(ctx, args),
            description="Busca en historial de conversaciones",
            usage="/msearch <query>",
            requires_args=True,
            aliases=["memsearch"],
            category="memory"
        ))
        
        self.register(Command(
            name="export",
            handler=lambda ctx, args: self._handle_export(ctx, args),
            description="Exporta conversación a Markdown",
            usage="/export [archivo.md]",
            category="memory"
        ))
        
        self.register(Command(
            name="mstats",
            handler=lambda ctx, args: self._handle_memory_stats(ctx),
            description="Estadísticas de memoria",
            usage="/mstats",
            aliases=["memstats"],
            category="memory"
        ))
        
        self.register(Command(
            name="plugins",
            handler=lambda ctx, args: self._handle_plugins(ctx, args),
            description="Gestiona plugins del sistema",
            usage="/plugins [list|enable|disable] [nombre]",
            category="system"
        ))
        
        self.register(Command(
            name="cache",
            handler=lambda ctx, args: self._handle_cache(ctx, args),
            description="Gestiona caché de respuestas",
            usage="/cache [stats|clear|cleanup]",
            category="system"
        ))
        
        self.register(Command(
            name="telemetry",
            handler=lambda ctx, args: self._handle_telemetry(ctx, args),
            description="Muestra telemetría del sistema",
            usage="/telemetry [stats|events|export|clear]",
            aliases=["telem"],
            category="system"
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
    
    def _handle_llm(self, ctx, args: str) -> str:
        if not hasattr(ctx, 'llm_manager'):
            return "❌ LLM Manager no disponible"
        
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        subcmd_args = parts[1] if len(parts) > 1 else ""
        
        llm_manager = ctx.llm_manager
        
        if subcmd == "providers":
            available = llm_manager.get_available_providers()
            current = llm_manager.get_current_provider()
            all_providers = list(llm_manager.adapters.keys())
            
            output = ["🤖 LLM Providers:\n"]
            for provider in all_providers:
                status = "✅" if provider in available else "❌"
                current_marker = " ⬅ ACTUAL" if provider == current else ""
                output.append(f"  {status} {provider}{current_marker}")
            
            output.append(f"\n💡 Auto-fallback: {'✅ Activado' if llm_manager.config.auto_fallback else '❌ Desactivado'}")
            output.append(f"📋 Orden de fallback: {', '.join(llm_manager.config.fallback_order)}")
            
            return '\n'.join(output)
        
        elif subcmd == "switch":
            if not subcmd_args:
                return "❌ Uso: /llm switch <provider>\nProviders disponibles: " + ', '.join(llm_manager.adapters.keys())
            
            provider = subcmd_args.strip()
            success = llm_manager.switch_provider(provider)
            
            if success:
                return f"✅ Provider cambiado a: {provider}"
            else:
                return f"❌ No se pudo cambiar a '{provider}'. Verifica que esté disponible con /llm providers"
        
        elif subcmd == "stats":
            stats = llm_manager.get_stats()
            
            output = [
                f"📊 Estadísticas LLM:\n",
                f"  Provider actual: {stats['current_provider']}",
                f"  Providers disponibles: {', '.join(stats['available_providers'])}",
                f"  Auto-fallback: {'✅' if stats['auto_fallback'] else '❌'}",
                f"\n📈 Por Provider:"
            ]
            
            for provider, pstats in stats['provider_stats'].items():
                output.append(f"\n  {provider.upper()}:")
                output.append(f"    - Requests: {pstats['total_requests']}")
                output.append(f"    - Exitosos: {pstats['successful_requests']}")
                output.append(f"    - Fallidos: {pstats['failed_requests']}")
                output.append(f"    - Tasa de éxito: {pstats['success_rate']:.1%}")
                if pstats['average_response_time'] > 0:
                    output.append(f"    - Tiempo promedio: {pstats['average_response_time']:.2f}s")
            
            return '\n'.join(output)
        
        elif subcmd == "test":
            provider = subcmd_args.strip() if subcmd_args else llm_manager.get_current_provider()
            
            output = [f"🧪 Probando provider: {provider}...\n"]
            
            result = llm_manager.test_provider(provider)
            
            if result['available']:
                output.append(f"✅ {provider} está disponible")
                if 'test_success' in result:
                    if result['test_success']:
                        output.append(f"✅ Test de generación exitoso ({result['test_response_length']} chars)")
                    else:
                        output.append(f"❌ Test de generación falló: {result.get('test_error', 'Unknown')}")
            else:
                output.append(f"❌ {provider} NO está disponible")
                if 'error' in result:
                    output.append(f"   Error: {result['error']}")
            
            return '\n'.join(output)
        
        else:
            return f"❌ Subcomando desconocido: {subcmd}\nDisponibles: providers, switch, stats, test"
    
    def _handle_memory_search(self, ctx, query: str) -> str:
        """Busca en el historial de conversaciones"""
        if not hasattr(ctx, 'memory_manager'):
            return "❌ Memory manager no disponible"
        
        try:
            results = ctx.memory_manager.search_messages(query.strip(), limit=10)
            
            if not results:
                return "🔍 No se encontraron resultados"
            
            output = [f"🔍 Encontrados {len(results)} resultados:\n"]
            
            for i, msg in enumerate(results, 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                role_emoji = "👤" if role == "user" else "🤖"
                
                if len(content) > 150:
                    content = content[:150] + "..."
                
                output.append(f"{i}. {role_emoji} {role.title()}")
                if timestamp:
                    output.append(f"   [{timestamp}]")
                output.append(f"   {content}\n")
            
            return '\n'.join(output)
        
        except Exception as e:
            logger.error(f"Error en búsqueda de memoria: {e}")
            return f"❌ Error: {str(e)}"
    
    def _handle_export(self, ctx, filename: str) -> str:
        """Exporta conversación a Markdown"""
        if not hasattr(ctx, 'memory_manager'):
            return "❌ Memory manager no disponible"
        
        try:
            from datetime import datetime
            
            if not filename:
                filename = f"patcode_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            if not filename.endswith('.md'):
                filename += '.md'
            
            output_path = Path(filename)
            ctx.memory_manager.export_to_markdown(output_path)
            
            return f"✅ Conversación exportada a: {output_path}"
        
        except Exception as e:
            logger.error(f"Error exportando: {e}")
            return f"❌ Error: {str(e)}"
    
    def _handle_memory_stats(self, ctx) -> str:
        """Muestra estadísticas de memoria"""
        if not hasattr(ctx, 'memory_manager'):
            return "❌ Memory manager no disponible"
        
        try:
            stats = ctx.memory_manager.get_stats()
            
            output = [
                "📊 Estadísticas de Memoria:\n",
                f"  - Mensajes activos: {stats['active_messages']}",
                f"  - Resúmenes pasivos: {stats['passive_summaries']}",
                f"  - Contexto total: {stats['total_context']}"
            ]
            
            return '\n'.join(output)
        
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return f"❌ Error: {str(e)}"
    
    def _handle_plugins(self, ctx, args: str) -> str:
        """Gestiona plugins del sistema"""
        if not hasattr(ctx, 'plugin_manager') or not ctx.plugin_manager:
            return "❌ Sistema de plugins no está habilitado"
        
        parts = args.split() if args else []
        
        if not parts or parts[0] == "list":
            plugins = ctx.list_plugins()
            
            if not plugins:
                return "No hay plugins disponibles"
            
            output = ["🔌 Plugins Disponibles:\n"]
            
            for p in plugins:
                status = "✅ Activo" if p["enabled"] else "❌ Inactivo"
                output.append(f"  • {p['name']} v{p['version']}")
                output.append(f"    {status} | Prioridad: {p['priority']}")
                output.append(f"    {p['description']}")
                output.append("")
            
            return '\n'.join(output)
        
        elif parts[0] == "enable":
            if len(parts) < 2:
                return "❌ Uso: /plugins enable <nombre>"
            
            plugin_name = parts[1]
            ctx.enable_plugin(plugin_name)
            return f"✅ Plugin '{plugin_name}' habilitado"
        
        elif parts[0] == "disable":
            if len(parts) < 2:
                return "❌ Uso: /plugins disable <nombre>"
            
            plugin_name = parts[1]
            ctx.disable_plugin(plugin_name)
            return f"✅ Plugin '{plugin_name}' deshabilitado"
        
        else:
            return f"❌ Subcomando desconocido: {parts[0]}\nDisponibles: list, enable, disable"
    
    def _handle_cache(self, ctx, args: str) -> str:
        """Gestiona caché de respuestas"""
        if not hasattr(ctx, 'cache') or not ctx.cache:
            return "❌ Sistema de caché no está disponible"
        
        parts = args.split() if args else []
        
        if not parts or parts[0] == "stats":
            try:
                stats = ctx.cache.get_stats()
                
                output = [
                    "💾 Estadísticas de Caché:\n",
                    f"  - Entradas: {stats.get('entries', stats.get('cache_size', 0))}",
                    f"  - Hits: {stats.get('hits', stats.get('cache_hits', 0))}",
                    f"  - Misses: {stats.get('misses', stats.get('cache_misses', 0))}",
                    f"  - Hit rate: {stats.get('hit_rate', stats.get('cache_hit_rate', '0%'))}",
                ]
                
                if 'evictions' in stats:
                    output.append(f"  - Evictions: {stats['evictions']}")
                
                if 'size_mb' in stats:
                    output.append(f"  - Tamaño: {stats['size_mb']:.2f} MB")
                
                return '\n'.join(output)
            except Exception as e:
                logger.error(f"Error obteniendo stats de caché: {e}")
                return f"❌ Error: {str(e)}"
        
        elif parts[0] == "clear":
            try:
                ctx.cache.clear()
                return "✅ Caché limpiado completamente"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        elif parts[0] == "cleanup":
            try:
                if hasattr(ctx.cache, 'cleanup_expired'):
                    ctx.cache.cleanup_expired()
                    return "✅ Entradas expiradas eliminadas"
                else:
                    return "⚠️ Cleanup no disponible en este caché"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        else:
            return f"❌ Subcomando desconocido: {parts[0]}\nDisponibles: stats, clear, cleanup"
    
    def _handle_telemetry(self, ctx, args: str) -> str:
        """Muestra telemetría del sistema"""
        try:
            from utils.simple_telemetry import telemetry
        except ImportError:
            return "❌ Sistema de telemetría no disponible"
        
        parts = args.split() if args else []
        
        if not parts or parts[0] == "stats":
            try:
                stats = telemetry.get_stats()
                
                output = [
                    "📊 Estadísticas de Telemetría:\n",
                    f"  - Métricas totales: {stats['total_metrics']}",
                    f"  - Eventos totales: {stats['total_events']}"
                ]
                
                if stats['counters']:
                    output.append("\n🔢 Contadores:")
                    for name, value in sorted(stats['counters'].items())[:10]:
                        output.append(f"    {name}: {value}")
                
                if stats['gauges']:
                    output.append("\n📏 Gauges:")
                    for name, value in sorted(stats['gauges'].items())[:10]:
                        output.append(f"    {name}: {value:.2f}")
                
                if stats['timers']:
                    output.append("\n⏱️  Timers:")
                    for name, timer_stats in sorted(stats['timers'].items())[:5]:
                        output.append(
                            f"    {name}: "
                            f"avg={timer_stats['avg']:.3f}s, "
                            f"min={timer_stats['min']:.3f}s, "
                            f"max={timer_stats['max']:.3f}s"
                        )
                
                return '\n'.join(output)
            except Exception as e:
                logger.error(f"Error obteniendo stats de telemetría: {e}")
                return f"❌ Error: {str(e)}"
        
        elif parts[0] == "events":
            try:
                level = parts[1] if len(parts) > 1 else None
                events = telemetry.get_recent_events(limit=10, level=level)
                
                if not events:
                    return "No hay eventos registrados"
                
                output = [f"📋 Eventos Recientes ({len(events)}):\n"]
                
                for event in reversed(events):
                    timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
                    level_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(event.level, "•")
                    output.append(f"  {level_emoji} [{timestamp}] {event.type}: {event.message}")
                
                return '\n'.join(output)
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        elif parts[0] == "export":
            try:
                filename = parts[1] if len(parts) > 1 else f"telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                output_path = Path(filename)
                telemetry.export_to_json(output_path)
                return f"✅ Telemetría exportada a: {output_path}"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        elif parts[0] == "clear":
            try:
                telemetry.clear()
                return "✅ Telemetría limpiada"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        else:
            return f"❌ Subcomando desconocido: {parts[0]}\nDisponibles: stats, events, export, clear"


command_registry = CommandRegistry()
