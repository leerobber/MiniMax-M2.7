# Project Handoff — Aethyro / MiniMax-M2.7 Sovereign Stack
# For Claude CLI and new sessions

Session origin: https://claude.ai/code/session_0163sRLcjECJkSUJSrtfFGSN
Last updated: 2026-07-27

---

## What This Project Is

Two companion repos building toward a **self-evolving, air-gapped sovereign AI
stack** that runs entirely on local GPU (tatortot, RTX 5050, 8 GB VRAM, WSL2):

| Repo | Language | Role |
|------|----------|------|
| `leerobber/MiniMax-M2.7` | Python | Self-evolution loop testbed (sovereign package) |
| `leerobber/aethyro-ntg`  | Rust    | Core NTG engine: genomic pipeline + ternary neural kernel + KAIROS agents |

Supporting:
- **tatortot** — local GPU machine (Windows + WSL2, RTX 5050 8 GB, AMD Ryzen 7, 16 threads)
  serving Qwen2.5-32B-AWQ via vLLM on `http://localhost:8001/v1`
- **HF account** `tastytator` — sovereign LoRA models (avery, forge, oracle, codex, sentinel, nexus),
  datasets (sovereign-economy, aethyro-training), Space (tatortot)

---

## Project Lineage

```
aetherflux-zero (leerobber/aetherflux-zero)
  └─ LM arch research (BPE tokenizer, depth experiments)
  └─ Established "measure don't assume" discipline used everywhere below

Firmament (abandoned)
  └─ Legal-vertical-first approach — wrong order, reset to engine-first

aethyro-ntg  ←── active Rust research kernel
  └─ Genomic pipeline (VCF, LD, bitsliced storage)
  └─ NTG engine (ternary weights + self-modifying topology + audit ledger)
  └─ KAIROS agent lifecycle (Zygote → Adult)
  └─ SovereignBrain (working set, LTM motifs, LanguageOrgan, fitness)
  └─ NanoKeymaster (sovereign routing agent — the API key IS the agent)
  └─ Ternary Memory Graph / HyperVector (8192-dim, Phase 6.11)
  └─ Safety Governance Engine (multi-factor gating, Phase 6.12)
  └─ Domain Coordination (multi-agent, Phase 6.13)
  └─ Quad-Brain Architecture (Phases 6.14–6.18) — COMPLETE
  └─ VITASCALE Hostframe (planned — ADR 0010, 68 KB spec)

MiniMax-M2.7  ←── active Python self-evolution testbed
  └─ sovereign/ package: ScaffoldAgent, EvolutionMemory, EvalHarness
  └─ Runs against Qwen2.5-32B-AWQ on tatortot (port 8001)
  └─ Models MiniMax M2.7's internal self-evolution methodology locally

GH05T3 / Avery  ←── live product at aethyro.com
  └─ 4 tiers: Personal $29/mo, Dev $299/mo, Research $199/mo, CPA $499/mo
```

---

## Key Architecture Concepts

### NTG Engine (aethyro-ntg)
**Neural Ternary Graph** — unique combination (no prior art as of 2026-07-07):
- Ternary weights (BitNet b1.58 absmean quantization)
- Bounded self-evolving graph topology (5 safety rails, off by default)
- Tamper-evident deterministic-replay SHA-256 audit ledger
- Purpose-built for air-gapped edge deployment

### KAIROS
The AI agent being raised within aethyro-ntg. Staged lifecycle:
`Zygote → Neonate → Infant → Toddler → Child → Adolescent → Young Adult → Adult`
Self-modification locked until Adulthood + explicit opt-in.
Named after Greek καιρός ("the critical moment").

### NanoKeymaster
The agent IS the API key. Sovereign routing agent (kernel_host binary):
- Routes calls via ternary policy brain (local / local-fallback / external)
- Logs every routing decision to tamper-evident ledger
- External backend: HTTP POST via ureq (KEYMASTER_BACKEND_URL env var)
- Memory accumulates routing statistics across a session

