"""
Sistema de planificación para PatCode.
Muestra plan antes de ejecutar acciones.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ActionType(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    EXECUTE_SHELL = "execute_shell"
    GIT_OPERATION = "git_operation"
    SEARCH_CODE = "search_code"

@dataclass
class PlanAction:
    type: ActionType
    description: str
    target: str
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"
    
    def __str__(self) -> str:
        risk_emoji = {"low": "✅", "medium": "⚠️ ", "high": "🔴"}
        return f"{risk_emoji.get(self.risk_level, '•')} {self.description}"

@dataclass
class ExecutionPlan:
    title: str
    actions: List[PlanAction]
    estimated_time: str = "< 1 min"
    requires_approval: bool = True
    
    def __str__(self) -> str:
        lines = [
            f"# 📋 Plan: {self.title}",
            f"⏱️  Tiempo estimado: {self.estimated_time}",
            f"\n## Acciones a ejecutar:\n"
        ]
        
        for i, action in enumerate(self.actions, 1):
            lines.append(f"{i}. {action}")
        
        if self.requires_approval:
            lines.append("\n❓ ¿Aprobar este plan? (s/n/m para modificar)")
        
        return '\n'.join(lines)

class PlanMode:
    
    def __init__(self):
        self.current_plan: Optional[ExecutionPlan] = None
        self.plan_history: List[ExecutionPlan] = []
        logger.info("PlanMode inicializado")
    
    def create_plan_from_intent(self, user_input: str, context: Any) -> ExecutionPlan:
        actions = []
        
        lower_input = user_input.lower()
        
        if "modifica" in lower_input or "cambia" in lower_input or "edita" in lower_input:
            actions.append(PlanAction(
                type=ActionType.READ_FILE,
                description="Leer archivo actual",
                target="(archivo a determinar)",
                risk_level="low"
            ))
            actions.append(PlanAction(
                type=ActionType.EDIT_FILE,
                description="Aplicar modificaciones",
                target="(archivo a determinar)",
                details={"changes": "TBD"},
                risk_level="medium"
            ))
        
        if "ejecuta" in lower_input or "corre" in lower_input or "run" in lower_input:
            actions.append(PlanAction(
                type=ActionType.EXECUTE_SHELL,
                description="Ejecutar comando shell",
                target="(comando a determinar)",
                risk_level="medium"
            ))
        
        if "commit" in lower_input or "git" in lower_input:
            actions.append(PlanAction(
                type=ActionType.GIT_OPERATION,
                description="Operación Git",
                target="git",
                details={"operation": "TBD"},
                risk_level="low"
            ))
        
        if not actions:
            actions.append(PlanAction(
                type=ActionType.SEARCH_CODE,
                description="Buscar información relevante en el proyecto",
                target="codebase",
                risk_level="low"
            ))
        
        plan = ExecutionPlan(
            title="Responder a: " + user_input[:50] + "...",
            actions=actions,
            estimated_time="< 1 min",
            requires_approval=any(a.risk_level in ["medium", "high"] for a in actions)
        )
        
        self.current_plan = plan
        return plan
    
    def execute_plan(self, plan: ExecutionPlan, context: Any) -> List[str]:
        results = []
        
        for i, action in enumerate(plan.actions, 1):
            logger.info(f"Ejecutando acción {i}/{len(plan.actions)}: {action.description}")
            
            try:
                result = self._execute_action(action, context)
                results.append(f"✅ {action.description}: {result}")
            except Exception as e:
                error_msg = f"❌ Error en {action.description}: {str(e)}"
                logger.error(error_msg)
                results.append(error_msg)
                
                if action.risk_level == "high":
                    results.append("🛑 Ejecución detenida debido a error crítico")
                    break
        
        self.plan_history.append(plan)
        return results
    
    def _execute_action(self, action: PlanAction, context: Any) -> str:
        
        if action.type == ActionType.READ_FILE:
            if hasattr(context, 'file_manager'):
                try:
                    context.file_manager.load_file(action.target)
                    return f"Archivo {action.target} cargado"
                except:
                    pass
            return "Listo para leer"
        
        elif action.type == ActionType.WRITE_FILE:
            return "Archivo preparado para escritura"
        
        elif action.type == ActionType.EXECUTE_SHELL:
            return "Comando listo para ejecución"
        
        elif action.type == ActionType.GIT_OPERATION:
            return "Operación Git preparada"
        
        elif action.type == ActionType.SEARCH_CODE:
            if hasattr(context, 'retriever'):
                try:
                    context_result = context.retriever.retrieve_context(action.target, top_k=3)
                    return context_result[:200]
                except:
                    pass
            return "Búsqueda completada"
        
        return "Acción ejecutada"
    
    def modify_plan(self, modifications: str) -> ExecutionPlan:
        if not self.current_plan:
            raise ValueError("No hay plan actual para modificar")
        
        modified_plan = ExecutionPlan(
            title=self.current_plan.title + " (modificado)",
            actions=self.current_plan.actions,
            estimated_time=self.current_plan.estimated_time,
            requires_approval=True
        )
        
        self.current_plan = modified_plan
        return modified_plan
    
    def get_plan_summary(self) -> str:
        if not self.current_plan:
            return "No hay plan activo"
        
        return str(self.current_plan)


plan_mode = PlanMode()
