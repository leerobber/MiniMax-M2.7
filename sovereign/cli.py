"""
sovereign/cli.py

Command-line interface for the Sovereign Core self-evolution loop.

Usage
-----
    # Run 50 rounds of LLM-judge mode on a task file
    python -m sovereign.cli --task tasks/sort_task.json --rounds 50

    # Show memory state for a task
    python -m sovereign.cli --task tasks/sort_task.json --status

Task JSON format
----------------
{
  "task_id": "merge_sort",
  "description": "Write a Python function merge_sort(lst) that ...",
  "mode": "llm_judge",        // or "exec"
  "rubric": "...",            // required for llm_judge mode
  "timeout": 30               // optional, for exec mode
}

For "exec" mode, the test functions must be defined in a separate
tests/<task_id>_tests.py file exporting a list named `TESTS`.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from sovereign.config import MAX_ROUNDS, SOVEREIGN_API_BASE, SOVEREIGN_MODEL
from sovereign.eval_harness import EvalConfig, evaluate
from sovereign.memory import EvolutionMemory
from sovereign.self_evolve import evolve


def _load_task_config(task_path: str, rounds: int) -> tuple[EvalConfig, int]:
    with open(task_path) as f:
        data = json.load(f)

    mode = data.get("mode", "llm_judge")
    tests = []

    if mode == "exec":
        import importlib.util
        task_id = data.get("task_id", "unknown")
        test_module_path = f"tests/{task_id}_tests.py"
        try:
            spec = importlib.util.spec_from_file_location("task_tests", test_module_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            tests = getattr(mod, "TESTS", [])
        except FileNotFoundError:
            print(
                f"Warning: test file {test_module_path} not found. "
                "Falling back to llm_judge mode.",
                file=sys.stderr,
            )
            mode = "llm_judge"

    config = EvalConfig(
        task_id=data["task_id"],
        description=data["description"],
        mode=mode,
        tests=tests,
        rubric=data.get("rubric", ""),
        timeout=data.get("timeout", 30),
    )
    return config, rounds or data.get("rounds", MAX_ROUNDS)


def _status(task_id: str) -> None:
    mem = EvolutionMemory(task_id)
    print(f"Task: {task_id}")
    print(mem.improvement_summary())
    print(f"\nSkills in library: {len(mem.list_skills())}")
    for skill in mem.list_skills():
        print(f"  • {skill.name}: {skill.description}")
    print(f"\nRounds logged: {len(mem.trajectory)}")


def _on_round(round_num: int, score: float, kept: bool, analysis: str) -> None:
    kept_str = "✓" if kept else "✗"
    print(f"  Round {round_num + 1:>4} | score={score:.4f} | {kept_str}")
    if analysis and not kept:
        short = analysis[:120].replace("\n", " ")
        print(f"           ↳ {short}…")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Sovereign Core self-evolution loop (MiniMax M2.7 methodology)"
    )
    parser.add_argument("--task", required=False, help="Path to task JSON file")
    parser.add_argument("--rounds", type=int, default=0,
                        help="Max evolution rounds (overrides task file)")
    parser.add_argument("--status", action="store_true",
                        help="Show memory status for task and exit")
    parser.add_argument("--task-id", default="",
                        help="Task ID for --status without a task file")
    parser.add_argument("--model", default="",
                        help=f"Model override (default: {SOVEREIGN_MODEL})")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    print(f"Sovereign Core Self-Evolution Loop")
    print(f"  endpoint : {SOVEREIGN_API_BASE}")
    print(f"  model    : {args.model or SOVEREIGN_MODEL}")
    print()

    # Status mode
    if args.status:
        task_id = args.task_id
        if not task_id and args.task:
            with open(args.task) as f:
                task_id = json.load(f).get("task_id", "unknown")
        if not task_id:
            print("Error: --task or --task-id required for --status", file=sys.stderr)
            sys.exit(1)
        _status(task_id)
        return

    if not args.task:
        parser.error("--task is required")

    config, max_rounds = _load_task_config(args.task, args.rounds)

    print(f"Task   : {config.task_id}")
    print(f"Mode   : {config.mode}")
    print(f"Rounds : {max_rounds}")
    print()

    result = evolve(
        config=config,
        max_rounds=max_rounds,
        model=args.model or None,
        on_round=_on_round,
    )

    print()
    print("═" * 50)
    print(f"Evolution complete: {result.summary}")
    print(f"Best score : {result.best_score:.4f}")
    print(f"Rounds     : {result.rounds_completed}")
    print(f"Improvement: {result.improvement_pct:+.1f}%")


if __name__ == "__main__":
    main()
