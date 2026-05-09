"""
sovereign/self_evolve.py

The core self-evolution loop for Sovereign Core + MiniMax-M2.7 methodology.

Reproduces the M2.7 self-evolution approach described in:
  "An internal version of M2.7 autonomously optimized a programming scaffold
   over 100+ rounds — analyzing failure trajectories, modifying code, running
   evaluations, and deciding to keep or revert — achieving a 30% performance
   improvement."

Architecture
------------
Each round:
  1. ScaffoldAgent.build_scaffold() → candidate code
  2. eval_harness.evaluate() → (score, failures)
  3. ScaffoldAgent.decide_keep_or_revert() → bool
  4. ScaffoldAgent.analyze_failures() → analysis string
  5. EvolutionMemory.record_round() → persist
  6. (Optional) ScaffoldAgent.extract_skill() → add to skill library
  7. Check convergence / max_rounds → continue or stop

Usage
-----
    from sovereign.self_evolve import evolve
    from sovereign.eval_harness import EvalConfig

    config = EvalConfig(
        task_id="my_task",
        description="Write a function that sorts a list using merge sort.",
        mode="exec",
        tests=[test_sort_empty, test_sort_integers, test_sort_strings],
    )
    result = evolve(config, max_rounds=50)
    print(f"Best score: {result.best_score:.3f}")
    print(result.best_scaffold)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, List, Optional

from sovereign.config import MAX_ROUNDS, REVERT_THRESHOLD, SOVEREIGN_MODEL
from sovereign.eval_harness import EvalConfig, evaluate
from sovereign.memory import EvolutionMemory
from sovereign.scaffold_agent import ScaffoldAgent

logger = logging.getLogger(__name__)


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class EvolutionResult:
    task_id: str
    best_scaffold: Optional[str]
    best_score: float
    rounds_completed: int
    improvement_pct: float
    summary: str


# ── Evolution loop ────────────────────────────────────────────────────────────

def evolve(
    config: EvalConfig,
    max_rounds: int = MAX_ROUNDS,
    revert_threshold: float = REVERT_THRESHOLD,
    model: Optional[str] = None,
    on_round: Optional[Callable[[int, float, bool, str], None]] = None,
    memory_dir: Optional[str] = None,
    extract_skills_every: int = 10,
) -> EvolutionResult:
    """
    Run the self-evolution loop for a task.

    Args:
        config:                 Evaluation configuration.
        max_rounds:             Maximum number of evolution rounds.
        revert_threshold:       Fraction of best_score below which we revert.
        model:                  Optional model override.
        on_round:               Optional callback(round_num, score, kept, analysis).
        memory_dir:             Override for MEMORY_DIR.
        extract_skills_every:   Extract skills every N successful rounds.

    Returns:
        EvolutionResult with the best scaffold and final stats.
    """
    resolved_model = model or SOVEREIGN_MODEL

    # Set up memory and agent
    kwargs = {}
    if memory_dir:
        kwargs["memory_dir"] = memory_dir
    memory = EvolutionMemory(config.task_id, **kwargs)
    agent = ScaffoldAgent(memory, model=resolved_model)

    initial_score = memory.best_score  # May be > 0 if resuming
    successful_rounds = 0

    logger.info(
        "Starting self-evolution for task=%r | max_rounds=%d | model=%s",
        config.task_id, max_rounds, resolved_model,
    )

    for round_num in range(max_rounds):
        logger.info("── Round %d / %d ──", round_num + 1, max_rounds)

        # 1. Build scaffold
        scaffold = agent.build_scaffold(config.description, round_num)
        logger.debug("Scaffold built (%d chars)", len(scaffold))

        # 2. Evaluate
        score, failures = evaluate(scaffold, config, model=resolved_model)
        logger.info("Score: %.4f | Failures: %d", score, len(failures))

        # 3. Failure analysis (always — feeds next round)
        analysis = ""
        if failures:
            analysis = agent.analyze_failures(
                config.description, scaffold, failures, round_num
            )
            logger.debug("Analysis: %s", analysis[:150])

        # 4. Keep / revert decision
        kept = agent.decide_keep_or_revert(
            round_num=round_num,
            current_score=score,
            best_score=memory.best_score,
            revert_threshold=revert_threshold,
        )
        if kept:
            successful_rounds += 1

        # 5. Record in memory
        memory.record_round(
            round_num=round_num,
            scaffold=scaffold,
            score=score,
            kept=kept,
            failures=failures,
            analysis=analysis,
        )

        # 6. Optional skill extraction on good rounds
        if kept and (successful_rounds % extract_skills_every == 0):
            skill = agent.extract_skill(
                scaffold, config.description, round_num, score
            )
            if skill and all(skill):
                name, description, code = skill
                memory.add_skill(
                    name=name,
                    description=description,
                    code=code,
                    source_round=round_num,
                    score=score,
                )
                logger.info("Skill extracted: %r", name)

        # 7. Callback
        if on_round:
            on_round(round_num, score, kept, analysis)

        # 8. Convergence: perfect score
        if memory.best_score >= 1.0:
            logger.info("Converged at round %d with perfect score.", round_num)
            break

    # Build result
    improvement_pct = (
        (memory.best_score - initial_score) / max(initial_score, 1e-6) * 100
        if initial_score > 0
        else (memory.best_score * 100)
    )
    result = EvolutionResult(
        task_id=config.task_id,
        best_scaffold=memory.best_scaffold,
        best_score=memory.best_score,
        rounds_completed=round_num + 1,
        improvement_pct=improvement_pct,
        summary=memory.improvement_summary(),
    )
    logger.info(
        "Evolution complete. Best score: %.4f after %d rounds (+%.1f%%)",
        result.best_score, result.rounds_completed, improvement_pct,
    )
    return result
