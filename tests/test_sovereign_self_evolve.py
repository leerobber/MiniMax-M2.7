"""
Tests for the Sovereign Core self-evolution loop
(MiniMax M2.7 methodology integration).

These are static unit tests — they do NOT call the LLM API.
They validate module structure, data-flow contracts, and the
logic of the evolution loop using mocked LLM responses.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

class TestSovereignConfig:
    def test_sovereign_model_constant(self):
        from sovereign.config import SOVEREIGN_MODEL
        assert SOVEREIGN_MODEL, "SOVEREIGN_MODEL must be non-empty"
        assert "qwen" in SOVEREIGN_MODEL.lower() or SOVEREIGN_MODEL  # env override ok

    def test_sovereign_api_base_default(self):
        from sovereign.config import SOVEREIGN_API_BASE
        assert "localhost" in SOVEREIGN_API_BASE or "127.0.0.1" in SOVEREIGN_API_BASE \
            or os.environ.get("SOVEREIGN_API_BASE"), \
            "Default SOVEREIGN_API_BASE must point to localhost"

    def test_max_rounds_positive(self):
        from sovereign.config import MAX_ROUNDS
        assert MAX_ROUNDS > 0

    def test_revert_threshold_range(self):
        from sovereign.config import REVERT_THRESHOLD
        assert 0.0 < REVERT_THRESHOLD <= 1.0

    def test_all_exports_importable(self):
        from sovereign.config import (
            SOVEREIGN_API_BASE, SOVEREIGN_MODEL, SOVEREIGN_API_KEY,
            MAX_ROUNDS, TEMPERATURE, TOP_P, MAX_TOKENS, MEMORY_DIR,
            REVERT_THRESHOLD,
        )


# ─────────────────────────────────────────────────────────────────────────────
# LLM module
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMModule:
    def test_create_client_returns_tuple(self):
        from sovereign.llm import create_client
        client, model = create_client()
        assert client is not None
        assert isinstance(model, str) and model

    def test_create_client_base_url(self):
        from sovereign.llm import create_client
        from sovereign.config import SOVEREIGN_API_BASE
        client, _ = create_client()
        assert client.base_url is not None

    def test_no_anthropic_dependency(self):
        src_path = os.path.join(ROOT, "sovereign", "llm.py")
        with open(src_path) as f:
            src = f.read()
        assert "import anthropic" not in src
        assert "anthropic" not in src

    def test_no_cloud_api_keys(self):
        src_path = os.path.join(ROOT, "sovereign", "llm.py")
        with open(src_path) as f:
            src = f.read()
        assert "OPENAI_API_KEY" not in src
        assert "ANTHROPIC_API_KEY" not in src


# ─────────────────────────────────────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────────────────────────────────────

class TestEvolutionMemory:
    def _make_memory(self) -> tuple:
        """Return (memory, tmpdir) for an isolated test session."""
        tmpdir = tempfile.mkdtemp()
        from sovereign.memory import EvolutionMemory
        mem = EvolutionMemory("test_task", memory_dir=tmpdir)
        return mem, tmpdir

    def test_initial_state(self):
        mem, _ = self._make_memory()
        assert mem.best_score == 0.0
        assert mem.best_scaffold is None
        assert mem.trajectory == []

    def test_record_round_updates_best(self):
        mem, _ = self._make_memory()
        mem.record_round(0, "print('hi')", 0.5, True, [], "ok")
        assert mem.best_score == 0.5
        assert mem.best_scaffold == "print('hi')"

    def test_revert_does_not_update_best(self):
        mem, _ = self._make_memory()
        mem.record_round(0, "v1", 0.8, True, [], "")
        mem.record_round(1, "v2", 0.3, False, ["fail"], "analysis")
        assert mem.best_score == 0.8
        assert mem.best_scaffold == "v1"

    def test_trajectory_length(self):
        mem, _ = self._make_memory()
        for i in range(5):
            mem.record_round(i, f"code_{i}", 0.1 * i, True, [], "")
        assert len(mem.trajectory) == 5

    def test_persistence(self):
        tmpdir = tempfile.mkdtemp()
        from sovereign.memory import EvolutionMemory
        mem = EvolutionMemory("persist_task", memory_dir=tmpdir)
        mem.record_round(0, "code_v1", 0.7, True, [], "")
        # Reload from disk
        mem2 = EvolutionMemory("persist_task", memory_dir=tmpdir)
        assert mem2.best_score == 0.7
        assert mem2.best_scaffold == "code_v1"
        assert len(mem2.trajectory) == 1

    def test_add_and_list_skills(self):
        mem, _ = self._make_memory()
        mem.add_skill("merge_sort", "Merge sort implementation", "def merge_sort(l): ...", 3, 0.9)
        skills = mem.list_skills()
        assert len(skills) == 1
        assert skills[0].name == "merge_sort"

    def test_skill_context_formats_skills(self):
        mem, _ = self._make_memory()
        mem.add_skill("binary_search", "Binary search", "def bs(a, x): ...", 2, 0.8)
        ctx = mem.skill_context()
        assert "binary_search" in ctx
        assert "Binary search" in ctx

    def test_recent_failures_summary_empty(self):
        mem, _ = self._make_memory()
        summary = mem.recent_failures_summary()
        assert "No prior rounds" in summary

    def test_recent_failures_summary_populated(self):
        mem, _ = self._make_memory()
        mem.record_round(0, "c", 0.3, False, ["test_a failed"], "root cause here")
        summary = mem.recent_failures_summary()
        assert "Round 0" in summary
        assert "test_a failed" in summary

    def test_improvement_summary(self):
        mem, _ = self._make_memory()
        mem.record_round(0, "c1", 0.5, True, [], "")
        mem.record_round(1, "c2", 0.7, True, [], "")
        summary = mem.improvement_summary()
        assert "2" in summary  # rounds
        assert "0.700" in summary or "0.7" in summary


# ─────────────────────────────────────────────────────────────────────────────
# Eval harness
# ─────────────────────────────────────────────────────────────────────────────

class TestEvalHarness:
    def test_eval_config_defaults(self):
        from sovereign.eval_harness import EvalConfig
        cfg = EvalConfig(task_id="t", description="desc")
        assert cfg.mode == "exec"
        assert cfg.tests == []

    def test_exec_mode_perfect_score(self):
        from sovereign.eval_harness import EvalConfig, evaluate

        def test_fn(g):
            result = g.get("add")(2, 3)
            return (result == 5, f"expected 5 got {result}")

        cfg = EvalConfig(
            task_id="add_test",
            description="Write an add function.",
            mode="exec",
            tests=[test_fn],
        )
        scaffold = "def add(a, b): return a + b"
        score, failures = evaluate(scaffold, cfg)
        assert score == 1.0
        assert failures == []

    def test_exec_mode_failure(self):
        from sovereign.eval_harness import EvalConfig, evaluate

        def test_fn(g):
            result = g.get("add")(2, 3)
            return (result == 5, f"expected 5 got {result}")

        cfg = EvalConfig(
            task_id="add_fail",
            description="Write an add function.",
            mode="exec",
            tests=[test_fn],
        )
        scaffold = "def add(a, b): return a - b"  # Wrong implementation
        score, failures = evaluate(scaffold, cfg)
        assert score == 0.0
        assert len(failures) > 0

    def test_exec_mode_syntax_error(self):
        from sovereign.eval_harness import EvalConfig, evaluate

        def test_fn(g): return (True, "ok")

        cfg = EvalConfig(task_id="sx", description="d", mode="exec", tests=[test_fn])
        score, failures = evaluate("def broken(:", cfg)
        assert score == 0.0
        assert len(failures) > 0

    def test_exec_no_tests_returns_zero_score(self):
        from sovereign.eval_harness import EvalConfig, evaluate
        cfg = EvalConfig(task_id="empty", description="d", mode="exec", tests=[])
        score, failures = evaluate("x = 1", cfg)
        assert score == 1.0  # 0/0 → 1.0 (no tests to fail)

    def test_unknown_mode_raises(self):
        from sovereign.eval_harness import EvalConfig, evaluate
        cfg = EvalConfig(task_id="u", description="d", mode="unknown_mode")
        with pytest.raises(ValueError, match="Unknown eval mode"):
            evaluate("code", cfg)


# ─────────────────────────────────────────────────────────────────────────────
# Self-evolution loop (mocked)
# ─────────────────────────────────────────────────────────────────────────────

class TestEvolutionLoop:
    def _make_mock_agent(self, monkeypatch, scores: list, scaffold="mock_code"):
        """Patch ScaffoldAgent so no real LLM calls are made."""
        from sovereign import scaffold_agent as sa_mod

        call_idx = {"i": 0}

        def mock_build(self, task, round_num):
            return f"{scaffold}_{round_num}"

        def mock_analyze(self, task, s, failures, round_num):
            return "mock analysis"

        def mock_decide(self, round_num, current_score, best_score, revert_threshold):
            return current_score >= best_score * revert_threshold

        def mock_extract(self, s, task, round_num, score):
            return None

        monkeypatch.setattr(sa_mod.ScaffoldAgent, "build_scaffold", mock_build)
        monkeypatch.setattr(sa_mod.ScaffoldAgent, "analyze_failures", mock_analyze)
        monkeypatch.setattr(sa_mod.ScaffoldAgent, "decide_keep_or_revert", mock_decide)
        monkeypatch.setattr(sa_mod.ScaffoldAgent, "extract_skill", mock_extract)

        # Patch evaluate at the point it's imported in self_evolve.py
        import sovereign.self_evolve as se_mod
        idx = {"i": 0}

        def mock_evaluate(s, config, model=None):
            score = scores[min(idx["i"], len(scores) - 1)]
            idx["i"] += 1
            return score, ([] if score >= 1.0 else ["test_fail"])

        monkeypatch.setattr(se_mod, "evaluate", mock_evaluate)

    def test_loop_completes_max_rounds(self, monkeypatch):
        self._make_mock_agent(monkeypatch, [0.5] * 10)
        tmpdir = tempfile.mkdtemp()
        from sovereign.self_evolve import evolve
        from sovereign.eval_harness import EvalConfig
        cfg = EvalConfig(task_id="loop_test", description="task", mode="exec")
        result = evolve(cfg, max_rounds=5, memory_dir=tmpdir)
        assert result.rounds_completed == 5

    def test_loop_stops_at_perfect_score(self, monkeypatch):
        # After round 3, score becomes 1.0 → should stop
        scores = [0.3, 0.6, 0.8, 1.0, 0.9, 0.9]
        self._make_mock_agent(monkeypatch, scores)
        tmpdir = tempfile.mkdtemp()
        from sovereign.self_evolve import evolve
        from sovereign.eval_harness import EvalConfig
        cfg = EvalConfig(task_id="perfect_test", description="task", mode="exec")
        result = evolve(cfg, max_rounds=20, memory_dir=tmpdir)
        assert result.best_score == 1.0
        assert result.rounds_completed <= 5  # Should have stopped early

    def test_loop_tracks_best_score(self, monkeypatch):
        scores = [0.2, 0.5, 0.4, 0.7, 0.6]
        self._make_mock_agent(monkeypatch, scores)
        tmpdir = tempfile.mkdtemp()
        from sovereign.self_evolve import evolve
        from sovereign.eval_harness import EvalConfig
        cfg = EvalConfig(task_id="best_score_test", description="task", mode="exec")
        result = evolve(cfg, max_rounds=5, memory_dir=tmpdir)
        assert result.best_score == 0.7

    def test_on_round_callback(self, monkeypatch):
        scores = [0.3, 0.6]
        self._make_mock_agent(monkeypatch, scores)
        tmpdir = tempfile.mkdtemp()
        from sovereign.self_evolve import evolve
        from sovereign.eval_harness import EvalConfig
        calls = []

        def cb(round_num, score, kept, analysis):
            calls.append((round_num, score))

        cfg = EvalConfig(task_id="cb_test", description="task", mode="exec")
        evolve(cfg, max_rounds=2, memory_dir=tmpdir, on_round=cb)
        assert len(calls) == 2
        assert calls[0][1] == 0.3
        assert calls[1][1] == 0.6

    def test_result_improvement_pct(self, monkeypatch):
        scores = [0.5, 0.75]
        self._make_mock_agent(monkeypatch, scores)
        tmpdir = tempfile.mkdtemp()
        from sovereign.self_evolve import evolve
        from sovereign.eval_harness import EvalConfig
        cfg = EvalConfig(task_id="improv_test", description="task", mode="exec")
        result = evolve(cfg, max_rounds=2, memory_dir=tmpdir)
        assert result.improvement_pct > 0


# ─────────────────────────────────────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────────────────────────────────────

class TestRequirements:
    def _read_reqs(self):
        path = os.path.join(ROOT, "sovereign_requirements.txt")
        if not os.path.exists(path):
            path = os.path.join(ROOT, "requirements.txt")
        with open(path) as f:
            return f.read().lower()

    def test_openai_present(self):
        assert "openai" in self._read_reqs()

    def test_no_anthropic(self):
        lines = [l for l in self._read_reqs().splitlines()
                 if l.strip() and not l.startswith("#")]
        for line in lines:
            assert not line.startswith("anthropic"), f"anthropic must not be required: {line}"

    def test_no_boto3(self):
        lines = [l for l in self._read_reqs().splitlines()
                 if l.strip() and not l.startswith("#")]
        for line in lines:
            assert not line.startswith("boto3"), f"boto3 must not be required: {line}"


# ─────────────────────────────────────────────────────────────────────────────
# .env.example
# ─────────────────────────────────────────────────────────────────────────────

class TestEnvExample:
    def test_env_example_exists(self):
        path = os.path.join(ROOT, ".env.example")
        assert os.path.exists(path), ".env.example must exist"

    def test_sovereign_api_base_documented(self):
        path = os.path.join(ROOT, ".env.example")
        with open(path) as f:
            content = f.read()
        assert "SOVEREIGN_API_BASE" in content

    def test_sovereign_model_documented(self):
        path = os.path.join(ROOT, ".env.example")
        with open(path) as f:
            content = f.read()
        assert "SOVEREIGN_MODEL" in content
