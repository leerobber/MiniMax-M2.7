#!/usr/bin/env bash
# =============================================================================
# scripts/run_full_test.sh
# Full end-to-end test suite for the MiniMax-M2.7 + aethyro-ntg project.
#
# Covers:
#   1. MiniMax-M2.7 — 36 sovereign Python/pytest tests
#   2. MiniMax-M2.7 — CPU vs GPU benchmark (scripts/bench_cpu_gpu.py)
#   3. aethyro-ntg  — 386 Rust/cargo tests (cargo test --release in kernel/)
#   4. aethyro-ntg  — CI smoke binaries (phase4_calib, density_bench)
#   5. aethyro-ntg  — cargo clippy (warnings-as-errors)
#
# Usage:
#   ./scripts/run_full_test.sh [OPTIONS]
#
# Options:
#   --skip-bench        Skip CPU/GPU micro-benchmarks
#   --skip-gpu          Run benchmarks in CPU-only mode
#   --skip-clippy       Skip cargo clippy step
#   --skip-smoke        Skip aethyro-ntg CI smoke binaries
#   --ntg-dir DIR       Path to aethyro-ntg clone (auto-cloned if missing)
#   --output FILE       Write full log to FILE (default: full_test_results.txt)
#   --release           Build Rust in release mode (default; disable with --debug)
#   --debug             Build Rust in debug mode (faster compile, slower tests)
# =============================================================================

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
SKIP_BENCH=false
SKIP_GPU=false
SKIP_CLIPPY=false
SKIP_SMOKE=false
RUST_MODE="--release"
OUTPUT_FILE="full_test_results.txt"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NTG_DIR="${REPO_ROOT}/../aethyro-ntg"
NTG_REPO_URL="https://github.com/leerobber/aethyro-ntg.git"
NTG_BRANCH="main"

# ── Arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-bench)   SKIP_BENCH=true ;;
    --skip-gpu)     SKIP_GPU=true ;;
    --skip-clippy)  SKIP_CLIPPY=true ;;
    --skip-smoke)   SKIP_SMOKE=true ;;
    --debug)        RUST_MODE="" ;;
    --release)      RUST_MODE="--release" ;;
    --ntg-dir)      shift; NTG_DIR="$1" ;;
    --ntg-dir=*)    NTG_DIR="${1#--ntg-dir=}" ;;
    --output)       shift; OUTPUT_FILE="$1" ;;
    --output=*)     OUTPUT_FILE="${1#--output=}" ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

exec > >(tee "$OUTPUT_FILE") 2>&1

# ── Helpers ───────────────────────────────────────────────────────────────────
PIP="python3 -m pip"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
PASS=0
FAIL=0
declare -A RESULTS

sep()    { printf '%0.s═' {1..72}; echo; }
banner() { sep; echo "  $1"; sep; }
ok()     { echo "  ✓ $1"; PASS=$((PASS+1)); RESULTS["$1"]="PASS"; }
fail()   { echo "  ✗ $1"; FAIL=$((FAIL+1)); RESULTS["$1"]="FAIL"; }

run_step() {
  local label="$1"; shift
  echo ""
  echo "▶ $label"
  local t0=$SECONDS
  if "$@" ; then
    echo "  └─ done in $((SECONDS - t0))s"
    ok "$label"
  else
    echo "  └─ FAILED after $((SECONDS - t0))s"
    fail "$label"
  fi
}

# ── Header ────────────────────────────────────────────────────────────────────
banner "FULL PROJECT TEST SUITE  |  $TIMESTAMP"
echo "  MiniMax-M2.7  ·  aethyro-ntg"
echo ""
echo "  MiniMax-M2.7 root : $REPO_ROOT"
echo "  aethyro-ntg dir   : $NTG_DIR"
echo "  Rust build mode   : ${RUST_MODE:-(debug)}"
echo "  Output log        : $OUTPUT_FILE"
echo ""

# ── System info ───────────────────────────────────────────────────────────────
banner "SYSTEM"
echo "  OS     : $(uname -srm)"
echo "  Python : $(python3 --version 2>&1)"
echo "  Rust   : $(rustc --version 2>/dev/null || echo 'not found')"
echo "  Cargo  : $(cargo --version 2>/dev/null || echo 'not found')"
echo ""
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=name,driver_version,memory.total \
    --format=csv,noheader | awk -F',' '{printf "  GPU    : %s  (driver %s, %s)\n",$1,$2,$3}'
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — MiniMax-M2.7 Python/pytest
# ─────────────────────────────────────────────────────────────────────────────
banner "SECTION 1 — MiniMax-M2.7  |  Python sovereign tests"

cd "$REPO_ROOT"

echo "Installing Python dependencies..."
$PIP install -q -r sovereign_requirements.txt

