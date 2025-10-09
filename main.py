#!/usr/bin/env python3
"""
PatCode - Asistente de programación local con Ollama
"""
import sys
import os
from agents.pat_agent import PatAgent

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Muestra el banner de bienvenida"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════╗
║                                                   ║
║         🤖  PatCode v2.1                         ║
║         Tu asistente de código local              ║
║         Con manejo de archivos ✨                 ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
{Colors.ENDC}
{Colors.BLUE}Powered by Ollama{Colors.ENDC}

Comandos disponibles:
  {Colors.GREEN}/help{Colors.ENDC}       - Muestra esta ayuda
  {Colors.GREEN}/clear{Colors.ENDC}      - Limpia la memoria de conversación
  {Colors.GREEN}/stats{Colors.ENDC}      - Muestra estadísticas de uso
  {Colors.GREEN}/export{Colors.ENDC}     - Exporta la conversación actual
  
  {Colors.CYAN}Comandos de archivos:{Colors.ENDC}
  {Colors.GREEN}/read{Colors.ENDC}       - Lee un archivo (ej: /read main.py)
  {Colors.GREEN}/write{Colors.ENDC}      - Crea/modifica archivo (uso avanzado)
  {Colors.GREEN}/list{Colors.ENDC}       - Lista archivos (ej: /list *.py)
  {Colors.GREEN}/analyze{Colors.ENDC}    - Analiza la estructura del proyecto
  
  {Colors.GREEN}/quit{Colors.ENDC}       - Salir de PatCode

Escribí tu pregunta o mencioná un archivo para analizarlo.
{Colors.WARNING}Tip: Decí "mirá main.py" y lo leeré automáticamente{Colors.ENDC}
"""
    print(banner)

def print_help():
    """Muestra ayuda detallada"""
    help_text = f"""
{Colors.CYAN}{Colors.BOLD}📖 Guía de Uso de PatCode{Colors.ENDC}

{Colors.GREEN}Comandos Especiales:{Colors.ENDC}
  /help      - Muestra esta guía
  /clear     - Borra toda la memoria de conversación
  /stats     - Estadísticas de mensajes y memoria
  /export    - Exporta conversación a archivo .md
  /quit      - Cierra PatCode

{Colors.GREEN}Ejemplos de uso:{Colors.ENDC}
  • "Explicame qué es un decorator en Python"
  • "Cómo puedo optimizar este código: [pegar código]"
  • "Haceme una función que ordene una lista"
  • "Qué patrón de diseño usar para [describir problema]"

{Colors.GREEN}Tips:{Colors.ENDC}
  ✓ Podés pegar bloques de código completos
  ✓ PatCode recuerda el contexto de la conversación
  ✓ Pedí ejemplos concretos para entender mejor
  ✓ Usá /clear si querés empezar un tema nuevo
"""
    print(help_text)

def handle_command(command: str, agent: PatAgent) -> bool:
    """
    Maneja comandos especiales
    
    Returns:
        True si debe continuar, False si debe salir
    """
    command = command.strip().lower()
    
    if command == "/quit" or command == "/exit":
        print(f"\n{Colors.CYAN}👋 ¡Hasta luego! Seguí codeando.{Colors.ENDC}\n")
        return False
    
    elif command == "/help":
        print_help()
    
    elif command == "/clear":
        agent.clear_memory()
        print(f"{Colors.GREEN}✓ Memoria limpiada. Empezamos de cero.{Colors.ENDC}\n")
    
    elif command == "/stats":
        stats = agent.get_stats()
        print(f"\n{Colors.CYAN}📊 Estadísticas:{Colors.ENDC}")
        print(f"  Total de mensajes: {stats['total_messages']}")
        print(f"  Tus mensajes: {stats['user_messages']}")
        print(f"  Respuestas de PatCode: {stats['assistant_messages']}")
        print(f"  Tamaño de memoria: {stats['memory_size_kb']:.2f} KB\n")
    
    elif command == "/export":
        filename = f"patcode_export_{agent.history[0]['content'][:20] if agent.history else 'empty'}.md"
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        agent.export_conversation(filename)
    
    else:
        print(f"{Colors.WARNING}⚠️  Comando desconocido: {command}{Colors.ENDC}")
        print(f"Usá {Colors.GREEN}/help{Colors.ENDC} para ver comandos disponibles\n")
    
    return True

def main():
    """Función principal"""
    try:
        # Mostrar banner
        print_banner()
        
        # Inicializar agente
        print(f"{Colors.BLUE}Inicializando PatCode...{Colors.ENDC}")
        agent = PatAgent(
            model="llama3.2:latest",
            memory_path="memory/memory.json",
            max_history=100
        )
        print(f"{Colors.GREEN}✓ Listo para ayudarte{Colors.ENDC}\n")
        
        # Loop principal
        while True:
            try:
                # Prompt del usuario
                prompt = input(f"{Colors.BOLD}Tú:{Colors.ENDC} ")
                
                # Verificar si está vacío
                if not prompt.strip():
                    continue
                
                # Manejar comandos especiales
                if prompt.strip().startswith('/'):
                    should_continue = handle_command(prompt, agent)
                    if not should_continue:
                        break
                    continue
                
                # Enviar pregunta al agente
                print(f"{Colors.BOLD}PatCode:{Colors.ENDC} ", end='', flush=True)
                agent.ask(prompt, stream=True)
                print()  # Línea extra para separación
                
            except KeyboardInterrupt:
                print(f"\n\n{Colors.WARNING}Interrupción detectada.{Colors.ENDC}")
                confirm = input(f"¿Querés salir? (s/n): ").lower()
                if confirm in ['s', 'y', 'yes', 'si', 'sí']:
                    print(f"{Colors.CYAN}👋 ¡Chau!{Colors.ENDC}\n")
                    break
                print()
            
            except Exception as e:
                print(f"\n{Colors.FAIL}❌ Error inesperado: {e}{Colors.ENDC}\n")
                continue
    
    except ConnectionError as e:
        print(f"\n{Colors.FAIL}{e}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Solución:{Colors.ENDC}")
        print("  1. Instalá Ollama: https://ollama.ai")
        print("  2. Ejecutá: ollama serve")
        print("  3. Descargá un modelo: ollama pull llama3.2\n")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error fatal: {e}{Colors.ENDC}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()