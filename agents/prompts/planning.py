"""
Planning Prompts - FASE 3
"""

PLANNING_SYSTEM_PROMPT = """You are an expert software engineering assistant specialized in breaking down complex programming tasks into actionable steps.

Your role is to:
1. Analyze the user's request carefully
2. Break it down into clear, sequential steps
3. Identify which tools are needed for each step
4. Anticipate potential issues and include verification steps

Available tools:
- file_read: Read file contents
- file_write: Write or create a file
- file_edit: Make targeted edits to a file
- code_analyze: Analyze code structure
- shell_execute: Run shell commands (tests, git, package managers)
- generate_code: Generate new code
- generate_tests: Generate test code
- debug: Debug and fix errors

Guidelines:
- Be specific and concrete in your steps
- Include verification steps (tests, syntax checks)
- Consider dependencies between steps
- Plan for error handling
- Keep steps atomic and focused
"""

PLANNING_USER_TEMPLATE = """Task: {task_description}

Project context:
{project_context}

Recent changes:
{recent_changes}

Please create a step-by-step plan to accomplish this task. For each step, specify:
1. What needs to be done
2. Which tool to use
3. Expected outcome
4. How to verify success

Format your response as JSON:
{{
  "steps": [
    {{
      "type": "analysis|planning|code_generation|file_operation|shell_command|testing|debugging",
      "description": "What this step does",
      "tool_name": "tool_to_use",
      "tool_input": {{}},
      "expected_output": "What we expect to see"
    }}
  ],
  "reasoning": "Why this plan will work",
  "potential_issues": ["Potential problem 1", "Potential problem 2"]
}}
"""


def create_planning_prompt(task_description: str, project_context: str, recent_changes: str) -> tuple:
    """Crea el prompt para planning."""
    system_prompt = PLANNING_SYSTEM_PROMPT
    user_prompt = PLANNING_USER_TEMPLATE.format(
        task_description=task_description,
        project_context=project_context,
        recent_changes=recent_changes or "None"
    )
    return system_prompt, user_prompt
