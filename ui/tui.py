"""
Interfaz de usuario en terminal (TUI) avanzada para PatCode
Requiere: pip install prompt_toolkit
"""

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    print("⚠ prompt_toolkit no está instalado. Usa: pip install prompt_toolkit")

import os
from utils.colors import Colors, colorize, print_success, print_error, print_info
from utils.logger import get_logger
from utils.formatters import format_response, format_code


class TUI:
    """Interfaz de usuario en terminal avanzada con prompt_toolkit"""
    
    def __init__(self, agent):
        """
        Inicializa la TUI
        
        Args:
            agent: Instancia del agente PatAgent
        """
        if not PROMPT_TOOLKIT_AVAILABLE:
            raise ImportError("TUI requiere prompt_toolkit. Instala con: pip install prompt_toolkit")
        
        self.agent = agent
        self.logger = get_logger()
        self.running = False
        
        # Configurar autocompletado
        self.commands = [
            'ayuda', 'help', 'salir', 'exit', 'quit',
            'limpiar', 'clear', 'historial', 'history',
            'leer', 'escribir', 'analizar', 'explicar',
            'optimizar', 'depurar'
        ]
        self.completer = WordCompleter(self.commands, ignore_case=True)
        
        # Configurar historial
        history_dir = os.path.expanduser("~/.patcode")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        history_file = os.path.join(history_dir, "history.txt")
        
        # Configurar estilo
        self.style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'continuation': '#00aa00',
            'answer': '#00ffff',
        })
        
        # Crear sesión de prompt
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer,
            style=self.style,
            enable_history_search=True,
            multiline=False,
        )
    
    def print_banner(self):
        """Muestra el banner de bienvenida"""
        banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗  █████╗ ████████╗ ██████╗ ██████╗ ██████╗ ███████╗            ║
