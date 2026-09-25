#!/usr/bin/env bash
# WARP local check: lint + all simulation tests, in one command.
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
if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi
for tool in iverilog verilator yosys; do
  command -v "$tool" >/dev/null || { echo "error: $tool not found" >&2; exit 1; }
done

TOP=$(python -c 'import yaml; print(yaml.safe_load(open("info.yaml"))["project"]["top_module"])')
yaml_src=$(python -c 'import yaml; print(" ".join(yaml.safe_load(open("info.yaml"))["project"]["source_files"]))')
make_src=$(sed -n 's/^PROJECT_SOURCES *= *//p' test/Makefile)
SOURCES=()
for f in $yaml_src; do SOURCES+=("src/$f"); done

step() { echo; echo "=== $* ==="; }

step "source lists in sync (info.yaml vs test/Makefile)"
if [ "$yaml_src" != "$make_src" ]; then
  echo "info.yaml source_files ($yaml_src) != test/Makefile PROJECT_SOURCES ($make_src)" >&2
  exit 1
fi
echo "ok: $yaml_src"

step "lint: verilator --lint-only -Wall"
verilator --lint-only -Wall -Isrc --top-module "$TOP" "${SOURCES[@]}"
echo "ok"

step "lint: iverilog -g2005"
iverilog -g2005 -Isrc -s "$TOP" -o /dev/null "${SOURCES[@]}"
echo "ok"

step "synth: yosys sanity (no latches outside configuration storage)"
# Latches are allowed only in generated fabric config storage and wp_cfg_* modules (CLAUDE.md).
yosys -q -p "read_verilog -Isrc ${SOURCES[*]}; synth -top $TOP; check -assert"
echo "ok"

if compgen -G "tools/**/test_*.py" >/dev/null || compgen -G "tools/*/tests/test_*.py" >/dev/null; then
  step "tools: pytest"
  python -m pytest -q -n auto
fi

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
