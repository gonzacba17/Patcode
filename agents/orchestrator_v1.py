"""
Orchestrator - FASE 1: Core del Sistema PatCode

Cerebro principal del sistema agentico que coordina la ejecución de tareas,
maneja el ciclo de planificar → ejecutar → validar, y utiliza las tools disponibles.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from tools.file_operations import FileOperationsTool
from agents.memory.project_memory import ProjectMemory


logger = logging.getLogger(__name__)


@dataclass
class Action:
    """Representa una acción que el agente quiere ejecutar."""
    thought: str
    action: str
    parameters: Dict[str, Any]


@dataclass
class ActionResult:
    """Resultado de ejecutar una acción."""
    success: bool
    output: Any
    error: Optional[str] = None


class Orchestrator:
    """
    Orquestador principal del sistema agentico.
    
    Coordina:
    - Comunicación con el LLM
    - Ejecución de tools
    - Memoria del proyecto
    - Ciclo de agente: planificar → ejecutar → validar
    """
    
    SYSTEM_PROMPT = """You are PatCode, an autonomous coding agent. Your job is to complete programming tasks by using available tools.

AVAILABLE TOOLS:
- read_file(path): Read file contents
- write_file(path, content): Create or overwrite a file
- edit_file(path, line_start, line_end, new_content): Edit specific lines
- list_files(directory, pattern): List files matching pattern
- create_directory(path): Create a directory

WORKFLOW:
1. Understand the user's task
2. Think step-by-step about what needs to be done
3. Use tools to read necessary files
4. Make changes carefully
5. Validate your work

RESPONSE FORMAT:
Always respond with a JSON object:
{{
  "thought": "Your reasoning about what to do next",
  "action": "tool_name",
  "parameters": {{"param": "value"}},
  "final_answer": null
}}

If the task is complete, set "final_answer" to your message instead of "action".

IMPORTANT:
- Always use forward slashes (/) in file paths
- Line numbers in edit_file are 1-indexed
- Be careful with indentation when editing code
- Validate your changes by reading the file after editing

Current project context:
{project_summary}

Conversation history:
{conversation}

User request: {user_input}

