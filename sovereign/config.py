"""
sovereign/config.py

Sovereign Core configuration for MiniMax-M2.7 self-evolution loop.
All values are read from environment variables; defaults target the
local vLLM endpoint serving Qwen2.5-32B-AWQ on TatorTot.
"""
import os

# ── Sovereign Core endpoint ──────────────────────────────────────────────────
SOVEREIGN_API_BASE: str = os.environ.get(
    "SOVEREIGN_API_BASE", "http://localhost:8001/v1"
)
SOVEREIGN_MODEL: str = os.environ.get(
    "SOVEREIGN_MODEL", "qwen2.5-32b-awq"
)
SOVEREIGN_API_KEY: str = os.environ.get(
    "SOVEREIGN_API_KEY", "sovereign"
)

# ── Self-evolution loop defaults ─────────────────────────────────────────────
MAX_ROUNDS: int = int(os.environ.get("SELF_EVOLVE_MAX_ROUNDS", "100"))
TEMPERATURE: float = float(os.environ.get("SELF_EVOLVE_TEMPERATURE", "1.0"))
TOP_P: float = float(os.environ.get("SELF_EVOLVE_TOP_P", "0.95"))
MAX_TOKENS: int = int(os.environ.get("SELF_EVOLVE_MAX_TOKENS", "8192"))

# ── Memory / skill store ─────────────────────────────────────────────────────
MEMORY_DIR: str = os.environ.get("SOVEREIGN_MEMORY_DIR", "./sovereign_memory")

# ── Revert policy ───────────────────────────────────────────────────────────
# If a round's score drops below (best_score * REVERT_THRESHOLD), revert.
REVERT_THRESHOLD: float = float(os.environ.get("REVERT_THRESHOLD", "0.95"))

__all__ = [
    "SOVEREIGN_API_BASE",
    "SOVEREIGN_MODEL",
    "SOVEREIGN_API_KEY",
    "MAX_ROUNDS",
    "TEMPERATURE",
    "TOP_P",
    "MAX_TOKENS",
    "MEMORY_DIR",
    "REVERT_THRESHOLD",
]