### SovereignBrain (ADR 0009)
Multi-organ cognitive substrate in aethyro-ntg:
1. Working Set (bounded active addresses)
2. LTM Motifs (long-term memory, consolidated + activated)
3. LanguageOrgan (SIS/docparse graph + calib)
4. Multi-axis fitness (task, structural cost, biological consistency, safety)

### Ternary Memory Graph (Phase 6.11)
8192-dimensional ternary hypervector extension on GraphNode:
- HDC operations: bind (XOR), bundle (majority vote), similarity (Hamming)
- 16× memory compression vs float32
- Bit-sliced encoding (pos/neg u64 slices, 128 words each)

### Safety Governance Engine (Phase 6.12)
Multi-factor mutation gating:
- SafetyScore: constraint (0.4) + alignment (0.3) + confidence (0.3)
- Behavioral drift detection: 10-cycle rolling window, 40% threshold
- Rollback checkpoint: triggers at 2× max_mutations consecutive rejections
- Full audit trail with cycle timestamp, scores, efficiency deltas

### Quad-Brain Architecture (Phases 6.14–6.18) — COMPLETE
Four specialized cognitive brains working in concert:

| Brain | Role |
|-------|------|
| α (Alpha) | Synchronization & Self-Healing: drift detection, rollback, consensus |
| β (Beta)  | Learning & Intelligent Routing: pattern learning, strategy optimization, load prediction |
| γ (Gamma) | Meta-Governance & Evolution: policy synthesis, mutation evolution plans |
| δ (Delta) | Perception & Forecasting: hormone levels, regime detection, 16-dim embeddings |

**Quad-Brain Execution Cycle:**
```
δ (perceive) → α (sync with δ forecast + γ policy) → β (learn with δ regime + γ strategy) → γ (govern) → loop
```

**Scale:** Supports 10,000–500,000 agent hierarchies (4-tier: Super/Sub/Micro/Nano).
**Tests:** 585 total (493 existing + 92 new across Phases 6.14–6.18), all green.

### Sovereign Self-Evolution Loop (MiniMax-M2.7)
100-round loop: `ScaffoldAgent` generates code → `EvalHarness` scores it →
keep if score ≥ 95% of best, else revert → `EvolutionMemory` accumulates skills.
All runs against Qwen2.5-32B-AWQ via OpenAI-compatible API.

---

## Active Branch

Both repos: `claude/session-0163srlcjeckjksujsrtfgfsn-y9hf3y`

```bash
# MiniMax-M2.7
git clone https://github.com/leerobber/MiniMax-M2.7.git
cd MiniMax-M2.7
git checkout claude/session-0163srlcjeckjksujsrtfgfsn-y9hf3y

# aethyro-ntg (for full tests) — Quad-Brain on main
git clone https://github.com/leerobber/aethyro-ntg.git
cd aethyro-ntg
# tests run from kernel/ subdirectory
```

---

## Run the Full Test Suite

```bash
# One command — runs everything
cd MiniMax-M2.7
./scripts/run_full_test.sh

# What it covers:
#   Section 1: 36 Python sovereign tests (pytest, offline, ~2s)
#   Section 2: CPU vs GPU micro-benchmarks (matmul, BMM, GELU, memcpy)
#   Section 3: Rust cargo tests in aethyro-ntg/kernel/ (~1-2 min)
#   Section 4: CI smoke binaries (phase4_calib roundtrip, density_bench)
#   Section 5: cargo clippy -D warnings
# Results saved to: full_test_results.txt

# Skip benchmarks for a faster run:
./scripts/run_full_test.sh --skip-bench

# CPU/GPU benchmark only:
python3 scripts/bench_cpu_gpu.py --reps 20 --warmup 5

# Python tests only:
python3 -m pytest tests/test_sovereign_self_evolve.py -v

# Rust tests only (585 tests as of Phase 6.18):
cd ../aethyro-ntg/kernel && cargo test --release
```

---

## Prerequisites on tatortot (WSL2 Ubuntu)

```bash
# Python deps
python3 -m pip install openai backoff pytest pytest-asyncio numpy
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cu121

# Rust (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Start vLLM for live self-evolution runs (not needed for unit tests):
pip install vllm
vllm serve qwen2.5-32b-awq --port 8001 --dtype auto
```

