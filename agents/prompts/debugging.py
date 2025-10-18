"""
Debugging Prompts - FASE 3
"""

DEBUGGING_SYSTEM_PROMPT = """You are an expert debugger who excels at finding and fixing software bugs.

Your debugging process:
1. Understand the error message and stack trace
2. Identify the root cause
3. Propose a fix
4. Explain why the bug occurred
5. Suggest how to prevent similar bugs

When debugging:
- Read error messages carefully
- Trace the execution flow
- Check assumptions and edge cases
- Look for common patterns (null checks, off-by-one, async issues)
- Consider the broader context
- Propose minimal, targeted fixes
"""

DEBUGGING_USER_TEMPLATE = """Debug the following issue:

Error:
{error_message}

Stack trace:
{stack_trace}

Relevant code:
{relevant_code}

Context:
{context}

Please provide:
1. Root cause analysis
2. Proposed fix (with code)
3. Explanation of why this happened

Format your response as JSON:
{{
  "root_cause": "Explanation of what's wrong",
  "fix": {{
    "file_path": "path/to/file.py",
    "changes": [
      {{
        "line": 42,
        "old": "old code",
        "new": "fixed code"
      }}
    ]
  }},
  "explanation": "Why this happened"
}}
"""


def create_debugging_prompt(
    error_message: str,
    stack_trace: str,
    relevant_code: str,
    context: str
) -> tuple:
    """Crea el prompt para debugging."""
    system_prompt = DEBUGGING_SYSTEM_PROMPT
    user_prompt = DEBUGGING_USER_TEMPLATE.format(
        error_message=error_message,
        stack_trace=stack_trace or "Not available",
        relevant_code=relevant_code,
        context=context
    )
    return system_prompt, user_prompt
