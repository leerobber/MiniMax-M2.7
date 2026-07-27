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
  └─ VITASCALE Hostframe (planned — ADR 0010, 68 KB spec)
  └─ Phases 0–5 COMPLETE, Phase 6 (integration) authorized to begin

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

### SovereignBrain (ADR 0009)
Multi-organ cognitive substrate in aethyro-ntg:
1. Working Set (bounded active addresses)
2. LTM Motifs (long-term memory, consolidated + activated)
3. LanguageOrgan (SIS/docparse graph + calib)
4. Multi-axis fitness (task, structural cost, biological consistency, safety)

### Sovereign Self-Evolution Loop (MiniMax-M2.7)
100-round loop: `ScaffoldAgent` generates code → `EvalHarness` scores it →
keep if score ≥ 95% of best, else revert → `EvolutionMemory` accumulates skills.
All runs against Qwen2.5-32B-AWQ via OpenAI-compatible API.

### TODO — Quad Brain (not yet in either repo)
The "quad brain" concept the founder has in mind has not been committed to
code yet. Likely candidates based on architecture:
- The 4 SovereignBrain organs (working set, LTM, LanguageOrgan, fitness)
- A 4-model ensemble from the sovereign LoRA set (avery, forge, oracle, codex)
- A 4-agent orchestration layer above the self-evolution loop
**Needs clarification and implementation.**

---

## Active Branch

Both repos: `claude/session-0163srlcjeckjksujsrtfgfsn-y9hf3y`

```bash
# MiniMax-M2.7
git clone https://github.com/leerobber/MiniMax-M2.7.git
cd MiniMax-M2.7
git checkout claude/session-0163srlcjeckjksujsrtfgfsn-y9hf3y

# aethyro-ntg (for full tests)
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
#   Section 3: 386 Rust cargo tests in aethyro-ntg/kernel/ (~1-2 min)
#   Section 4: CI smoke binaries (phase4_calib roundtrip, density_bench)
#   Section 5: cargo clippy -D warnings
# Results saved to: full_test_results.txt

# Skip benchmarks for a faster run:
./scripts/run_full_test.sh --skip-bench

# CPU/GPU benchmark only:
python3 scripts/bench_cpu_gpu.py --reps 20 --warmup 5

# Python tests only:
python3 -m pytest tests/test_sovereign_self_evolve.py -v

# Rust tests only:
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
| **6** | **AUTHORIZED** | Integration — host load of frozen models, compare vs aethyro.com |
| F | PROPOSED | Self-awareness instrumentation, self-healing, robotics |

---

## Open PRs
- `leerobber/MiniMax-M2.7#3` — feat: CPU/GPU benchmark scripts (draft)
- `leerobber/MiniMax-M2.7#2` — ECC Tools bot PR (auto-generated, review before merge)

---

## Next Steps (suggested)
1. Run `./scripts/run_full_test.sh` on tatortot — paste results
2. Define and implement **quad brain** concept
3. Begin **Phase 6**: integration of frozen NTG models with aethyro.com/GH05T3
4. Add CI workflow to MiniMax-M2.7 (`.github/workflows/ci.yml`)
5. Fix orphaned `tests/test_genomic_operator.rs` in aethyro-ntg
   (wrong crate name `ntg` → should be `ntg_kernel`, not wired to Cargo.toml)
