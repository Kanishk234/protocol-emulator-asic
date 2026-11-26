#!/usr/bin/env bash
# Exercise both SRAM implementations against the same read/hold reference.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
out=build/basys3-preflight/sram-check
macro=macro/RM_IHPSG13_1P_512x16_c2_bm_bist
mkdir -p "$out"
sed 's/module trw_sram (/module trw_sram_fpga (/' fpga/basys3/trw_sram.v > "$out/trw_sram_fpga.v"
iverilog -g2012 -DFUNCTIONAL -s tb_sram -o "$out/tb_sram.vvp" \
  test_internal/fpga/tb_sram.v "$out/trw_sram_fpga.v" src/trw_sram.v \
  "$macro/RM_IHPSG13_1P_core_behavioral_bm_bist.v" "$macro/RM_IHPSG13_1P_512x16_c2_bm_bist.v"
vvp "$out/tb_sram.vvp"