Your response (JSON only):"""
    
    def __init__(self, llm_client, workspace_root: str):
        """
        Inicializa el orquestador.
        
        Args:
            llm_client: Cliente LLM (debe tener método generate(messages))
            workspace_root: Directorio raíz del workspace
        """
        self.llm = llm_client
        self.workspace_root = workspace_root
        
        self.file_tool = FileOperationsTool(workspace_root)
        
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "edit_file": self._tool_edit_file,
            "list_files": self._tool_list_files,
            "create_directory": self._tool_create_directory,
        }
        
        self.memory = ProjectMemory(workspace_root)
        self.conversation_history = []
        
        self.memory.index_project()
        
        logger.info(f"Orchestrator initialized for workspace: {workspace_root}")
    
    def execute_task(self, user_input: str, max_iterations: int = 10) -> str:
        """
        Ejecuta una tarea completa usando ciclo de agente.
        
        Args:
            user_input: La tarea del usuario
            max_iterations: Máximo de iteraciones para evitar loops infinitos
            
        Returns:
            Respuesta final al usuario
        """
        logger.info(f"Executing task: {user_input[:100]}...")
        
        self.memory.set_current_task(user_input)
        self.conversation_history.append({"role": "user", "content": user_input})
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Iteration {iteration}/{max_iterations}")
            
            prompt = self._build_prompt(user_input)
            
            try:
                llm_response = self._call_llm(prompt)
                logger.debug(f"LLM response: {llm_response[:200]}...")
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"Error calling LLM: {str(e)}"
            
            try:
                action_data = self._parse_llm_response(llm_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Response was: {llm_response}")
                return f"Error: LLM returned invalid JSON. Response: {llm_response[:500]}"
            
            if "final_answer" in action_data and action_data["final_answer"]:
                final_answer = action_data["final_answer"]
                logger.info(f"Task completed: {final_answer[:100]}...")
                return final_answer
            
            if "action" not in action_data:
                logger.error("LLM response missing 'action' field")
                return f"Error: LLM response missing action. Response: {llm_response[:500]}"
            
            action = Action(
                thought=action_data.get("thought", ""),
                action=action_data.get("action", ""),
                parameters=action_data.get("parameters", {})
            )
            
            logger.info(f"Executing action: {action.action} - {action.thought[:100]}")
            
            result = self._execute_action(action)
            
            if result.success:
                file_path = action.parameters.get("path", "unknown")
                self.memory.record_change(file_path, action.action, action.thought)
            
            self.conversation_history.append({
                "role": "assistant",
                "thought": action.thought,
                "action": action.action,
                "result": result.output if result.success else result.error,
                "success": result.success
            })
        
        logger.warning(f"Task exceeded max iterations ({max_iterations})")
        return "Task exceeded maximum iterations. Please try breaking it into smaller steps."
    
    def _build_prompt(self, user_input: str) -> str:
        """
        Construye el prompt con todo el contexto.
        
        Args:
            user_input: Input del usuario
            
        Returns:
            Prompt completo para el LLM
        """
        context = self.memory.get_context_summary()
        
        conversation_entries = []
        for entry in self.conversation_history[-5:]:
            if entry["role"] == "user":
                conversation_entries.append(f"User: {entry['content']}")
            elif entry["role"] == "assistant":
                action_info = f"Action: {entry.get('action', 'unknown')}"
                result_info = f"Result: {str(entry.get('result', ''))[:200]}"
                conversation_entries.append(f"Assistant: {action_info} | {result_info}")
        
        conversation = "\n".join(conversation_entries) if conversation_entries else "No previous conversation"
        
        prompt = self.SYSTEM_PROMPT.format(
            project_summary=context,
            conversation=conversation,
            user_input=user_input
        )
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Llama al LLM con el prompt.
        
        Args:
            prompt: Prompt a enviar
            
        Returns:
            Respuesta del LLM
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.generate(messages)
            return response
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    def _parse_llm_response(self, llm_response: str) -> Dict:
        """
        Parsea la respuesta del LLM extrayendo el JSON.
        
        Args:
            llm_response: Respuesta cruda del LLM
            
        Returns:
            Dict con la respuesta parseada
            
        Raises:
            json.JSONDecodeError: Si no se puede parsear
        """
        response = llm_response.strip()
        
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            raise
    
    def _execute_action(self, action: Action) -> ActionResult:
        """
        Ejecuta una acción usando las tools disponibles.
        
        Args:
            action: Acción a ejecutar
            
        Returns:
            Resultado de la acción
        """
        tool_name = action.action
        
        if tool_name not in self.tools:
            logger.error(f"Unknown tool: {tool_name}")
            return ActionResult(
                success=False,
                output=None,
                error=f"Unknown tool: {tool_name}. Available tools: {list(self.tools.keys())}"
            )
        
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**action.parameters)
            
            if isinstance(result, dict) and "success" in result:
                if result["success"]:
                    return ActionResult(success=True, output=result)
                else:
                    return ActionResult(
                        success=False,
                        output=None,
                        error=result.get("error", "Unknown error")
                    )
            else:
                return ActionResult(success=True, output=result)
                
        except TypeError as e:
            logger.error(f"Invalid parameters for {tool_name}: {e}")
            return ActionResult(
                success=False,
                output=None,
                error=f"Invalid parameters for {tool_name}: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return ActionResult(
                success=False,
                output=None,
                error=f"Error executing {tool_name}: {str(e)}"
            )
    
    def _tool_read_file(self, path: str) -> Dict:
        """Wrapper para read_file tool."""
        return self.file_tool.read_file(path)
    
    def _tool_write_file(self, path: str, content: str) -> Dict:
        """Wrapper para write_file tool."""
        return self.file_tool.write_file(path, content)
    
    def _tool_edit_file(self, path: str, line_start: int, line_end: int, new_content: str) -> Dict:
        """Wrapper para edit_file tool."""
        return self.file_tool.edit_file(path, line_start, line_end, new_content)
    
    def _tool_list_files(self, directory: str = ".", pattern: str = "*") -> Dict:
        """Wrapper para list_files tool."""
        return self.file_tool.list_files(directory, pattern)
    
    def _tool_create_directory(self, path: str) -> Dict:
        """Wrapper para create_directory tool."""
        return self.file_tool.create_directory(path)
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del orquestador.
        
        Returns:
            Dict con estadísticas
        """
        return {
            "total_actions": len(self.conversation_history),
            "memory_stats": self.memory.get_file_stats(),
            "current_task": self.memory.memory.get("current_task"),
            "recent_files": self.memory.get_recent_files()
        }
    
    def clear_history(self) -> None:
        """Limpia el historial de conversación."""
        self.conversation_history = []
        self.memory.clear_recent_changes()
        logger.info("Conversation history cleared")
