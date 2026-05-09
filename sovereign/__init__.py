"""sovereign/__init__.py"""
from sovereign.self_evolve import evolve, EvolutionResult
from sovereign.eval_harness import EvalConfig, evaluate
from sovereign.memory import EvolutionMemory
from sovereign.config import SOVEREIGN_MODEL, SOVEREIGN_API_BASE

__all__ = [
    "evolve",
    "EvolutionResult",
    "EvalConfig",
    "evaluate",
    "EvolutionMemory",
    "SOVEREIGN_MODEL",
    "SOVEREIGN_API_BASE",
]
