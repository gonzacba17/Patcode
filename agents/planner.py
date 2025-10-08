"""
Task Planner - Divide tareas complejas en pasos más pequeños
"""
from typing import List, Dict, Any
import re


class TaskPlanner:
    """
    Planificador de tareas que descompone peticiones complejas
    en pasos ejecutables secuencialmente
    """
    
    def __init__(self, agent=None):
        """
        Inicializa el planificador
        
        Args:
            agent: Instancia de PatAgent (opcional)
        """
        self.agent = agent
        self.current_plan = []
        self.completed_steps = []
    
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """
        Analiza una tarea y determina su complejidad
        
        Args:
            task: Descripción de la tarea
            
        Returns:
            Dict con análisis de la tarea
        """
        task_lower = task.lower()
        
        # Detectar complejidad
        complexity_indicators = {
            "simple": [
                r'\b(leer|ver|mostrar|listar)\b',
                r'\b(qué (es|hay|contiene))\b'
            ],
            "medium": [
                r'\b(crear|escribir|modificar|actualizar)\b',
                r'\b(agregar|eliminar|cambiar)\b',
                r'\b(buscar y (modificar|crear|actualizar))\b'
            ],
            "complex": [
                r'\b(refactorizar|reorganizar|optimizar)\b',
                r'\b(implementar|desarrollar)\b',
                r'\bmúltiples archivos\b',
                r'\bproyecto completo\b',
                r'\by\s+(luego|después|también)\b'
            ]
        }
        
        complexity = "simple"
        for level, patterns in complexity_indicators.items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    complexity = level
        
        # Detectar múltiples acciones
        action_count = len(re.findall(r'\b(y|además|también|después|luego)\b', task_lower))
        if action_count >= 2:
            complexity = "complex"
        
        return {
            "task": task,
            "complexity": complexity,
            "estimated_steps": self._estimate_steps(task, complexity),
            "requires_planning": complexity in ["medium", "complex"]
        }
    
    def _estimate_steps(self, task: str, complexity: str) -> int:
        """Estima la cantidad de pasos necesarios"""
        if complexity == "simple":
            return 1
        elif complexity == "medium":
            return 2
        else:
            # Contar conjunciones que separan acciones
            conjunctions = len(re.findall(r'\b(y|además|también|después|luego|primero|segundo)\b', 
                                         task.lower()))
            return max(3, conjunctions + 1)
    
    def create_plan(self, task: str) -> List[Dict[str, Any]]:
        """
        Crea un plan de pasos para ejecutar la tarea
        
        Args:
            task: Descripción de la tarea
            
        Returns:
            Lista de pasos a ejecutar
        """
        analysis = self.analyze_task(task)
        
        if not analysis["requires_planning"]:
            # Tarea simple, un solo paso
            return [{
                "step": 1,
                "description": task,
                "type": "direct",
                "status": "pending"
            }]
        
        # Descomponer tarea compleja
        steps = self._decompose_task(task)
        
        self.current_plan = steps
        return steps
    
    def _decompose_task(self, task: str) -> List[Dict[str, Any]]:
        """
        Descompone una tarea en pasos específicos
        
        Args:
            task: Tarea compleja
            
        Returns:
            Lista de pasos
        """
        steps = []
        task_lower = task.lower()
        
        # Patrón 1: "Leer X y luego Y"
        if re.search(r'(leer|ver).+(y|luego|después).+(crear|modificar|escribir)', task_lower):
            steps.append({
                "step": 1,
                "description": "Leer y analizar el archivo existente",
                "type": "read",
                "status": "pending"
            })
            steps.append({
                "step": 2,
                "description": "Modificar o crear el archivo basándose en el análisis",
                "type": "write",
                "status": "pending"
            })
        
        # Patrón 2: "Crear múltiples archivos"
        elif 'múltiples' in task_lower or 'varios' in task_lower:
            # Detectar cuántos archivos
            file_count = len(re.findall(r'\b\w+\.(py|js|txt|md|json)', task))
            for i in range(max(2, file_count)):
                steps.append({
                    "step": i + 1,
                    "description": f"Crear archivo {i + 1}",
                    "type": "write",
                    "status": "pending"
                })
        
        # Patrón 3: "Buscar y modificar"
        elif re.search(r'buscar.+(y|luego).+(modificar|cambiar|actualizar)', task_lower):
            steps.append({
                "step": 1,
                "description": "Buscar archivos o código relevante",
                "type": "search",
                "status": "pending"
            })
            steps.append({
                "step": 2,
                "description": "Leer archivos encontrados",
                "type": "read",
                "status": "pending"
            })
            steps.append({
                "step": 3,
                "description": "Modificar los archivos",
                "type": "write",
                "status": "pending"
            })
        
        # Patrón 4: División genérica por conjunciones
        else:
            # Dividir por conectores
            parts = re.split(r'\b(y|además|también|después|luego|primero|segundo|tercero)\b', 
                           task, flags=re.IGNORECASE)
            
            # Filtrar partes vacías y conectores
            meaningful_parts = [p.strip() for p in parts if p.strip() and 
                              p.lower() not in ['y', 'además', 'también', 'después', 'luego', 
                                               'primero', 'segundo', 'tercero']]
            
            for i, part in enumerate(meaningful_parts, 1):
                step_type = "direct"
                if any(word in part.lower() for word in ['leer', 'ver', 'mostrar']):
                    step_type = "read"
                elif any(word in part.lower() for word in ['crear', 'escribir', 'modificar']):
                    step_type = "write"
                elif any(word in part.lower() for word in ['buscar', 'encontrar']):
                    step_type = "search"
                
                steps.append({
                    "step": i,
                    "description": part,
                    "type": step_type,
                    "status": "pending"
                })
        
        return steps if steps else [{
            "step": 1,
            "description": task,
            "type": "direct",
            "status": "pending"
        }]
    
    def mark_step_complete(self, step_number: int, result: Any = None):
        """
        Marca un paso como completado
        
        Args:
            step_number: Número del paso
            result: Resultado de la ejecución (opcional)
        """
        for step in self.current_plan:
            if step["step"] == step_number:
                step["status"] = "completed"
                step["result"] = result
                self.completed_steps.append(step)
                break
    
    def mark_step_failed(self, step_number: int, error: str):
        """
        Marca un paso como fallido
        
        Args:
            step_number: Número del paso
            error: Descripción del error
        """
        for step in self.current_plan:
            if step["step"] == step_number:
                step["status"] = "failed"
                step["error"] = error
                break
    
    def get_next_step(self) -> Dict[str, Any]:
        """
        Obtiene el siguiente paso pendiente
        
        Returns:
            Dict con información del paso o None si no hay más pasos
        """
        for step in self.current_plan:
            if step["status"] == "pending":
                return step
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Obtiene el progreso actual del plan
        
        Returns:
            Dict con estadísticas de progreso
        """
        total = len(self.current_plan)
        completed = sum(1 for s in self.current_plan if s["status"] == "completed")
        failed = sum(1 for s in self.current_plan if s["status"] == "failed")
        pending = sum(1 for s in self.current_plan if s["status"] == "pending")
        
        return {
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }
    
    def print_plan(self):
        """Imprime el plan actual de forma legible"""
        if not self.current_plan:
            print("📋 No hay plan activo")
            return
        
        print("\n📋 PLAN DE EJECUCIÓN:")
        print("=" * 60)
        
        for step in self.current_plan:
            status_icon = {
                "pending": "⏳",
                "completed": "✅",
                "failed": "❌"
            }.get(step["status"], "❓")
            
            print(f"{status_icon} Paso {step['step']}: {step['description']}")
            if step.get("error"):
                print(f"   Error: {step['error']}")
        
        progress = self.get_progress()
        print("=" * 60)
        print(f"Progreso: {progress['completed']}/{progress['total_steps']} "
              f"({progress['progress_percent']:.1f}%)")
        print()
    
    def reset(self):
        """Reinicia el planificador"""
        self.current_plan = []
        self.completed_steps = []