║   ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔═══██╗██╔══██╗██╔════╝            ║
║   ██████╔╝███████║   ██║   ██║     ██║   ██║██║  ██║█████╗              ║
║   ██╔═══╝ ██╔══██║   ██║   ██║     ██║   ██║██║  ██║██╔══╝              ║
║   ██║     ██║  ██║   ██║   ╚██████╗╚██████╔╝██████╔╝███████╗            ║
║   ╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝            ║
║                                                                           ║
║              Tu asistente de programación local con Ollama               ║
║                       🚀 Modo TUI Avanzado 🚀                            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
        """
        print(colorize(banner, Colors.CYAN, Colors.BOLD))
        print(colorize("  💡 Características TUI:", Colors.BRIGHT_CYAN, Colors.BOLD))
        print(colorize("     • Autocompletado de comandos (Tab)", Colors.DIM))
        print(colorize("     • Sugerencias basadas en historial", Colors.DIM))
        print(colorize("     • Búsqueda en historial (Ctrl+R)", Colors.DIM))
        print(colorize("     • Navegación con flechas ↑↓", Colors.DIM))
        print(colorize("\n  💡 Escribe 'ayuda' para ver comandos disponibles", Colors.DIM))
        print(colorize("  💡 Presiona Ctrl+C o escribe 'salir' para cerrar\n", Colors.DIM))
    
    def print_help(self):
        """Muestra la ayuda con comandos disponibles"""
        help_text = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                        COMANDOS DISPONIBLES (TUI)                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  📝 COMANDOS GENERALES:                                                   ║
║     ayuda, help          - Muestra esta ayuda                            ║
║     salir, exit, quit    - Cierra PatCode                                ║
║     limpiar, clear       - Limpia la pantalla                            ║
║     historial            - Muestra el historial de conversación          ║
║                                                                           ║
║  📄 COMANDOS DE ARCHIVOS:                                                 ║
║     leer <archivo>       - Lee y muestra un archivo                      ║
║     analizar <archivo>   - Analiza un archivo de código                  ║
║                                                                           ║
║  🎯 ATAJOS DE TECLADO:                                                    ║
║     Tab                  - Autocompletar comando                         ║
║     Ctrl+R               - Buscar en historial                           ║
║     ↑↓                   - Navegar historial                             ║
║     Ctrl+C               - Cancelar entrada actual                       ║
║     Ctrl+D               - Salir de PatCode                              ║
║                                                                           ║
║  💬 USO GENERAL:                                                          ║
║     Escribe tu pregunta o instrucción en lenguaje natural                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
        """
        print(colorize(help_text, Colors.CYAN))
    
    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_history(self):
        """Muestra el historial de conversación"""
        if not self.agent.history:
            print_info("No hay historial disponible")
            return
        
        print(colorize("\n📜 Historial de conversación:", Colors.CYAN, Colors.BOLD))
        print(colorize("═" * 80, Colors.CYAN))
        
        for i, msg in enumerate(self.agent.history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                print(colorize(f"\n[{i}] 👤 Usuario:", Colors.YELLOW, Colors.BOLD))
                print(colorize(f"    {content}", Colors.WHITE))
            else:
                print(colorize(f"\n[{i}] 🤖 PatCode:", Colors.GREEN, Colors.BOLD))
                if len(content) > 200:
                    print(colorize(f"    {content[:200]}...", Colors.WHITE))
                else:
                    print(colorize(f"    {content}", Colors.WHITE))
        
        print(colorize("\n" + "═" * 80 + "\n", Colors.CYAN))
    
    def process_command(self, user_input):
        """
        Procesa comandos especiales
        
        Args:
            user_input (str): Entrada del usuario
        
        Returns:
            bool: True si fue un comando especial, False si es una pregunta normal
        """
        command = user_input.lower().strip()
        
        if command in ['salir', 'exit', 'quit', 'q']:
            self.running = False
            print(colorize("\n👋 ¡Hasta luego! Gracias por usar PatCode\n", 
                         Colors.CYAN, Colors.BOLD))
            return True
        
        if command in ['ayuda', 'help', 'h', '?']:
            self.print_help()
            return True
        
        if command in ['limpiar', 'clear', 'cls']:
            self.clear_screen()
            self.print_banner()
            return True
        
        if command in ['historial', 'history']:
            self.show_history()
            return True
        
        if command.startswith('leer '):
            file_path = command[5:].strip()
            self.read_file(file_path)
            return True
        
        return False
    
    def read_file(self, file_path):
        """Lee y muestra un archivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(colorize(f"\n📄 Contenido de {file_path}:", Colors.CYAN, Colors.BOLD))
            print(colorize("─" * 80, Colors.CYAN))
            print(format_code(content))
            print(colorize("─" * 80 + "\n", Colors.CYAN))
            
        except FileNotFoundError:
            print_error(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            print_error(f"Error al leer el archivo: {str(e)}")
    
    def get_input(self):
        """Obtiene la entrada del usuario con prompt avanzado"""
        try:
            # Crear prompt HTML con estilo
            message = HTML('<ansigreen><b>Tú</b></ansigreen> <ansicyan>❯</ansicyan> ')
            return self.session.prompt(message)
        except KeyboardInterrupt:
            return ''
        except EOFError:
            return 'salir'
    
    def display_response(self, response):
        """Muestra la respuesta del agente"""
        print(colorize("\n🤖 PatCode", Colors.GREEN, Colors.BOLD) + 
              colorize(" ❯ ", Colors.CYAN))
        
        formatted_response = format_response(response)
        print(formatted_response)
        print()
    
    def run(self):
        """Ejecuta el loop principal de la TUI"""
        self.clear_screen()
        self.print_banner()
        self.running = True
        
        while self.running:
            try:
                user_input = self.get_input()
                
                if not user_input.strip():
                    continue
                
                if self.process_command(user_input):
                    continue
                
                try:
                    response = self.agent.ask(user_input)
                    self.display_response(response)
                except Exception as e:
                    print_error(f"Error al procesar: {str(e)}")
                    self.logger.error(str(e))
                
            except KeyboardInterrupt:
                print(colorize("\n⚠ Usa 'salir' para cerrar PatCode\n", Colors.YELLOW))
                continue
            except Exception as e:
                print_error(f"Error inesperado: {str(e)}")
                self.logger.critical(str(e))
                break


def main():
    """Función principal para ejecutar la TUI"""
    if not PROMPT_TOOLKIT_AVAILABLE:
        print("❌ No se puede iniciar TUI sin prompt_toolkit")
        print("💡 Instala con: pip install prompt_toolkit")
        return
    
    from agents.pat_agent import PatAgent
    
    agent = PatAgent()
    tui = TUI(agent)
    tui.run()


if __name__ == "__main__":
    main()