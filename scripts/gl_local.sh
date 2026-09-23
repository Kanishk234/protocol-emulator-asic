#!/usr/bin/env bash
# Run the pin-level test suite (test/) on a gate-level netlist locally, the way CI's gl_test does.
#
# Usage:
#   scripts/gl_local.sh                 synthesize src/ with Yosys onto the cmos5l cells, then test it
#   scripts/gl_local.sh path/to/net.v   test a given netlist (e.g. the tt_submission/*.v from a gds run)
#
# Uses the same PDK revision and the same Tiny Tapeout Icarus 13 build as tt-gds-action's gl_test.
# Stock Icarus 12 does not drive the cell models' delayed_* timing-check nets, so every flop reads X
# (docs/BUGS.md #1). Downloads are cached in ${XDG_CACHE_HOME:-~/.cache}/tripwire.
#
# A Yosys netlist is not the hardened netlist: it checks the cell models and X-safety after reset,
# not placement, CTS or timing. The CI gl_test on the real netlist remains the evidence.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Pinned to tt-gds-action@ihp-cmos5l install_sg13cmos5l.sh (IHP-Open-PDK dev, 2026-09-08). Update together.
PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"
IVERILOG_DEB_URL="https://github.com/TinyTapeout/iverilog/releases/download/v13.0/iverilog_13.0-1_amd64.deb"
LIB_CORNER="sg13cmos5l_stdcell_typ_1p20V_25C.lib"

CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire"
PDK_ROOT="$CACHE/pdk-$PDK_REV"
REF="$PDK_ROOT/ihp-sg13cmos5l/libs.ref"
IV="$CACHE/iverilog-13"

# Python: always the project venv.
if [ ! -f .venv/bin/activate ]; then
  echo "error: .venv missing; run scripts/setup_venv.sh" >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi

fetch() {  # fetch <path under libs.ref>
  local dst="$REF/$1"
  if [ ! -s "$dst" ]; then
    mkdir -p "$(dirname "$dst")"
    curl -sfL -o "$dst" \
      "https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/$PDK_REV/ihp-sg13cmos5l/libs.ref/$1"
  fi
}

echo "=== PDK models ($PDK_REV)"
fetch sg13cmos5l_io/verilog/sg13cmos5l_io.v
fetch sg13cmos5l_stdcell/verilog/sg13cmos5l_stdcell.v
fetch sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v
fetch "sg13cmos5l_stdcell/lib/$LIB_CORNER"

echo "=== Tiny Tapeout Icarus 13"
if [ ! -x "$IV/usr/bin/iverilog" ]; then
  mkdir -p "$CACHE"
  curl -sfL -o "$CACHE/iverilog13.deb" "$IVERILOG_DEB_URL"
  rm -rf "$IV"
  dpkg-deb -x "$CACHE/iverilog13.deb" "$IV"
fi
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -V 2>&1 | sed -n 1p

NETLIST="test/gate_level_netlist.v"   # git-ignored; the name the test Makefile expects
if [ $# -ge 1 ]; then
  echo "=== netlist: $1"
  cp "$1" "$NETLIST"
else
  echo "=== netlist: Yosys synthesis of src/ onto $LIB_CORNER"
  SOURCES=$(python - <<'EOF'
import yaml
print(" ".join("src/" + f for f in yaml.safe_load(open("info.yaml"))["project"]["source_files"]))
EOF
)
  TOP=$(python -c 'import yaml; print(yaml.safe_load(open("info.yaml"))["project"]["top_module"])')
  LIB="$REF/sg13cmos5l_stdcell/lib/$LIB_CORNER"
  yosys -q -p "read_verilog -Isrc $SOURCES; synth -top $TOP -flatten; dfflibmap -liberty $LIB; abc -liberty $LIB; opt_clean; write_verilog -noattr -noexpr $NETLIST"
fi

echo "=== test/: pin-level suite on the netlist"
export PATH="$IV/usr/bin:$PATH"
export IVERILOG_VPI_MODULE_PATH="$IV/usr/lib/ivl"
export COMPILE_ARGS="-B $IV/usr/lib/ivl"   # the Makefile appends its own GL defines
export PDK_ROOT
rm -rf test/sim_build/gl test/results.xml
GATES=yes make -C test 2>&1 | grep -v "sorry: ifnone with an edge-sensitive path"

test -f test/results.xml
if grep -q failure test/results.xml; then
  echo "gl_local: FAIL" >&2
  exit 1
fi
echo "gl_local: PASS"
