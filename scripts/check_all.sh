#!/usr/bin/env bash
# TRIPWIRE local check: lint + pin-level tests + internal tests, in one command.
# Usage: scripts/check_all.sh
# Needs: .venv (scripts/setup_venv.sh), Icarus, and the OSS CAD Suite (Verilator, Yosys).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Python: always the project venv.
if [ ! -f .venv/bin/activate ]; then
  echo "error: .venv missing; run scripts/setup_venv.sh" >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# OSS CAD Suite: appended (not prepended) so the system Icarus, the one CI uses, wins.
if ! command -v verilator >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi
for tool in iverilog verilator yosys sigrok-cli; do
  command -v "$tool" >/dev/null || { echo "error: $tool not found" >&2; exit 1; }
done

# Keep info.yaml source_files and test/Makefile PROJECT_SOURCES in sync (L0-TT).
yaml_src=$(python - <<'EOF'
import yaml
print(" ".join(yaml.safe_load(open("info.yaml"))["project"]["source_files"]))
EOF
)
make_src=$(sed -n 's/^PROJECT_SOURCES *= *//p' test/Makefile)
SOURCES=()
for f in $yaml_src; do SOURCES+=("src/$f"); done

step() { echo; echo "=== $* ==="; }

step "L0-TT: source lists in sync"
if [ "$yaml_src" != "$make_src" ]; then
  echo "info.yaml source_files ($yaml_src) != test/Makefile PROJECT_SOURCES ($make_src)" >&2
  exit 1
fi
echo "ok: $yaml_src"

step "L0-LINT: verilator --lint-only -Wall"
verilator --lint-only -Wall -Isrc --top-module tt_um_tripwire "${SOURCES[@]}"
echo "ok"

step "L0-SYNTH: yosys synth sanity"
yosys -q -p "read_verilog -Isrc ${SOURCES[*]}; synth -top tt_um_tripwire; check -assert; select -assert-none t:\$dlatch t:\$_DLATCH_*"
echo "ok"

step "sigrok: UART decode of a VCD (toolchain smoke test)"
python scripts/sigrok_smoke.py

step "test/: pin-level cocotb suite (RTL)"
make -C test clean >/dev/null
make -C test
if grep -q failure test/results.xml; then
  echo "error: failures in test/results.xml" >&2
  exit 1
fi

if [ -f test_internal/Makefile ]; then
  step "test_internal/: white-box tests"
  make -C test_internal
fi

echo; echo "check_all: PASS"
