"""
Code Generation Prompts - FASE 3
"""

CODE_GENERATION_SYSTEM_PROMPT = """You are an expert programmer who writes clean, efficient, and well-documented code.

Principles:
- Write production-ready code, not pseudocode
- Include proper error handling
- Add docstrings and comments where helpful
- Follow language-specific best practices
- Consider edge cases
- Make code testable

Languages you excel at:
- Python (PEP 8, type hints, modern idioms)
- JavaScript/TypeScript (ES6+, async/await)
- React (hooks, functional components)

Always:
1. Understand the context fully before coding
2. Write complete, working code
3. Include imports and dependencies
4. Think about testing
5. Consider performance and maintainability
"""

CODE_GENERATION_USER_TEMPLATE = """Generate code for the following:

Task: {task_description}

Context:
{context}

Existing code to reference:
{existing_code}

Requirements:
{requirements}

Please provide:
1. Complete, working code
2. Brief explanation of key design decisions
3. Any assumptions made

Format your response as:
```{language}
# Your code here
```

Explanation:
[Your explanation here]
"""


def create_code_generation_prompt(
    task_description: str,
    context: str,
    existing_code: str,
    requirements: str,
    language: str = "python"
) -> tuple:
    """Crea el prompt para generación de código."""
    system_prompt = CODE_GENERATION_SYSTEM_PROMPT
    user_prompt = CODE_GENERATION_USER_TEMPLATE.format(
        task_description=task_description,
        context=context,
        existing_code=existing_code or "None",
        requirements=requirements,
        language=language
    )
    return system_prompt, user_prompt
