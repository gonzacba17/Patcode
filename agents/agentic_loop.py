"""
Agentic Loop - Ciclo de razonamiento, acción y observación
Inspirado en el sistema de Claude Code
"""
from typing import Dict, Any, List, Optional
from agents.tool_parser import ToolParser


class AgenticLoop:
    """
    Implementa el ciclo agentic completo:
    
    1. PENSAR (Reasoning): El agente analiza la tarea
    2. ACTUAR (Action): Usa herramientas para obtener información o hacer cambios
    3. OBSERVAR (Observation): Procesa el resultado de la acción
    4. ITERAR: Repite hasta completar la tarea o alcanzar el límite
    
    Similar a ReAct (Reasoning + Acting) de Yao et al. 2022
    """
    
    MAX_ITERATIONS = 5  # Límite de iteraciones para evitar loops infinitos
    
    def __init__(self, agent, verbose: bool = False):
        """
        Inicializa el loop agentic
        
        Args:
            agent: Instancia de PatAgent
            verbose: Si es True, muestra información detallada del proceso
        """
        self.agent = agent
        self.parser = ToolParser()
        self.verbose = verbose
        
        # Estado del loop
        self.iteration_count = 0
        self.tool_history = []  # Registro de herramientas usadas
        self.current_task = ""
    
    def run(self, user_input: str, stream: bool = True) -> str:
        """
        Ejecuta el loop agentic completo para una tarea
        
        Args:
            user_input: Tarea o pregunta del usuario
            stream: Si mostrar respuestas en streaming
            
        Returns:
            Respuesta final del agente
        """
        # Resetear estado
        self.iteration_count = 0
        self.tool_history = []
        self.current_task = user_input
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🎯 TAREA: {user_input}")
            print(f"{'='*60}\n")
        else:
            print(f"\n🤔 Procesando tu petición...\n")
        
        # Preparar input inicial con contexto de herramientas
        current_input = self._prepare_initial_prompt(user_input)
        
        # Loop principal
        while self.iteration_count < self.MAX_ITERATIONS:
            self.iteration_count += 1
            
            if self.verbose:
                print(f"\n--- ITERACIÓN {self.iteration_count}/{self.MAX_ITERATIONS} ---\n")
            
            # FASE 1: PENSAR - El agente genera una respuesta
            response = self._think_phase(current_input)
            
            if not response:
                return self._handle_error("No se obtuvo respuesta del modelo")
            
            # FASE 2: DETECTAR - ¿Quiere usar una herramienta?
            tool_call = self.parser.extract_tool_call(response)
            
            if tool_call and tool_call.get("tool"):
                # HAY UNA TOOL CALL - Ejecutar ciclo de acción
                result = self._action_phase(tool_call, response)
                
                if result.get("should_continue"):
                    # Continuar iterando con el resultado de la tool
                    current_input = result["feedback"]
                else:
                    # La tool completó la tarea
                    return result.get("final_response", "Tarea completada")
            
            else:
                # NO HAY TOOL CALL - Esta es la respuesta final
                return self._finalize_response(response, stream)
        
        # Límite de iteraciones alcanzado
        return self._handle_max_iterations()
    
    def _prepare_initial_prompt(self, user_input: str) -> str:
        """
        Prepara el prompt inicial con contexto de herramientas
        
        Args:
            user_input: Input original del usuario
            
        Returns:
            Prompt enriquecido con información de herramientas
        """
        tools_context = "\n\n🔧 HERRAMIENTAS DISPONIBLES:\n"
        
        for name, tool in self.agent.tools.items():
            tools_context += f"\n• {name}(): {tool.description}"
        
        tools_context += "\n\n📋 INSTRUCCIONES:\n"
        tools_context += "- Si necesitás usar una herramienta, respondé con formato JSON:\n"
        tools_context += '  {"thought": "tu razonamiento", "tool": "nombre_herramienta", "arguments": {...}}\n'
        tools_context += "- Si podés responder directamente, hacelo sin usar herramientas\n"
        tools_context += "- Explicá tu razonamiento antes de actuar\n"
        
        return user_input + tools_context
    
    def _think_phase(self, input_text: str) -> str:
        """
        FASE DE PENSAMIENTO: El agente procesa el input y decide qué hacer
        
        Args:
            input_text: Input actual (puede ser la tarea original o feedback de tools)
            
        Returns:
            Respuesta del modelo
        """
        if self.verbose:
            print("💭 PENSANDO...\n")
        
        # Agregar al historial
        self.agent.history.append({
            "role": "user",
            "content": input_text
        })
        
        # Obtener respuesta del modelo (sin streaming en el loop)
        prompt = self.agent._build_prompt()
        response = self.agent._call_ollama(prompt, stream=False)
        
        if self.verbose and response:
            print(f"🧠 Respuesta del modelo:\n{response[:200]}...\n")
        
        return response
    
    def _action_phase(self, tool_call: Dict[str, Any], full_response: str) -> Dict[str, Any]:
        """
        FASE DE ACCIÓN: Ejecuta la herramienta solicitada
        
        Args:
            tool_call: Diccionario con la llamada a la herramienta
            full_response: Respuesta completa del modelo
            
        Returns:
            Dict con resultado y si debe continuar el loop
        """
        tool_name = tool_call["tool"]
        arguments = tool_call["arguments"]
        thought = tool_call.get("thought", "")
        
        # Mostrar información de la acción
        print(f"🔧 Usando herramienta: {tool_name}")
        if thought and self.verbose:
            print(f"💭 Razonamiento: {thought}")
        
        # Ejecutar la herramienta
        if self.verbose:
            print(f"⚙️  Argumentos: {arguments}\n")
        
        tool_result = self.agent.use_tool(tool_name, **arguments)
        
        # Registrar en historial
        self.tool_history.append({
            "iteration": self.iteration_count,
            "tool": tool_name,
            "arguments": arguments,
            "result": tool_result,
            "thought": thought
        })
        
        # Procesar resultado
        if tool_result["success"]:
            print(f"✅ Resultado: {tool_result.get('message', 'OK')}\n")
            feedback = self._format_success_feedback(tool_call, tool_result)
        else:
            print(f"❌ Error: {tool_result.get('error', 'Unknown error')}\n")
            feedback = self._format_error_feedback(tool_call, tool_result)
        
        return {
            "should_continue": True,
            "feedback": feedback
        }
    
    def _format_success_feedback(self, tool_call: Dict, result: Dict) -> str:
        """
        Formatea el feedback exitoso de una herramienta para la siguiente iteración
        
        Args:
            tool_call: La llamada a la herramienta ejecutada
            result: El resultado de la ejecución
            
        Returns:
            String con feedback formateado
        """
        feedback = f"✅ Resultado de {tool_call['tool']}:\n"
        feedback += f"{result['message']}\n\n"
        
        # Agregar datos relevantes según el tipo de herramienta
        data = result.get('data', {})
        
        if isinstance(data, dict):
            # Para archivos leídos
            if 'content' in data:
                content = data['content']
                lines = content.splitlines()
                
                # Limitar contenido si es muy largo
                if len(lines) > 100:
                    feedback += f"📄 Contenido del archivo (primeras 100 líneas):\n"
                    feedback += "```\n"
                    feedback += "\n".join(lines[:100])
                    feedback += f"\n... ({len(lines) - 100} líneas más)\n```\n"
                else:
                    feedback += f"📄 Contenido completo del archivo:\n"
                    feedback += "```\n"
                    feedback += content
                    feedback += "\n```\n"
            
            # Para listados de directorio
            elif 'items' in data:
                items = data['items']
                feedback += f"📁 Encontrados {len(items)} items:\n"
                for item in items[:20]:  # Mostrar máximo 20
                    icon = "📁" if item['type'] == 'directory' else "📄"
                    feedback += f"  {icon} {item['name']}\n"
                if len(items) > 20:
                    feedback += f"  ... y {len(items) - 20} items más\n"
            
            # Para comandos ejecutados
            elif 'stdout' in data or 'stderr' in data:
                if data.get('stdout'):
                    feedback += f"📤 Salida:\n```\n{data['stdout']}\n```\n"
                if data.get('stderr'):
                    feedback += f"⚠️  Errores:\n```\n{data['stderr']}\n```\n"
            
            # Para búsquedas
            elif 'matches' in data:
                matches = data['matches']
                feedback += f"🔍 Encontrados {len(matches)} resultados:\n"
                for match in matches[:10]:
                    feedback += f"  • {match}\n"
                if len(matches) > 10:
                    feedback += f"  ... y {len(matches) - 10} más\n"
        
        feedback += "\n💬 Ahora analizá este resultado y respondé al usuario de forma clara y útil.\n"
        feedback += "Si necesitás más información, usá otra herramienta.\n"
        feedback += "Si ya tenés suficiente información, da tu respuesta final sin formato JSON.\n"
        
        return feedback
    
    def _format_error_feedback(self, tool_call: Dict, result: Dict) -> str:
        """
        Formatea el feedback de error para la siguiente iteración
        
        Args:
            tool_call: La llamada a la herramienta que falló
            result: El resultado con error
            
        Returns:
            String con feedback de error
        """
        feedback = f"❌ Error ejecutando {tool_call['tool']}:\n"
        feedback += f"{result.get('error', 'Error desconocido')}\n\n"
        feedback += "💡 Sugerencias:\n"
        feedback += "- Intentá con otra herramienta\n"
        feedback += "- Verificá los argumentos\n"
        feedback += "- O explicale el problema al usuario\n"
        
        return feedback
    
    def _finalize_response(self, response: str, stream: bool) -> str:
        """
        Finaliza el loop con la respuesta del agente
        
        Args:
            response: Respuesta final del modelo
            stream: Si mostrar en streaming
            
        Returns:
            La respuesta final
        """
        # Agregar al historial
        self.agent.history.append({
            "role": "assistant",
            "content": response
        })
        self.agent._save_memory()
        
        # Mostrar respuesta
        if stream:
            print("PatCode: ", end="", flush=True)
            for char in response:
                print(char, end="", flush=True)
            print()
        else:
            print(f"\nPatCode: {response}\n")
        
        # Mostrar resumen si verbose
        if self.verbose:
            self._print_summary()
        
        return response
    
    def _handle_error(self, error_msg: str) -> str:
        """Maneja errores durante el loop"""
        error_response = f"❌ Error en el loop agentic: {error_msg}"
        print(error_response)
        return error_response
    
    def _handle_max_iterations(self) -> str:
        """Maneja cuando se alcanza el límite de iteraciones"""
        msg = f"⚠️ Se alcanzó el límite de {self.MAX_ITERATIONS} iteraciones.\n"
        msg += "La tarea podría ser muy compleja o estar mal formulada.\n"
        msg += "Sugerencias:\n"
        msg += "- Dividí tu tarea en pasos más pequeños\n"
        msg += "- Reformulá tu pregunta de forma más específica\n"
        msg += "- Usá comandos directos como /read o /ls\n"
        
        if self.verbose:
            self._print_summary()
        
        print(msg)
        return msg
    
    def _print_summary(self):
        """Imprime un resumen de las herramientas usadas"""
        if not self.tool_history:
            return
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN DEL LOOP AGENTIC")
        print(f"{'='*60}")
        print(f"Iteraciones: {self.iteration_count}")
        print(f"Herramientas usadas: {len(self.tool_history)}\n")
        
        for i, entry in enumerate(self.tool_history, 1):
            status = "✅" if entry["result"]["success"] else "❌"
            print(f"{i}. {status} {entry['tool']} - {entry['result'].get('message', entry['result'].get('error'))}")
        
        print(f"{'='*60}\n")
    
    def get_tool_history(self) -> List[Dict]:
        """
        Devuelve el historial completo de herramientas usadas
        
        Returns:
            Lista de diccionarios con información de cada tool call
        """
        return self.tool_history
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Devuelve estadísticas del loop actual
        
        Returns:
            Diccionario con métricas
        """
        tool_names = [entry["tool"] for entry in self.tool_history]
        successful_tools = sum(1 for entry in self.tool_history if entry["result"]["success"])
        
        return {
            "iterations": self.iteration_count,
            "tools_used": len(self.tool_history),
            "successful_tools": successful_tools,
            "failed_tools": len(self.tool_history) - successful_tools,
            "unique_tools": len(set(tool_names)),
            "tool_breakdown": {tool: tool_names.count(tool) for tool in set(tool_names)}
        }