"""
sovereign/memory.py

Skill and trajectory memory store for the self-evolution loop.

Inspired by MiniMax-M2.7's described self-evolution methodology:
  "we let the model update its own memory, build dozens of complex skills
   for RL experiments, and improve its own learning process based on
   experiment results."

Each evolution session persists:
  - A skill library: named, reusable code fragments extracted by the LLM
  - A trajectory log: round → {scaffold, score, kept, failures, analysis}
  - A best-so-far snapshot: the highest-scoring scaffold seen

Memory is stored as JSON in MEMORY_DIR so it survives process restarts
and can accumulate across multiple sessions.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sovereign.config import MEMORY_DIR


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class Skill:
    name: str
    description: str
    code: str
    source_round: int
    score_at_extraction: float
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RoundRecord:
    round_num: int
    scaffold: str           # The full code/solution for this round
    score: float            # 0.0 – 1.0 normalized eval score
    kept: bool              # True if this round was accepted (not reverted)
    failures: List[str]     # Test names / assertions that failed
    analysis: str           # LLM's failure-trajectory analysis
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Memory store ─────────────────────────────────────────────────────────────

class EvolutionMemory:
    """
    Persistent memory for a single self-evolution task session.

    Args:
        task_id: Unique identifier for the task being evolved.
        memory_dir: Directory for storing JSON state files.
    """

    def __init__(self, task_id: str, memory_dir: str = MEMORY_DIR) -> None:
        self.task_id = task_id
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self.memory_dir / f"{task_id}.json"

        self._skills: Dict[str, Skill] = {}
        self._trajectory: List[RoundRecord] = []
        self._best_scaffold: Optional[str] = None
        self._best_score: float = 0.0

        if self._state_path.exists():
            self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        with open(self._state_path) as f:
            state = json.load(f)
        self._skills = {
            name: Skill(**data) for name, data in state.get("skills", {}).items()
        }
        self._trajectory = [
            RoundRecord(**r) for r in state.get("trajectory", [])
        ]
        self._best_scaffold = state.get("best_scaffold")
        self._best_score = state.get("best_score", 0.0)

    def save(self) -> None:
        state = {
            "task_id": self.task_id,
            "best_score": self._best_score,
            "best_scaffold": self._best_scaffold,
            "skills": {name: asdict(skill) for name, skill in self._skills.items()},
            "trajectory": [asdict(r) for r in self._trajectory],
        }
        with open(self._state_path, "w") as f:
            json.dump(state, f, indent=2)

    # ── Trajectory ───────────────────────────────────────────────────────────

    def record_round(
        self,
        round_num: int,
        scaffold: str,
        score: float,
        kept: bool,
        failures: List[str],
        analysis: str,
    ) -> None:
        record = RoundRecord(
            round_num=round_num,
            scaffold=scaffold,
            score=score,
            kept=kept,
            failures=failures,
            analysis=analysis,
        )
        self._trajectory.append(record)
        if kept and score > self._best_score:
            self._best_score = score
            self._best_scaffold = scaffold
        self.save()

    @property
    def trajectory(self) -> List[RoundRecord]:
        return list(self._trajectory)

    @property
    def best_scaffold(self) -> Optional[str]:
        return self._best_scaffold

    @property
    def best_score(self) -> float:
        return self._best_score

    # ── Skill library ────────────────────────────────────────────────────────

    def add_skill(
        self,
        name: str,
        description: str,
        code: str,
        source_round: int,
        score: float,
    ) -> None:
        self._skills[name] = Skill(
            name=name,
            description=description,
            code=code,
            source_round=source_round,
            score_at_extraction=score,
        )
        self.save()

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    # ── Context helpers ──────────────────────────────────────────────────────

    def recent_failures_summary(self, last_n: int = 5) -> str:
        """Build a concise summary of recent failure trajectories for the LLM."""
        recent = self._trajectory[-last_n:] if self._trajectory else []
        if not recent:
            return "No prior rounds recorded."
        lines = []
        for rec in recent:
            kept_str = "✓ kept" if rec.kept else "✗ reverted"
            lines.append(
                f"Round {rec.round_num} [{kept_str}] score={rec.score:.3f}\n"
                f"  Failures: {', '.join(rec.failures) or 'none'}\n"
                f"  Analysis: {rec.analysis[:200]}"
            )
        return "\n".join(lines)

    def skill_context(self) -> str:
        """Return skill library as formatted context for the LLM."""
        if not self._skills:
            return "No skills extracted yet."
        lines = []
        for skill in self._skills.values():
            lines.append(
                f"### Skill: {skill.name}\n"
                f"# {skill.description}\n"
                f"{skill.code}\n"
            )
        return "\n".join(lines)

    def improvement_summary(self) -> str:
        """Summarize progress across all rounds."""
        if not self._trajectory:
            return "No rounds completed yet."
        scores = [r.score for r in self._trajectory]
        kept = sum(1 for r in self._trajectory if r.kept)
        reverted = len(self._trajectory) - kept
        improvement = (
            (self._best_score - scores[0]) / max(scores[0], 1e-6) * 100
            if scores else 0
        )
        return (
            f"Rounds: {len(self._trajectory)} | Kept: {kept} | Reverted: {reverted}\n"
            f"Score: {scores[0]:.3f} → {self._best_score:.3f} "
            f"({improvement:+.1f}%)"
        )
