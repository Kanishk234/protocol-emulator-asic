#!/usr/bin/env bash
# Whole-chip protocol regression on an ignored status-merge candidate copy.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
export PATH="$PATH:$HOME/oss-cad-suite/bin"
python scripts/check_status_merge_candidate.py
python - <<'PY'
from pathlib import Path
import shutil
for path in Path('src').iterdir():
    if path.is_file() and path.name != 'trw_pin_bs.v':
        shutil.copyfile(path, Path('build/pin_unit_status_candidate/src') / path.name)
PY
candidate_root="$PWD/build/pin_unit_status_candidate"
make -C test_internal/chip SIM=verilator \
  SRC_DIR="$candidate_root/src" SIM_BUILD="$candidate_root/chip_sim_vl" \
  COCOTB_RESULTS_FILE="$candidate_root/chip_results_vl.xml" \
  COCOTB_TEST_MODULES=test_chip,test_l3,test_rot,test_phase3,test_ack_path,test_spi_flash,test_onewire_overdrive,test_ps2_framing,test_uart_bridge,test_capture_replay,test_metamorphic_tap,test_metamorphic_loop,test_metamorphic_perm,test_metamorphic_timing