---

## GPU Info (tatortot)
- GPU: NVIDIA GeForce RTX 5050 Laptop GPU (Blackwell)
- VRAM: 8151 MiB
- Driver: 610.47 (KMD), CUDA UMD 13.3
- WSL2 kernel: 6.6.87.2-microsoft-standard-WSL2
- CPU: AMD Ryzen 7 250 w/ Radeon 780M, 8 cores / 16 threads
- RAM: ~7.6 GB available to WSL

---

## Phase Status (aethyro-ntg)
| Phase | Status | What |
|-------|--------|------|
| 0 | COMPLETE | Foundation, ADRs, repo structure |
| 1 | COMPLETE | Genomic pipeline (VCF, bitsliced, LD) |
| 2 | COMPLETE | NTG ternary kernel + SIMD matmul |
| 3 | COMPLETE | Self-modification safety rails + audit ledger |
| 4 | COMPLETE | Calibration (phase4_calib binary, model roundtrip) |
| 5 | COMPLETE | Storage integration |
| 6.0 | COMPLETE | Ternary GEMM vs f32 head-to-head benchmark (143.6× speedup) |
| 6.1 | COMPLETE | NanoKeymaster routing agent |
| 6.2 | COMPLETE | External HTTP backend (ureq POST) |
| 6.11 | COMPLETE | Ternary Memory Graph / HyperVector (8192-dim HDC) |
| 6.12 | COMPLETE | Autonomous Safety & Governance Engine |
| 6.13 | COMPLETE | Domain Coordination (multi-agent) |
| 6.14 | COMPLETE | Brain α — Synchronization & Self-Healing |
| 6.15 | COMPLETE | Brain β — Learning & Intelligent Routing |
| 6.16 | COMPLETE | Twin-Brain + Quad-Brain Integration |
| 6.17 | COMPLETE | Brain γ — Meta-Governance & Evolution |
| 6.18 | COMPLETE | Brain δ — Perception & Forecasting |
| **F** | **PROPOSED** | Self-awareness instrumentation, self-healing, robotics |

**Test count (aethyro-ntg/kernel):** 585 tests, all passing.

---

## Open PRs (as of 2026-07-27)

### aethyro-ntg
None — all merged to `main`.

### MiniMax-M2.7
- `#3` — feat: CPU/GPU benchmark scripts (draft, our PR — ready to merge)
- `#2` — ECC Tools bot PR (auto-generated; adds Claude/Codex agent config files;
  low-risk content but changes how future agent sessions behave — maintainer decision needed)

---

## Known Issues / Follow-ups

- **Orphaned test**: `aethyro-ntg/tests/test_genomic_operator.rs` uses wrong crate
  name `ntg` (should be `ntg_kernel`); not wired to Cargo.toml, never runs via `cargo test`.
- **Clippy debt**: ~155 remaining warnings in `genomic/` modules (added by 67 commits
  between PR #3 and PR #4); pre-existing, out of scope for fixes so far.
- **MiniMax-M2.7 CI**: No `.github/workflows/ci.yml` yet.
- **VITASCALE Hostframe** (ADR 0010): Production hosting architecture for KAIROS — not yet implemented.
- **Phase F**: Self-awareness instrumentation, self-healing, robotics — proposed, not started.

---

## Next Steps (suggested)
1. Run `./scripts/run_full_test.sh` on tatortot — paste results (GPU benchmark + 585 Rust tests)
2. Decide on MiniMax-M2.7 PR #2 (ecc-tools bot — merge or close?)
3. Merge MiniMax-M2.7 PR #3 (CPU/GPU benchmarks — ready)
4. Add CI workflow to MiniMax-M2.7 (`.github/workflows/ci.yml`)
5. Fix orphaned `tests/test_genomic_operator.rs` in aethyro-ntg
6. Begin **Phase F**: self-awareness instrumentation
7. Wire the real aethyro.com production comparison for Phase 6 (requires live API access)
