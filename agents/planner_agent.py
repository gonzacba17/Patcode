# agents/planner_agent.py

class PlannerAgent:
    """Agente que planifica antes de actuar"""
    
    PLANNING_PROMPT = """
Eres un asistente de programación experto. Antes de realizar cualquier acción,
debes crear un plan detallado.

Tarea del usuario: {user_request}

Contexto del proyecto:
{project_context}

Crea un plan paso a paso para completar esta tarea. Para cada paso, indica:
1. Qué archivo(s) necesitas leer o modificar
2. Qué comandos necesitas ejecutar
3. Qué validación hacer después

Formato tu plan así:
PLAN:
- Paso 1: [descripción]
  - Acción: [read_file/edit_file/run_command]
  - Archivo/Comando: [detalles]
- Paso 2: ...

Después de crear el plan, ejecutarás cada paso uno por uno.
"""
    
    def create_plan(self, user_request: str) -> list:
        """Crea un plan de acción estructurado"""
        # Obtener contexto del proyecto
        context = self._gather_project_context()
        
        # Generar plan
        prompt = self.PLANNING_PROMPT.format(
            user_request=user_request,
            project_context=context
        )
        
        plan_text = self.model.generate(prompt)
        
        # Parsear plan en pasos ejecutables
        steps = self._parse_plan(plan_text)
        return steps
    
    def execute_plan(self, steps: list):
        """Ejecuta el plan paso a paso con validación"""
        for i, step in enumerate(steps):
            print(f"\n[Paso {i+1}/{len(steps)}] {step['description']}")
            
            # Ejecutar acción
            result = self._execute_step(step)
            
            # Mostrar resultado
            print(f"✓ Completado: {result}")
            
            # Validar si es necesario
            if step.get('validation'):
                validation_result = self._validate_step(step, result)
                if not validation_result:
                    print(f"⚠ Validación falló, ajustando...")
                    self._adjust_and_retry(step)