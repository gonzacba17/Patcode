"""
Orchestrator Agentic - FASE 3: Sistema Agentic Avanzado

Orchestrator con loop agentic completo: Planning → Execution → Reflection
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from agents.models import Task, Step, StepType, TaskStatus, ExecutionContext
from agents.prompts import planning, code_generation, debugging, testing, reflection
from llm.provider_manager import ProviderManager, LLMError
from tools.file_operations import FileOperationsTool
from tools.shell_executor import ShellExecutor
from tools.code_analyzer import CodeAnalyzer
from agents.memory.project_memory import ProjectMemory


logger = logging.getLogger(__name__)


class AgenticOrchestrator:
    """
    Orchestrator agentic que ejecuta tareas de forma autónoma.
    
    Loop agentic:
    1. Recibe tarea
    2. PLANNING: Descompone en steps
    3. EXECUTION: Ejecuta cada step
    4. REFLECTION: Evalúa si está completo
    5. Re-planifica si es necesario (hasta max_iterations)
    """
    
    def __init__(
        self,
        llm_manager: ProviderManager,
        project_root: str = ".",
        max_iterations: int = 10,
        enable_shell: bool = True
    ):
        """
        Inicializa el orchestrator agentic.
        
        Args:
            llm_manager: Gestor de LLMs
            project_root: Directorio raíz del proyecto
            max_iterations: Máximo de iteraciones del loop
            enable_shell: Si habilitar shell executor
        """
        self.llm_manager = llm_manager
        self.project_root = Path(project_root).absolute()
        self.max_iterations = max_iterations
        
        self.file_ops = FileOperationsTool(str(self.project_root))
        self.code_analyzer = CodeAnalyzer()
        self.project_memory = ProjectMemory(str(self.project_root))
        
        if enable_shell:
            self.shell_executor = ShellExecutor(
                working_dir=str(self.project_root),
                timeout=300
            )
        else:
            self.shell_executor = None
        
        self.context = ExecutionContext(
            project_root=str(self.project_root),
            working_directory=str(self.project_root)
        )
        
        logger.info(f"🚀 AgenticOrchestrator initialized at {self.project_root}")
    
    def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Task:
        """
        Ejecuta una tarea completa de forma autónoma.
        
        Args:
            task_description: Descripción de la tarea
            context: Contexto adicional
            
        Returns:
            Task con el resultado de la ejecución
        """
        logger.info(f"📋 Starting task: {task_description}")
        
        task = Task(
            description=task_description,
            context=context or {},
            max_iterations=self.max_iterations
        )
        task.start()
        
        try:
            while task.should_continue():
                task.iterations += 1
                logger.info(f"🔄 Iteration {task.iterations}/{task.max_iterations}")
                
                if not task.steps or self._should_replan(task):
                    logger.info("📝 Planning phase...")
                    self._plan_task(task)
                
                logger.info("⚙️ Execution phase...")
                self._execute_steps(task)
                
                logger.info("🤔 Reflection phase...")
                is_complete, reflection = self._reflect_on_progress(task)
                
                if is_complete:
                    logger.info("✅ Task completed successfully!")
                    task.complete(reflection)
                    break
                
                elif task.iterations >= task.max_iterations:
                    logger.warning("⚠️ Max iterations reached")
                    task.fail(f"Max iterations reached. Last reflection: {reflection}")
                    break
                
                else:
                    logger.info("🔄 Task not complete, re-planning...")
                    task.steps = []
                    task.current_step_index = 0
            
            return task
            
        except Exception as e:
            logger.error(f"💥 Error executing task: {e}", exc_info=True)
            task.fail(str(e))
            return task
    
    def _plan_task(self, task: Task):
        """Fase de planning: descompone la tarea en steps."""
        try:
            project_context = self._gather_project_context()
            recent_changes = self.context.to_summary()
            
            system_prompt, user_prompt = planning.create_planning_prompt(
                task_description=task.description,
                project_context=project_context,
                recent_changes=recent_changes
            )
            
            response = self.llm_manager.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                strategy="complex"
            )
            
            plan = self._parse_plan_response(response.content)
            
            for step_data in plan.get("steps", []):
                step = Step(
                    type=StepType(step_data.get("type", "analysis")),
                    description=step_data["description"],
                    tool_name=step_data.get("tool_name"),
                    tool_input=step_data.get("tool_input", {}),
                    expected_output=step_data.get("expected_output")
                )
                task.add_step(step)
            
            logger.info(f"📋 Created plan with {len(task.steps)} steps")
            
        except Exception as e:
            logger.error(f"Error in planning: {e}")
            task.add_step(Step(
                type=StepType.ANALYSIS,
                description="Analyze project structure",
                tool_name="code_analyze"
            ))
    
    def _execute_steps(self, task: Task):
        """Fase de ejecución: ejecuta cada step del plan."""
        while task.current_step_index < len(task.steps):
            step = task.get_current_step()
            if not step:
                break
            
            logger.info(f"▶️ Step {task.current_step_index + 1}/{len(task.steps)}: {step.description}")
            
            step.start()
            
            try:
                if step.tool_name == "file_read":
                    result = self._execute_file_read(step)
                elif step.tool_name == "file_write":
                    result = self._execute_file_write(step)
                elif step.tool_name == "file_edit":
                    result = self._execute_file_edit(step)
                elif step.tool_name == "code_analyze":
                    result = self._execute_code_analyze(step)
                elif step.tool_name == "shell_execute":
                    result = self._execute_shell_command(step)
                elif step.tool_name == "generate_code":
                    result = self._execute_code_generation(step, task)
                elif step.tool_name == "generate_tests":
                    result = self._execute_test_generation(step, task)
                elif step.tool_name == "debug":
                    result = self._execute_debugging(step, task)
                else:
                    result = f"Unknown tool: {step.tool_name}"
                    logger.warning(f"⚠️ {result}")
                
                step.complete(result)
                logger.info(f"✅ Step completed in {step.duration:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Step failed: {e}")
                step.fail(str(e))
                
                if self._is_critical_step(step):
                    logger.error("Critical step failed, stopping execution")
                    break
            
            task.advance_step()
    
    def _reflect_on_progress(self, task: Task) -> tuple:
        """Fase de reflection: evalúa si la tarea está completa."""
        try:
            steps_summary = self._summarize_steps(task.steps)
            results_summary = self._summarize_results(task.steps)
            
            system_prompt, user_prompt = reflection.create_reflection_prompt(
                task_description=task.description,
                steps_completed=steps_summary,
                results=results_summary,
                files_modified=self.context.files_modified,
                test_results=str(self.context.test_results)
            )
            
            response = self.llm_manager.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                strategy="complex"
            )
            
            reflection_data = self._parse_reflection_response(response.content)
            
            is_complete = reflection_data.get("task_complete", False)
            reasoning = reflection_data.get("reasoning", "")
            
            logger.info(f"🤔 Reflection: {'Complete' if is_complete else 'Incomplete'}")
            logger.info(f"Reasoning: {reasoning}")
            
            return is_complete, reflection_data
            
        except Exception as e:
            logger.error(f"Error in reflection: {e}")
            all_success = all(s.status == TaskStatus.COMPLETED for s in task.steps)
            return all_success, {"reasoning": "Fallback reflection"}
    
    def _execute_file_read(self, step: Step) -> str:
        """Ejecuta operación de lectura de archivo."""
        file_path = step.tool_input.get("file_path", step.tool_input.get("path"))
        result = self.file_ops.read_file(file_path)
        if result.get("success"):
            return f"Read {len(result['content'])} characters from {file_path}"
        return f"Failed to read {file_path}: {result.get('error')}"
    
    def _execute_file_write(self, step: Step) -> str:
        """Ejecuta operación de escritura de archivo."""
        file_path = step.tool_input.get("file_path", step.tool_input.get("path"))
        content = step.tool_input.get("content")
        result = self.file_ops.write_file(file_path, content)
        if result.get("success"):
            self.context.add_file_modified(file_path)
            self.project_memory.record_change(file_path, "write", "File created/updated")
            return f"Wrote to {file_path}"
        return f"Failed to write {file_path}: {result.get('error')}"
    
    def _execute_file_edit(self, step: Step) -> str:
        """Ejecuta operación de edición de archivo."""
        file_path = step.tool_input.get("file_path", step.tool_input.get("path"))
        line_start = step.tool_input.get("line_start")
        line_end = step.tool_input.get("line_end")
        new_content = step.tool_input.get("new_content")
        
        result = self.file_ops.edit_file(file_path, line_start, line_end, new_content)
        if result.get("success"):
            self.context.add_file_modified(file_path)
            return f"Edited {file_path}"
        return f"Failed to edit {file_path}: {result.get('error')}"
    
    def _execute_code_analyze(self, step: Step) -> str:
        """Ejecuta análisis de código."""
        target = step.tool_input.get("target", ".")
        
        if Path(target).is_file():
            result = self.code_analyzer.analyze_file(target)
            if result:
                self.context.analysis_cache[target] = result.to_dict()
                return result.summary
            return f"Failed to analyze {target}"
        
        elif Path(target).is_dir():
            results = self.code_analyzer.analyze_directory(target, recursive=False)
            summary = f"Analyzed {len(results)} files"
            for file_path, result in results.items():
                self.context.analysis_cache[file_path] = result.to_dict()
            return summary
        
        return f"Invalid target: {target}"
    
    def _execute_shell_command(self, step: Step) -> str:
        """Ejecuta comando de shell."""
        if not self.shell_executor:
            return "Shell executor disabled"
        
        command = step.tool_input.get("command")
        result = self.shell_executor.execute(command)
        self.context.add_command_executed(command)
        
        if result.success:
            return f"Command succeeded: {result.stdout[:200]}"
        else:
            return f"Command failed (exit {result.exit_code}): {result.stderr[:200]}"
    
    def _execute_code_generation(self, step: Step, task: Task) -> str:
        """Ejecuta generación de código."""
        try:
            context_info = self._gather_code_generation_context(step)
            
            system_prompt, user_prompt = code_generation.create_code_generation_prompt(
                task_description=step.description,
                context=context_info,
                existing_code=step.tool_input.get("existing_code", ""),
                requirements=step.tool_input.get("requirements", ""),
                language=step.tool_input.get("language", "python")
            )
            
            response = self.llm_manager.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                strategy="code_generation"
            )
            
            code = self._extract_code_from_response(response.content)
            
            if "output_file" in step.tool_input:
                output_file = step.tool_input["output_file"]
                self.file_ops.write_file(output_file, code)
                self.context.add_file_modified(output_file)
                return f"Generated code written to {output_file}"
            
            return f"Generated {len(code)} characters of code"
            
        except Exception as e:
            return f"Code generation failed: {e}"
    
    def _execute_test_generation(self, step: Step, task: Task) -> str:
        """Ejecuta generación de tests."""
        try:
            code_to_test = step.tool_input.get("code_to_test", "")
            target_name = step.tool_input.get("target_name", "")
            
            system_prompt, user_prompt = testing.create_testing_prompt(
                code_to_test=code_to_test,
                target_name=target_name,
                requirements=step.tool_input.get("requirements", ""),
                framework=step.tool_input.get("framework", "pytest")
            )
            
            response = self.llm_manager.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                strategy="code_generation"
            )
            
            test_code = self._extract_code_from_response(response.content)
            
            if "output_file" in step.tool_input:
                output_file = step.tool_input["output_file"]
                self.file_ops.write_file(output_file, test_code)
                self.context.add_file_modified(output_file)
                return f"Generated tests written to {output_file}"
            
            return f"Generated {len(test_code)} characters of test code"
            
        except Exception as e:
            return f"Test generation failed: {e}"
    
    def _execute_debugging(self, step: Step, task: Task) -> str:
        """Ejecuta debugging."""
        try:
            error_message = step.tool_input.get("error_message", "")
            stack_trace = step.tool_input.get("stack_trace", "")
            relevant_code = step.tool_input.get("relevant_code", "")
            
            system_prompt, user_prompt = debugging.create_debugging_prompt(
                error_message=error_message,
                stack_trace=stack_trace,
                relevant_code=relevant_code,
                context=str(task.context)
            )
            
            response = self.llm_manager.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                strategy="complex"
            )
            
            debug_result = self._parse_debug_response(response.content)
            
            return debug_result.get("root_cause", "Debug analysis completed")
            
        except Exception as e:
            return f"Debugging failed: {e}"
    
    def _gather_project_context(self) -> str:
        """Recopila contexto del proyecto."""
        parts = [f"Project root: {self.project_root}"]
        
        recent_files = self.project_memory.get_recent_files(limit=5)
        if recent_files:
            parts.append(f"Recent files: {', '.join(recent_files)}")
        
        if self.context.files_modified:
            parts.append(f"Modified this session: {', '.join(self.context.files_modified)}")
        
        return "\n".join(parts)
    
    def _gather_code_generation_context(self, step: Step) -> str:
        """Recopila contexto para generación de código."""
        parts = []
        
        if self.context.analysis_cache:
            parts.append("Analyzed files:")
            for file_path, analysis in list(self.context.analysis_cache.items())[:3]:
                parts.append(f"- {file_path}: {analysis.get('summary', 'N/A')}")
        
        return "\n".join(parts)
    
    def _should_replan(self, task: Task) -> bool:
        """Determina si se debe re-planificar."""
        failed_steps = [s for s in task.steps if s.status == TaskStatus.FAILED]
        return len(failed_steps) > 0 and task.iterations < task.max_iterations
    
    def _is_critical_step(self, step: Step) -> bool:
        """Determina si un step es crítico."""
        return step.type != StepType.ANALYSIS
    
    def _summarize_steps(self, steps: List[Step]) -> str:
        """Genera resumen de los steps ejecutados."""
        lines = []
        for i, step in enumerate(steps, 1):
            status_emoji = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.IN_PROGRESS: "⏳",
                TaskStatus.PENDING: "⏸️"
            }.get(step.status, "❓")
            
            lines.append(f"{i}. {status_emoji} {step.description}")
        
        return "\n".join(lines)
    
    def _summarize_results(self, steps: List[Step]) -> str:
        """Genera resumen de los resultados."""
        completed = [s for s in steps if s.status == TaskStatus.COMPLETED]
        failed = [s for s in steps if s.status == TaskStatus.FAILED]
        
        parts = [f"Completed: {len(completed)}/{len(steps)} steps"]
        
        if failed:
            parts.append(f"Failed: {len(failed)} steps")
            for step in failed:
                parts.append(f"  - {step.description}: {step.error}")
        
        return "\n".join(parts)
    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """Parsea la respuesta del planning."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except:
            logger.warning("Failed to parse planning response as JSON")
            return {"steps": []}
    
    def _parse_reflection_response(self, response: str) -> Dict[str, Any]:
        """Parsea la respuesta del reflection."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except:
            return {"task_complete": False, "reasoning": "Parse error"}
    
    def _parse_debug_response(self, response: str) -> Dict[str, Any]:
        """Parsea la respuesta del debugging."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except:
            return {"root_cause": response}
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extrae código de una respuesta."""
        code_block_match = re.search(r'```[\w]*\n(.*?)\n```', response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return response
