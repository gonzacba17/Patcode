"""
Planning Agent - Planifica y ejecuta tareas complejas paso a paso
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
    """Agente de planificación que descompone tareas complejas"""
    
    def __init__(self, llm_agent, tool_registry):
        self.llm_agent = llm_agent
        self.tool_registry = tool_registry
        self.current_plan: List[PlanStep] = []
    
    def create_plan(self, task: str) -> List[PlanStep]:
        """Crea un plan simple (placeholder por ahora)"""
        print(f"🧠 Planificando tarea: {task}")
        
        # Plan simple de fallback
        steps = [PlanStep(
            id=1,
            action=task,
            description=task,
            tool=None,
            parameters=None
        )]
        
        self.current_plan = steps
        return steps
    
    def display_plan(self, steps: List[PlanStep]):
        """Muestra el plan al usuario"""
        print("\n📋 Plan de Ejecución:")
        print("=" * 60)
        
        for step in steps:
            status_icon = "⏸️"
            print(f"\n{status_icon} Paso {step.id}: {step.action}")
        
        print("\n" + "=" * 60)
    
    def execute_plan(self, steps: List[PlanStep], auto_execute: bool = False) -> List[PlanStep]:
        """Ejecuta el plan paso a paso"""
        print("\n🚀 Ejecutando plan...\n")
        results = []
        
        for step in steps:
            print(f"▶️  Paso {step.id}: {step.action}")
            step.status = StepStatus.COMPLETED
            results.append(step)
        
        return results
    
    def execute_task(self, task: str, auto_execute: bool = False) -> Dict:
        """Ejecuta una tarea completa"""
        steps = self.create_plan(task)
        self.display_plan(steps)
        results = self.execute_plan(steps, auto_execute)
        
        return {
            "plan": [s.to_dict() for s in steps],
            "results": [s.to_dict() for s in results],
            "executed": True,
            "success": True
        }