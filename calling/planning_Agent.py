"""
Planning Agent - Planifica y ejecuta tareas complejas paso a paso
Similar a cómo Claude Code descompone problemas
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class StepStatus(Enum):
    """Estado de un paso del plan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """Representa un paso en el plan de ejecución"""
    id: int
    action: str
    description: str
    tool: Optional[str] = None
    parameters: Optional[Dict] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "action": self.action,
            "description": self.description,
            "tool": self.tool,
            "parameters": self.parameters,
            "status": self.status.value,
            "result": self.result,
            "error": self.error
        }


class PlanningAgent:
    """
    Agente de planificación que descompone tareas complejas en pasos
    ejecutables, similar a Claude Code
    """
    
    def __init__(self, llm_agent, tool_registry):
        self.llm_agent = llm_agent
        self.tool_registry = tool_registry
        self.current_plan: List[PlanStep] = []
        self.planning_prompt = self._get_planning_prompt()
    
    def _get_planning_prompt(self) -> str:
        """System prompt para modo planificación"""
        return """Sos un agente de planificación experto. Tu tarea es descomponer solicitudes complejas en pasos ejecutables.

Herramientas disponibles:
{tools}

Cuando recibas una tarea compleja, debes:
1. Analizarla cuidadosamente
2. Crear un plan paso a paso
3. Cada paso debe ser concreto y ejecutable
4. Usar herramientas cuando sea necesario

Formato de respuesta:
<plan>
<step id="1">
  <action>Descripción de la acción</action>
  <tool>nombre_tool</tool>
  <parameters>
    <param name="nombre">valor</param>
  </parameters>
</step>
<step id="2">
  ...
</step>
</plan>

Ejemplo:
Tarea: "Analizá el código de main.py y sugerí mejoras"

<plan>
<step id="1">
  <action>Leer el archivo main.py</action>
  <tool>read_file</tool>
  <parameters>
    <param name="filepath">main.py</param>
  </parameters>
</step>
<step id="2">
  <action>Analizar la complejidad del código</action>
  <tool>none</tool>
</step>
<step id="3">
  <action>Generar sugerencias de mejora basadas en el análisis</action>
  <tool>none</tool>
</step>
</plan>

Sé conciso. Máximo 10 pasos. Usa herramientas solo cuando sea necesario."""
    
    def create_plan(self, task: str) -> List[PlanStep]:
        """
        Crea un plan de ejecución para una tarea
        
        Args:
            task: Descripción de la tarea a realizar
        
        Returns:
            Lista de pasos del plan
        """
        print(f"🧠 Planificando tarea: {task}")
        
        # Preparar prompt con herramientas disponibles
        tools_desc = self.tool_registry.get_tools_description()
        prompt = self.planning_prompt.format(tools=tools_desc)
        
        # Solicitar plan al LLM
        plan_request = f"{prompt}\n\nTarea: {task}\n\nGenera el plan:"
        
        # Obtener respuesta del LLM (sin streaming para parsear)
        response = self.llm_agent.ask(plan_request, stream=False)
        
        # Parsear el plan
        steps = self._parse_plan(response)
        
        if not steps:
            # Fallback: crear plan simple de un solo paso
            steps = [PlanStep(
                id=1,
                action=task,
                description=task,
                tool=None,
                parameters=None
            )]
        
        self.current_plan = steps
        return steps
    
    def _parse_plan(self, llm_response: str) -> List[PlanStep]:
        """Parsea la respuesta del LLM para extraer el plan"""
        import re
        
        steps = []
        
        # Buscar bloques <step>
        step_pattern = r'<step id="(\d+)">(.*?)</step>'
        step_matches = re.findall(step_pattern, llm_response, re.DOTALL)
        
        for step_id, step_content in step_matches:
            # Extraer action
            action_match = re.search(r'<action>(.*?)</action>', step_content, re.DOTALL)
            action = action_match.group(1).strip() if action_match else "Acción no especificada"
            
            # Extraer tool
            tool_match = re.search(r'<tool>(.*?)</tool>', step_content, re.DOTALL)
            tool = tool_match.group(1).strip() if tool_match else None
            if tool and tool.lower() == 'none':
                tool = None
            
            # Extraer parameters
            params = {}
            param_pattern = r'<param name="(.*?)">(.*?)</param>'
            param_matches = re.findall(param_pattern, step_content, re.DOTALL)
            for param_name, param_value in param_matches:
                params[param_name.strip()] = param_value.strip()
            
            steps.append(PlanStep(
                id=int(step_id),
                action=action,
                description=action,
                tool=tool,
                parameters=params if params else None
            ))
        
        return steps
    
    def display_plan(self, steps: List[PlanStep]):
        """Muestra el plan al usuario"""
        print("\n📋 Plan de Ejecución:")
        print("=" * 60)
        
        for step in steps:
            status_icon = {
                StepStatus.PENDING: "⏸️",
                StepStatus.IN_PROGRESS: "▶️",
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️"
            }.get(step.status, "❓")
            
            print(f"\n{status_icon} Paso {step.id}: {step.action}")
            if step.tool:
                print(f"   Herramienta: {step.tool}")
                if step.parameters:
                    print(f"   Parámetros: {step.parameters}")
        
        print("\n" + "=" * 60)
    
    def execute_plan(
        self,
        steps: List[PlanStep],
        auto_execute: bool = False
    ) -> List[PlanStep]:
        """
        Ejecuta el plan paso a paso
        
        Args:
            steps: Lista de pasos a ejecutar
            auto_execute: Si es True, ejecuta sin pedir confirmación
        
        Returns:
            Lista de pasos con resultados
        """
        print("\n🚀 Ejecutando plan...\n")
        
        results = []
        context = []  # Contexto acumulado para pasos posteriores
        
        for step in steps:
            # Mostrar paso actual
            print(f"▶️  Paso {step.id}: {step.action}")
            
            # Pedir confirmación si no es auto_execute
            if not auto_execute:
                confirm = input(f"   Ejecutar este paso? (s/n/skip/abort): ").lower()
                if confirm == 'abort':
                    print("⏹️  Ejecución abortada")
                    break
                elif confirm == 'skip':
                    step.status = StepStatus.SKIPPED
                    print("   ⏭️  Paso saltado")
                    results.append(step)
                    continue
                elif confirm not in ['s', 'y', 'yes', 'si', 'sí']:
                    step.status = StepStatus.SKIPPED
                    results.append(step)
                    continue
            
            # Ejecutar paso
            step.status = StepStatus.IN_PROGRESS
            
            try:
                if step.tool:
                    # Ejecutar herramienta
                    tool = self.tool_registry.get_tool(step.tool)
                    if tool:
                        result = tool.execute(**(step.parameters or {}))
                        
                        if result.get("success"):
                            step.status = StepStatus.COMPLETED
                            step.result = result.get("result")
                            context.append(f"Paso {step.id}: {step.result}")
                            print(f"   ✅ Completado")
                        else:
                            step.status = StepStatus.FAILED
                            step.error = result.get("error")
                            print(f"   ❌ Error: {step.error}")
                    else:
                        step.status = StepStatus.FAILED
                        step.error = f"Herramienta '{step.tool}' no encontrada"
                        print(f"   ❌ {step.error}")
                else:
                    # Paso sin herramienta - ejecutar con LLM usando contexto
                    context_str = "\n".join(context[-3:]) if context else ""
                    prompt = f"Contexto previo:\n{context_str}\n\nTarea: {step.action}"
                    
                    response = self.llm_agent.ask(prompt, stream=True)
                    step.status = StepStatus.COMPLETED
                    step.result = response
                    context.append(f"Paso {step.id}: Completado")
                    print()
            
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                print(f"   ❌ Error: {e}")
            
            results.append(step)
        
        # Resumen final
        print("\n📊 Resumen de Ejecución:")
        print("=" * 60)
        completed = sum(1 for s in results if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in results if s.status == StepStatus.FAILED)
        skipped = sum(1 for s in results if s.status == StepStatus.SKIPPED)
        
        print(f"✅ Completados: {completed}")
        print(f"❌ Fallidos: {failed}")
        print(f"⏭️  Saltados: {skipped}")
        print("=" * 60)
        
        return results
    
    def execute_task(self, task: str, auto_execute: bool = False) -> Dict:
        """
        Crea y ejecuta un plan para una tarea (método todo-en-uno)
        
        Args:
            task: Descripción de la tarea
            auto_execute: Si es True, ejecuta sin confirmaciones
        
        Returns:
            Dict con el plan y resultados
        """
        # Crear plan
        steps = self.create_plan(task)
        
        # Mostrar plan
        self.display_plan(steps)
        
        # Pedir confirmación para ejecutar
        if not auto_execute:
            print("\n¿Ejecutar este plan?")
            confirm = input("(s=sí, n=no, a=auto sin confirmaciones): ").lower()
            
            if confirm == 'n':
                print("❌ Ejecución cancelada")
                return {
                    "plan": [s.to_dict() for s in steps],
                    "executed": False
                }
            elif confirm == 'a':
                auto_execute = True
        
        # Ejecutar plan
        results = self.execute_plan(steps, auto_execute=auto_execute)
        
        return {
            "plan": [s.to_dict() for s in steps],
            "results": [s.to_dict() for s in results],
            "executed": True,
            "success": all(s.status == StepStatus.COMPLETED for s in results)
        }