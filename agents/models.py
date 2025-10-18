"""
Models - FASE 3: Orchestrator Agentic

Modelos de datos para el sistema agentic.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
import time


class TaskStatus(Enum):
    """Estados de una tarea."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN_INPUT = "requires_human_input"


class StepType(Enum):
    """Tipos de pasos."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    CODE_GENERATION = "code_generation"
    FILE_OPERATION = "file_operation"
    SHELL_COMMAND = "shell_command"
    TESTING = "testing"
    DEBUGGING = "debugging"
    REFLECTION = "reflection"


@dataclass
class Step:
    """Un paso en la ejecución de una tarea."""
    type: StepType
    description: str
    tool_name: Optional[str] = None
    tool_input: Dict[str, Any] = field(default_factory=dict)
    expected_output: Optional[str] = None
    
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def start(self):
        """Marca el paso como iniciado."""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = time.time()
    
    def complete(self, result: Any):
        """Marca el paso como completado."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.end_time = time.time()
    
    def fail(self, error: str):
        """Marca el paso como fallido."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.end_time = time.time()
    
    @property
    def duration(self) -> Optional[float]:
        """Duración del paso en segundos."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class Task:
    """Una tarea a ejecutar."""
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    steps: List[Step] = field(default_factory=list)
    
    status: TaskStatus = TaskStatus.PENDING
    current_step_index: int = 0
    iterations: int = 0
    max_iterations: int = 10
    
    final_result: Optional[Any] = None
    error_message: Optional[str] = None
    
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def start(self):
        """Inicia la tarea."""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = time.time()
    
    def complete(self, result: Any):
        """Completa la tarea."""
        self.status = TaskStatus.COMPLETED
        self.final_result = result
        self.end_time = time.time()
    
    def fail(self, error: str):
        """Falla la tarea."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.end_time = time.time()
    
    def get_current_step(self) -> Optional[Step]:
        """Obtiene el paso actual."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def advance_step(self):
        """Avanza al siguiente paso."""
        self.current_step_index += 1
    
    def add_step(self, step: Step):
        """Añade un nuevo paso al plan."""
        self.steps.append(step)
    
    def should_continue(self) -> bool:
        """Verifica si debe continuar ejecutando."""
        return (
            self.status == TaskStatus.IN_PROGRESS and
            self.iterations < self.max_iterations and
            self.current_step_index < len(self.steps)
        )
    
    @property
    def duration(self) -> Optional[float]:
        """Duración total de la tarea."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def progress_percentage(self) -> float:
        """Porcentaje de progreso."""
        if not self.steps:
            return 0.0
        return (self.current_step_index / len(self.steps)) * 100


@dataclass
class ExecutionContext:
    """Contexto de ejecución para el orchestrator."""
    project_root: str
    working_directory: str
    files_modified: List[str] = field(default_factory=list)
    commands_executed: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    analysis_cache: Dict[str, Any] = field(default_factory=dict)
    
    def add_file_modified(self, file_path: str):
        """Registra un archivo modificado."""
        if file_path not in self.files_modified:
            self.files_modified.append(file_path)
    
    def add_command_executed(self, command: str):
        """Registra un comando ejecutado."""
        self.commands_executed.append(command)
    
    def to_summary(self) -> str:
        """Genera un resumen del contexto."""
        parts = []
        
        if self.files_modified:
            parts.append(f"Modified {len(self.files_modified)} files")
        
        if self.commands_executed:
            parts.append(f"Executed {len(self.commands_executed)} commands")
        
        if self.test_results:
            parts.append(f"Test results: {self.test_results}")
        
        return " | ".join(parts) if parts else "No changes made"
