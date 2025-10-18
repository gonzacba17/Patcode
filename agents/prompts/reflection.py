"""
Reflection Prompts - FASE 3
"""

REFLECTION_SYSTEM_PROMPT = """You are an expert code reviewer who evaluates whether tasks have been completed successfully.

Your role:
1. Review what was done
2. Check if requirements were met
3. Identify any issues or gaps
4. Suggest improvements or next steps
5. Determine if the task is complete or needs more work

When reviewing:
- Compare results against original requirements
- Check for completeness and correctness
- Consider edge cases and error handling
- Look for potential improvements
- Be objective and thorough
"""

REFLECTION_USER_TEMPLATE = """Review the following task execution:

Original task: {task_description}

Steps completed:
{steps_completed}

Results:
{results}

Files modified:
{files_modified}

Tests run:
{test_results}

Please provide:
1. Is the task complete? (yes/no)
2. What was accomplished successfully?
3. What issues or gaps remain?
4. Suggested next steps

Format your response as JSON:
{{
  "task_complete": true/false,
  "accomplishments": ["Achievement 1", "Achievement 2"],
  "issues": ["Issue 1", "Issue 2"],
  "next_steps": ["Step 1", "Step 2"],
  "quality_score": 0-10,
  "reasoning": "Explanation of assessment"
}}
"""


def create_reflection_prompt(
    task_description: str,
    steps_completed: str,
    results: str,
    files_modified: list,
    test_results: str
) -> tuple:
    """Crea el prompt para reflection."""
    system_prompt = REFLECTION_SYSTEM_PROMPT
    user_prompt = REFLECTION_USER_TEMPLATE.format(
        task_description=task_description,
        steps_completed=steps_completed,
        results=results,
        files_modified="\n".join(files_modified) if files_modified else "None",
        test_results=test_results or "No tests run"
    )
    return system_prompt, user_prompt
