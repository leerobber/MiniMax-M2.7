"""
sovereign/scaffold_agent.py

The scaffold agent builds, analyzes, and refines code solutions using
the Sovereign Core LLM endpoint.

Mirrors the M2.7 self-evolution pattern:
  "build dozens of complex skills for RL experiments, and improve its own
   learning process based on experiment results"

The agent has three primary capabilities:
  1. build_scaffold  — generate an initial or revised solution from the task
                        description + failure context + skill library
  2. analyze_failures — analyze why the current scaffold failed and suggest
                        specific code changes
  3. extract_skill   — extract a reusable skill from a successful scaffold
"""
from __future__ import annotations

from typing import List, Optional

from sovereign.llm import complete_text, create_client
from sovereign.memory import EvolutionMemory

# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a self-improving AI engineer operating within the
Sovereign Core self-evolution loop. Your goal is to iteratively build and
refine code scaffolds that solve a given task, using feedback from previous
evaluation rounds and an evolving skill library.

When building scaffolds:
- Write clean, runnable Python code
- Use the provided skill library when relevant
- Address the specific failures from previous rounds

When analyzing failures:
- Be precise about root causes
- Suggest concrete code changes
- Identify patterns across failure trajectories

When extracting skills:
- Extract small, reusable code fragments
- Give each skill a clear, descriptive name
- Include a one-line description

Always respond in valid JSON as specified by the instruction."""


# ── Agent class ───────────────────────────────────────────────────────────────

class ScaffoldAgent:
    """
    Builds and refines code scaffolds for the self-evolution loop.

    Args:
        memory: The EvolutionMemory instance for the current task.
        model: Optional model override (uses SOVEREIGN_MODEL by default).
    """

    def __init__(self, memory: EvolutionMemory, model: Optional[str] = None) -> None:
        self.memory = memory
        self.client, self.model = create_client(model)

    def build_scaffold(self, task_description: str, round_num: int) -> str:
        """
        Generate or refine a scaffold for the given task.

        On round 0, generates fresh code. On subsequent rounds, uses
        failure analysis + skill library to improve.
        """
        failure_context = self.memory.recent_failures_summary(last_n=5)
        skill_context = self.memory.skill_context()
        best_scaffold = self.memory.best_scaffold

        if round_num == 0:
            instruction = (
                "Write an initial code scaffold that solves the following task.\n"
                "Return ONLY the Python code, no explanation."
            )
            prior_context = ""
        else:
            instruction = (
                f"Round {round_num}: Improve the scaffold based on failure analysis.\n"
                "Apply targeted fixes. Return ONLY the improved Python code."
            )
            prior_context = (
                f"\n\n## Best scaffold so far (score={self.memory.best_score:.3f}):\n"
                f"```python\n{best_scaffold or 'N/A'}\n```"
                f"\n\n## Recent failure trajectories:\n{failure_context}"
                f"\n\n## Skill library:\n{skill_context}"
            )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{instruction}\n\n"
                    f"## Task:\n{task_description}"
                    f"{prior_context}"
                ),
            },
        ]
        return complete_text(self.client, self.model, messages)

    def analyze_failures(
        self,
        task_description: str,
        scaffold: str,
        failures: List[str],
        round_num: int,
    ) -> str:
        """
        Analyze why the current scaffold failed.

        Returns a natural-language analysis of root causes and recommended fixes.
        """
        recent = self.memory.recent_failures_summary(last_n=3)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analyze why round {round_num} failed and recommend fixes.\n\n"
                    f"## Task:\n{task_description}\n\n"
                    f"## Scaffold:\n```python\n{scaffold}\n```\n\n"
                    f"## Failures:\n" + "\n".join(f"- {f}" for f in failures) + "\n\n"
                    f"## Recent trajectory:\n{recent}\n\n"
                    "Respond with a concise root-cause analysis (2–4 sentences) "
                    "and bullet-point recommended changes."
                ),
            },
        ]
        return complete_text(self.client, self.model, messages)

    def decide_keep_or_revert(
        self,
        round_num: int,
        current_score: float,
        best_score: float,
        revert_threshold: float,
    ) -> bool:
        """
        Heuristic keep/revert decision, consistent with M2.7's reported policy.

        Keeps the scaffold if score >= best_score * revert_threshold.
        Optionally queries the LLM for close-call decisions (within 2%).
        """
        if current_score >= best_score:
            return True
        if current_score < best_score * revert_threshold:
            return False
        # Close call: ask the LLM
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Round {round_num}: current score={current_score:.4f}, "
                    f"best score={best_score:.4f}.\n"
                    "Should we keep this round or revert to the best scaffold?\n"
                    "Reply with exactly one word: KEEP or REVERT."
                ),
            },
        ]
        answer = complete_text(self.client, self.model, messages).strip().upper()
        return "KEEP" in answer

    def extract_skill(
        self,
        scaffold: str,
        task_description: str,
        round_num: int,
        score: float,
    ) -> Optional[tuple[str, str, str]]:
        """
        Extract a reusable skill from a successful scaffold.

        Returns (name, description, code) or None if no skill is identified.
        """
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"From the scaffold below (round {round_num}, score={score:.3f}), "
                    "extract ONE reusable skill.\n\n"
                    f"## Task:\n{task_description}\n\n"
                    f"## Scaffold:\n```python\n{scaffold}\n```\n\n"
                    'Respond in JSON: {"name": "...", "description": "...", "code": "..."}\n'
                    "If there is no reusable skill, respond: null"
                ),
            },
        ]
        raw = complete_text(self.client, self.model, messages).strip()
        if raw.lower() in ("null", "none", ""):
            return None
        # Parse JSON
        import json, re
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
        try:
            data = json.loads(clean)
            if data and isinstance(data, dict):
                return data.get("name"), data.get("description"), data.get("code")
        except json.JSONDecodeError:
            pass
        return None
