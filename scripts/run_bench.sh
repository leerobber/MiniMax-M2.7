#!/usr/bin/env bash
# =============================================================================
# scripts/run_bench.sh
# MiniMax-M2.7 — CPU vs GPU performance benchmark + sovereign test suite
#
# Usage:
#   ./scripts/run_bench.sh [--skip-gpu] [--skip-tests] [--output FILE]
#
# Options:
#   --skip-gpu      Skip GPU benchmarks (CPU-only mode)
#   --skip-tests    Skip pytest sovereign test suite
#   --output FILE   Write results to FILE in addition to stdout (default: bench_results.txt)
# =============================================================================

set -euo pipefail

# ── Argument parsing ──────────────────────────────────────────────────────────
SKIP_GPU=false
SKIP_TESTS=false
OUTPUT_FILE="bench_results.txt"

for arg in "$@"; do
  case "$arg" in
    --skip-gpu)    SKIP_GPU=true ;;
    --skip-tests)  SKIP_TESTS=true ;;
    --output)      shift; OUTPUT_FILE="$1" ;;
    --output=*)    OUTPUT_FILE="${arg#--output=}" ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCH_PY="$SCRIPT_DIR/bench_cpu_gpu.py"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# Tee all output to file
exec > >(tee "$OUTPUT_FILE") 2>&1

sep() { printf '%0.s═' {1..72}; echo; }
banner() { sep; echo "  $1"; sep; }

# ── Header ────────────────────────────────────────────────────────────────────
banner "MiniMax-M2.7  |  CPU vs GPU Benchmark  |  $TIMESTAMP"

# ── System info ───────────────────────────────────────────────────────────────
banner "SYSTEM INFORMATION"

echo "OS:      $(uname -srm)"
echo "Kernel:  $(uname -r)"
echo "Python:  $(python3 --version 2>&1)"
echo ""

echo "── CPU ──────────────────────────────────────────"
if command -v lscpu &>/dev/null; then
  lscpu | grep -E "^(Model name|Architecture|CPU\(s\)|Thread|Core|Socket|MHz|NUMA)" | \
    sed 's/^/  /'
else
  sysctl -n machdep.cpu.brand_string 2>/dev/null || cat /proc/cpuinfo | grep "model name" | head -1
fi
echo ""

echo "── Memory ───────────────────────────────────────"
if [ -f /proc/meminfo ]; then
  grep -E "^(MemTotal|MemAvailable|MemFree)" /proc/meminfo | sed 's/^/  /'
else
  vm_stat 2>/dev/null | head -5 || true
fi
echo ""

echo "── GPU ──────────────────────────────────────────"
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free,utilization.gpu,temperature.gpu \
    --format=csv,noheader | \
    awk -F',' '{printf "  GPU:     %s\n  Driver:  %s\n  VRAM:    %s total / %s free\n  Util:    %s\n  Temp:    %s\n", $1,$2,$3,$4,$5,$6}'
  GPU_AVAILABLE=true
else
  echo "  nvidia-smi not found — GPU benchmarks will be skipped."
  GPU_AVAILABLE=false
  SKIP_GPU=true
fi
echo ""

# ── Dependency install ────────────────────────────────────────────────────────
banner "INSTALLING DEPENDENCIES"

cd "$REPO_ROOT"

PIP="python3 -m pip"

$PIP install -q -r sovereign_requirements.txt
$PIP install -q numpy

# Install torch if GPU benchmarking is requested and torch isn't present
if [ "$SKIP_GPU" = false ]; then
  if ! python3 -c "import torch" &>/dev/null; then
    echo "Installing PyTorch with CUDA support..."
    $PIP install -q torch --index-url https://download.pytorch.org/whl/cu121
  else
    echo "PyTorch already installed: $(python3 -c 'import torch; print(torch.__version__)')"
  fi
  TORCH_CUDA=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "False")
  echo "torch.cuda.is_available() = $TORCH_CUDA"
  if [ "$TORCH_CUDA" = "False" ]; then
    echo "WARNING: CUDA not available to PyTorch — GPU benchmarks will be CPU-only."
    SKIP_GPU=true
  fi
else
  $PIP install -q torch --index-url https://download.pytorch.org/whl/cpu 2>/dev/null || \
    $PIP install -q torch 2>/dev/null || true
fi

echo "All dependencies installed."
echo ""

# ── Sovereign test suite ──────────────────────────────────────────────────────
if [ "$SKIP_TESTS" = false ]; then
  banner "SOVEREIGN TEST SUITE  (pytest)"
  TEST_START=$(date +%s%N)
  set +e
  python3 -m pytest tests/test_sovereign_self_evolve.py -v \
    --tb=short \
    --durations=10 \
    -p no:warnings \
    2>&1
  TEST_RC=$?
  set -e
  TEST_END=$(date +%s%N)
  TEST_MS=$(( (TEST_END - TEST_START) / 1000000 ))
  echo ""
  echo "Test suite finished in ${TEST_MS}ms — exit code: $TEST_RC"
  if [ $TEST_RC -eq 0 ]; then
    echo "RESULT: ✓ ALL TESTS PASSED"
  else
    echo "RESULT: ✗ SOME TESTS FAILED"
  fi
  echo ""
fi

# ── CPU / GPU benchmarks ──────────────────────────────────────────────────────
banner "CPU vs GPU MATRIX & MEMORY BENCHMARKS"

python3 "$BENCH_PY" $([ "$SKIP_GPU" = true ] && echo "--skip-gpu")
echo ""

# ── vLLM endpoint check (optional) ───────────────────────────────────────────
banner "SOVEREIGN API ENDPOINT CHECK"

SOVEREIGN_API_BASE="${SOVEREIGN_API_BASE:-http://localhost:8001/v1}"
echo "Checking endpoint: $SOVEREIGN_API_BASE"
if curl -sf --max-time 3 "$SOVEREIGN_API_BASE/models" -o /dev/null 2>/dev/null; then
  echo "  ✓ vLLM endpoint is LIVE at $SOVEREIGN_API_BASE"
  curl -s --max-time 3 "$SOVEREIGN_API_BASE/models" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); [print('  Model:', m['id']) for m in d.get('data',[])]" \
    2>/dev/null || true
else
  echo "  ✗ vLLM endpoint NOT reachable at $SOVEREIGN_API_BASE"
  echo "    Start with: vllm serve qwen2.5-32b-awq --port 8001 --dtype auto"
fi
echo ""

# ── Final summary ─────────────────────────────────────────────────────────────
banner "BENCHMARK COMPLETE"
echo "Full results saved to: $OUTPUT_FILE"
echo ""
