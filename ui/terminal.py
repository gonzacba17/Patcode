"""
Terminal CLI mejorada para PatCode con comandos slash y plan mode.
"""
from cli.commands import command_registry
from cli.plan_mode import plan_mode
from cli.formatter import formatter
import readline
import logging

logger = logging.getLogger(__name__)

class PatCodeTerminal:
    
    def __init__(self, agent):
        self.agent = agent
        self.formatter = formatter
        self.in_plan_mode = False
        self.pending_plan = None
        
        self._setup_autocomplete()
        
        print(formatter.format_info_box(
            "PatCode v2.0", 
            "Asistente de programación con IA local\nEscribe /help para ver comandos disponibles",
            box_type="info"
        ))
    
    def _setup_autocomplete(self):
        commands = list(command_registry.commands.keys())
        
        def completer(text, state):
            options = [f"/{cmd}" for cmd in commands if cmd.startswith(text.lstrip('/'))]
            return options[state] if state < len(options) else None
        
        try:
            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")
        except:
            logger.warning("Autocompletado no disponible en este sistema")
    
    def run(self):
        while True:
            try:
                if self.in_plan_mode:
                    prompt = formatter._color("patcode[plan]> ", formatter.Colors.BRIGHT_YELLOW)
                else:
                    prompt = formatter._color("patcode> ", formatter.Colors.BRIGHT_GREEN)
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                response = self._process_input(user_input)
                
                if response:
                    if response == "exit":
                        print(formatter.format_success("¡Hasta luego! 👋"))
                        break
                    
                    formatted_response = formatter.format_response(response)
                    print(formatted_response)
                    print()
                
            except KeyboardInterrupt:
                print("\n" + formatter.format_warning("Usa /exit para salir"))
            except EOFError:
                print("\n" + formatter.format_success("¡Hasta luego! 👋"))
                break
            except Exception as e:
                print(formatter.format_error(f"Error inesperado: {str(e)}"))
    
    def _process_input(self, user_input: str) -> str:
        
        if user_input.startswith('/'):
            response = command_registry.execute(user_input, self.agent)
            
            if response == "exit":
                return "exit"
            
            return response
        
        if self.in_plan_mode:
            return self._handle_plan_mode_input(user_input)
        
        if self._should_use_plan_mode(user_input):
            plan = plan_mode.create_plan_from_intent(user_input, self.agent)
            self.pending_plan = plan
            self.in_plan_mode = True
            return str(plan)
        
        response = self.agent.ask(user_input)
        return response
    
    def _should_use_plan_mode(self, user_input: str) -> bool:
        keywords = [
            'modifica', 'cambia', 'edita', 'crea', 'elimina',
            'ejecuta', 'corre', 'instala', 'commit', 'borra'
        ]
        return any(keyword in user_input.lower() for keyword in keywords)
    
    def _handle_plan_mode_input(self, user_input: str) -> str:
        response_lower = user_input.lower()
        
        if response_lower in ['s', 'si', 'yes', 'y', 'aprobar', 'approve']:
            results = plan_mode.execute_plan(self.pending_plan, self.agent)
            self.in_plan_mode = False
            self.pending_plan = None
            return '\n'.join(results)
        
        elif response_lower in ['n', 'no', 'rechazar', 'reject']:
            self.in_plan_mode = False
            self.pending_plan = None
            return formatter.format_warning("Plan rechazado")
        
        elif response_lower in ['m', 'modificar', 'modify']:
            return "💬 ¿Qué modificaciones quieres hacer al plan?"
        
        else:
            modified_plan = plan_mode.modify_plan(user_input)
            self.pending_plan = modified_plan
            return str(modified_plan)
