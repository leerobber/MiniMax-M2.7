```markdown
# MiniMax-M2.7 Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill introduces the core development patterns and conventions used in the MiniMax-M2.7 Python repository. You'll learn how to structure files, write and organize code, follow commit message guidelines, and implement and run tests. This guide is ideal for contributors seeking consistency and efficiency in MiniMax-M2.7 development.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example:  
    ```
    mini_max_core.py
    utils_helper.py
    ```

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils_helper import calculate_score
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ["MiniMax", "calculate_score"]
    ```

### Commit Messages
- Follow the **Conventional Commits** format.
- Use the `feat` prefix for new features.
- Keep commit messages concise (average: 67 characters).
  - Example:
    ```
    feat: add minimax algorithm with alpha-beta pruning
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new capability or module  
**Command:** `/add-feature`

1. Create a new Python file using snake_case naming.
2. Implement the feature using relative imports for dependencies.
3. Define named exports in the module.
4. Write or update corresponding test files (see Testing Patterns).
5. Commit changes with a message starting with `feat:` and a concise description.

### Running Tests
**Trigger:** When verifying code correctness  
**Command:** `/run-tests`

1. Locate test files matching the `*.test.*` pattern.
2. Use the project's preferred test runner (framework is unspecified; try `pytest` or `unittest`).
3. Run tests and review output for failures.

### Refactoring Code
**Trigger:** When improving or restructuring existing code  
**Command:** `/refactor-code`

1. Update file and function names to follow snake_case if needed.
2. Adjust imports to use relative paths.
3. Update `__all__` for named exports.
4. Ensure all tests still pass after changes.

## Testing Patterns

- Test files follow the pattern: `*.test.*` (e.g., `minimax.test.py`).
- The testing framework is unspecified; use standard Python testing tools such as `pytest` or `unittest`.
- Place tests alongside or near the modules they cover.
- Example test file:
  ```python
  # minimax.test.py
  from .mini_max_core import MiniMax

  def test_minimax_basic():
      assert MiniMax().run([1, 2, 3]) == expected_result
  ```

## Commands
| Command        | Purpose                                      |
|----------------|----------------------------------------------|
| /add-feature   | Scaffold and implement a new feature/module  |
| /run-tests     | Run all tests in the repository              |
| /refactor-code | Refactor code to follow conventions          |
```
