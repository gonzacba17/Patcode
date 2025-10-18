"""
Testing Prompts - FASE 3
"""

TESTING_SYSTEM_PROMPT = """You are an expert in software testing who writes comprehensive, meaningful tests.

Testing principles:
- Test behavior, not implementation
- Cover happy path and edge cases
- Write clear, descriptive test names
- Use appropriate assertions
- Keep tests independent and isolated
- Make tests fast and reliable

Test types you write:
- Unit tests (pytest, jest, vitest)
- Integration tests
- Edge case tests
- Error handling tests

Always:
1. Understand what needs to be tested
2. Identify critical paths and edge cases
3. Write clear, maintainable tests
4. Include setup and teardown when needed
5. Add docstrings explaining what's being tested
"""

TESTING_USER_TEMPLATE = """Generate tests for:

Code to test:
{code_to_test}

Function/Class name: {target_name}

Requirements:
{requirements}

Test framework: {framework}

Please provide complete test file with multiple test cases covering:
1. Happy path
2. Edge cases
3. Error handling

Format your response as:
```{language}
# Your test code here
```

Test coverage explanation:
[Explain what's tested]
"""


def create_testing_prompt(
    code_to_test: str,
    target_name: str,
    requirements: str,
    framework: str = "pytest",
    language: str = "python"
) -> tuple:
    """Crea el prompt para generación de tests."""
    system_prompt = TESTING_SYSTEM_PROMPT
    user_prompt = TESTING_USER_TEMPLATE.format(
        code_to_test=code_to_test,
        target_name=target_name,
        requirements=requirements,
        framework=framework,
        language=language
    )
    return system_prompt, user_prompt