run_step "sovereign pytest (36 tests)" \
  python3 -m pytest tests/test_sovereign_self_evolve.py \
    -v --tb=short --durations=10 -p no:warnings

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — MiniMax-M2.7 CPU vs GPU benchmark
# ─────────────────────────────────────────────────────────────────────────────
if [ "$SKIP_BENCH" = false ]; then
  banner "SECTION 2 — MiniMax-M2.7  |  CPU vs GPU benchmark"

  $PIP install -q numpy

  # torch: CUDA build if GPU requested, else CPU wheel
  if [ "$SKIP_GPU" = false ] && command -v nvidia-smi &>/dev/null; then
    if ! python3 -c "import torch" &>/dev/null; then
      echo "Installing PyTorch (CUDA)..."
      $PIP install -q torch --index-url https://download.pytorch.org/whl/cu121
    fi
    CUDA_OK=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "False")
    if [ "$CUDA_OK" = "False" ]; then
      echo "  CUDA not available to PyTorch — running CPU-only benchmark."
      BENCH_GPU_FLAG="--skip-gpu"
    else
      BENCH_GPU_FLAG=""
    fi
  else
    if ! python3 -c "import torch" &>/dev/null; then
      echo "Installing PyTorch (CPU)..."
      $PIP install -q torch --index-url https://download.pytorch.org/whl/cpu
    fi
    BENCH_GPU_FLAG="--skip-gpu"
  fi

  run_step "CPU vs GPU benchmark" \
    python3 scripts/bench_cpu_gpu.py $BENCH_GPU_FLAG --reps 20 --warmup 5
fi

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — aethyro-ntg: clone / update
# ─────────────────────────────────────────────────────────────────────────────
banner "SECTION 3 — aethyro-ntg  |  Rust cargo tests (386)"

if ! command -v cargo &>/dev/null; then
  echo "ERROR: Rust/cargo not found."
  echo "  Install with: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
  fail "cargo available"
  echo ""
else
  ok "cargo available"

  NTG_DIR="$(realpath -m "$NTG_DIR")"
  if [ ! -d "$NTG_DIR/.git" ]; then
    echo "Cloning aethyro-ntg → $NTG_DIR ..."
    git clone --depth 1 -b "$NTG_BRANCH" "$NTG_REPO_URL" "$NTG_DIR"
  else
    echo "Updating aethyro-ntg..."
    git -C "$NTG_DIR" pull --ff-only || true
  fi

  NTG_KERNEL="$NTG_DIR/kernel"

  # ── 3a. cargo test ───────────────────────────────────────────────────────
  run_step "aethyro-ntg cargo test (386 tests)" \
    bash -c "cd '$NTG_KERNEL' && cargo test $RUST_MODE 2>&1"

  # ── 3b. Smoke binaries (mirrors CI) ─────────────────────────────────────
  if [ "$SKIP_SMOKE" = false ]; then
    banner "SECTION 4 — aethyro-ntg  |  CI smoke binaries"

    run_step "phase4_calib --json (smoke)" \
      bash -c "cd '$NTG_KERNEL' && cargo run $RUST_MODE --bin phase4_calib -- --json 2>&1"

    CALIB_TMP="$(mktemp -d)"
    run_step "phase4_calib roundtrip write+load" \
      bash -c "cd '$NTG_KERNEL' && \
        cargo run $RUST_MODE --bin phase4_calib -- \
          --write-model   '$CALIB_TMP/ci_ntg.calib' \
          --write-sparse  '$CALIB_TMP/ci_ntg.sparse' \
          --write-report  '$CALIB_TMP/ci_ntg.json' \
          --json 2>&1 && \
        test -s '$CALIB_TMP/ci_ntg.calib'  && \
        test -s '$CALIB_TMP/ci_ntg.sparse' && \
        test -s '$CALIB_TMP/ci_ntg.json'"
    rm -rf "$CALIB_TMP"

    run_step "density_bench smoke" \
      bash -c "cd '$NTG_KERNEL' && cargo run $RUST_MODE --bin density_bench 2>&1"
  fi

  # ── 3c. Clippy ───────────────────────────────────────────────────────────
  if [ "$SKIP_CLIPPY" = false ]; then
    banner "SECTION 5 — aethyro-ntg  |  cargo clippy"
    run_step "cargo clippy -D warnings" \
      bash -c "cd '$NTG_KERNEL' && cargo clippy -- -D warnings 2>&1"
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
banner "SUMMARY"
echo ""
for step in "${!RESULTS[@]}"; do
  status="${RESULTS[$step]}"
  if [ "$status" = "PASS" ]; then
    echo "  ✓  $step"
  else
    echo "  ✗  $step"
  fi
done | sort
echo ""
echo "  Passed : $PASS"
echo "  Failed : $FAIL"
echo "  Total  : $((PASS + FAIL))"
echo ""
if [ $FAIL -eq 0 ]; then
  echo "  ✓ ALL STEPS PASSED"
  EXIT_CODE=0
else
  echo "  ✗ $FAIL STEP(S) FAILED — see $OUTPUT_FILE for details"
  EXIT_CODE=1
fi
sep
echo "  Log saved to: $OUTPUT_FILE"
sep
exit $EXIT_CODE
