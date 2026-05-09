"""
sovereign/eval_harness.py

Evaluation harness for the self-evolution loop.

Runs a scaffold against a task's test suite and returns a normalized
score [0.0, 1.0] plus a list of failures.

Two evaluation modes:
  - "exec"     : execute the scaffold as Python code in a sandbox subprocess
                 and run provided test functions against it
  - "llm_judge": ask the LLM to judge the scaffold's quality (for tasks
                 without executable test suites)

The choice of mode is set per-task in the EvalConfig.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from sovereign.llm import complete_text, create_client


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class EvalConfig:
    """
    Configuration for a single evaluation task.

    Args:
        task_id:      Unique identifier used for memory/logging.
        description:  Natural-language task description (fed to the agent).
        mode:         "exec" or "llm_judge".
        tests:        For "exec" mode: list of test functions
                      (each receives the exec'd module globals).
        rubric:       For "llm_judge" mode: evaluation rubric.
        timeout:      Subprocess timeout in seconds (exec mode).
    """
    task_id: str
    description: str
    mode: str = "exec"
    tests: List[Callable[[Dict[str, Any]], Tuple[bool, str]]] = field(
        default_factory=list
    )
    rubric: str = ""
    timeout: int = 30


# ── Exec harness ──────────────────────────────────────────────────────────────

def _run_scaffold_exec(
    scaffold: str,
    tests: List[Callable],
    timeout: int = 30,
) -> Tuple[float, List[str]]:
    """
    Execute the scaffold in a subprocess, then run each test against
    the resulting namespace.

    Returns (score, failures) where score = passed / total.
    """
    failures: List[str] = []
    passed = 0

    # Write scaffold to a temp file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(scaffold)
        tmp_path = tmp.name

    # Execute it in a subprocess to get globals
    try:
        exec_result = subprocess.run(
            [sys.executable, "-c",
             f"import runpy; g = runpy.run_path(r'{tmp_path}'); "
             "import json, sys; "
             "print(json.dumps({k: repr(v) for k, v in g.items() if not k.startswith('_')}))"],
            capture_output=True, text=True, timeout=timeout,
        )
        if exec_result.returncode != 0:
            failures.append(f"ExecutionError: {exec_result.stderr[:300]}")
            return 0.0, failures
    except subprocess.TimeoutExpired:
        failures.append("TimeoutError: scaffold took too long to execute")
        return 0.0, failures
    finally:
        import os
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    # Run each test
    exec_globals: Dict[str, Any] = {}
    try:
        # Safe re-execute in-process for test inspection
        exec(compile(scaffold, "<scaffold>", "exec"), exec_globals)
    except Exception as exc:
        failures.append(f"ExecException: {exc}")
        return 0.0, failures

    if not tests:
        return 1.0, []

    for test_fn in tests:
        try:
            ok, msg = test_fn(exec_globals)
            if ok:
                passed += 1
            else:
                failures.append(msg)
        except Exception as exc:
            failures.append(f"{test_fn.__name__}: {exc}")

    score = passed / len(tests)
    return score, failures


# ── LLM judge ────────────────────────────────────────────────────────────────

def _run_scaffold_llm_judge(
    scaffold: str,
    task_description: str,
    rubric: str,
    model: Optional[str] = None,
) -> Tuple[float, List[str]]:
    """
    Ask the Sovereign Core LLM to judge scaffold quality.

    Returns (score, failures) where score ∈ [0.0, 1.0].
    """
    client, resolved_model = create_client(model)
    prompt = (
        "You are an impartial code judge. Evaluate the following scaffold "
        "against the task description and rubric.\n\n"
        f"## Task:\n{task_description}\n\n"
        f"## Rubric:\n{rubric}\n\n"
        f"## Scaffold:\n```python\n{scaffold}\n```\n\n"
        "Respond in JSON:\n"
        '{"score": <float 0.0-1.0>, "failures": ["<issue1>", ...]}\n'
        "score=1.0 means perfect. failures is an empty list if score=1.0."
    )
    raw = complete_text(
        client,
        resolved_model,
        [{"role": "user", "content": prompt}],
    )
    import json, re
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    try:
        data = json.loads(clean)
        score = float(data.get("score", 0.0))
        failures = data.get("failures", [])
        return score, failures
    except (json.JSONDecodeError, KeyError, TypeError):
        # Parse failed: treat as zero
        return 0.0, [f"JudgeParseError: {raw[:200]}"]


# ── Public API ────────────────────────────────────────────────────────────────

def evaluate(
    scaffold: str,
    config: EvalConfig,
    model: Optional[str] = None,
) -> Tuple[float, List[str]]:
    """
    Evaluate a scaffold and return (score, failures).

    Args:
        scaffold: The generated/refined code to evaluate.
        config:   Evaluation configuration for the task.
        model:    Optional model override for llm_judge mode.

    Returns:
        Tuple[float, List[str]]: Normalized score and list of failure messages.
    """
    if config.mode == "exec":
        return _run_scaffold_exec(scaffold, config.tests, config.timeout)
    elif config.mode == "llm_judge":
        return _run_scaffold_llm_judge(
            scaffold, config.description, config.rubric, model
        )
    else:
        raise ValueError(f"Unknown eval mode: {config.mode!r}")
