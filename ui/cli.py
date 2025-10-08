"""
Interfaz de línea de comandos (CLI) para PatCode
"""

import sys
import os
from utils.colors import Colors, colorize, print_success, print_error, print_info
from utils.logger import get_logger
from utils.formatters import format_response, format_code, format_error


class CLI:
    """Interfaz de línea de comandos para PatCode"""
    
    def __init__(self, agent):
        """
        Inicializa la CLI
        
        Args:
            agent: Instancia del agente PatAgent
        """
        self.agent = agent
        self.logger = get_logger()
        self.running = False
        
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
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
        """
        print(colorize(banner, Colors.CYAN, Colors.BOLD))
        print(colorize("  💡 Escribe 'ayuda' para ver los comandos disponibles", Colors.DIM))
        print(colorize("  💡 Escribe 'salir' para cerrar PatCode\n", Colors.DIM))
    
    def print_help(self):
        """Muestra la ayuda con comandos disponibles"""
        help_text = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                           COMANDOS DISPONIBLES                            ║
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
║     escribir <archivo>   - Crea o modifica un archivo                    ║
║     analizar <archivo>   - Analiza un archivo de código                  ║
║                                                                           ║
║  🔧 COMANDOS DE CÓDIGO:                                                   ║
║     explicar <código>    - Explica un fragmento de código                ║
║     optimizar <código>   - Sugiere optimizaciones                        ║
║     depurar <código>     - Ayuda a encontrar errores                     ║
║                                                                           ║
║  💬 USO GENERAL:                                                          ║
║     Simplemente escribe tu pregunta o instrucción en lenguaje natural    ║
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
                # Truncar respuestas largas
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
        
        # Comandos de salida
        if command in ['salir', 'exit', 'quit', 'q']:
            self.running = False
            print(colorize("\n👋 ¡Hasta luego! Gracias por usar PatCode\n", 
                         Colors.CYAN, Colors.BOLD))
            return True
        
        # Ayuda
        if command in ['ayuda', 'help', 'h', '?']:
            self.print_help()
            return True
        
        # Limpiar pantalla
        if command in ['limpiar', 'clear', 'cls']:
            self.clear_screen()
            self.print_banner()
            return True
        
        # Historial
        if command in ['historial', 'history']:
            self.show_history()
            return True
        
        # Leer archivo
        if command.startswith('leer '):
            file_path = command[5:].strip()
            self.read_file(file_path)
            return True
        
        return False
    
    def read_file(self, file_path):
        """
        Lee y muestra un archivo
        
        Args:
            file_path (str): Ruta del archivo
        """
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
        """
        Obtiene la entrada del usuario con prompt personalizado
        
        Returns:
            str: Entrada del usuario
        """
        try:
            prompt = colorize("Tú", Colors.YELLOW, Colors.BOLD) + \
                    colorize(" ❯ ", Colors.DIM)
            return input(prompt)
        except EOFError:
            return 'salir'
        except KeyboardInterrupt:
            print()
            return 'salir'
    
    def display_response(self, response):
        """
        Muestra la respuesta del agente
        
        Args:
            response (str): Respuesta del agente
        """
        print(colorize("\n🤖 PatCode", Colors.GREEN, Colors.BOLD) + 
              colorize(" ❯ ", Colors.DIM))
        
        # Formatear y mostrar respuesta
        formatted_response = format_response(response)
        print(formatted_response)
        print()  # Línea en blanco
    
    def run(self):
        """Ejecuta el loop principal de la CLI"""
        self.clear_screen()
        self.print_banner()
        self.running = True
        
        while self.running:
            try:
                # Obtener entrada del usuario
                user_input = self.get_input()
                
                if not user_input.strip():
                    continue
                
                # Procesar comandos especiales
                if self.process_command(user_input):
                    continue
                
                # Enviar pregunta al agente
                try:
                    response = self.agent.ask(user_input)
                    self.display_response(response)
                    
                except Exception as e:
                    error_msg = f"Error al procesar la solicitud: {str(e)}"
                    print(format_error(error_msg))
                    self.logger.error(error_msg)
                
            except KeyboardInterrupt:
                print(colorize("\n\n⚠ Interrupción detectada. Escribe 'salir' para cerrar PatCode\n", 
                             Colors.YELLOW))
                continue
            
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                print(format_error(error_msg))
                self.logger.critical(error_msg)
                break
    
    def run_single_query(self, query):
        """
        Ejecuta una única consulta sin entrar en modo interactivo
        
        Args:
            query (str): Consulta a realizar
        """
        try:
            response = self.agent.ask(query)
            self.display_response(response)
        except Exception as e:
            error_msg = f"Error al procesar la consulta: {str(e)}"
            print(format_error(error_msg))
            self.logger.error(error_msg)


def main():
    """Función principal para ejecutar la CLI"""
    from agents.pat_agent import PatAgent
    
    # Crear agente
    agent = PatAgent()
    
    # Crear y ejecutar CLI
    cli = CLI(agent)
    cli.run()


if __name__ == "__main__":
    main()