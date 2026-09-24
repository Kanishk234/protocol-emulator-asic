#!/usr/bin/env bash
# R2: post-route STA of the hardened lane, with EVAL and EXEC endpoints separated. The flow's own
# report lists only the 1000 worst paths, and all of them are latch data pins at slack 0 (time
# borrowing), so the lane's real paths do not appear in it.
# Uses the routed netlist and extracted parasitics from a gds run's GDS_logs artifact, with the flow's
# sign-off settings (20 ns, 0.25 ns uncertainty, +/-5 % derate, propagated clock, 4 ns I/O delays,
# 6 fF output load). Check: its hold slacks should equal the flow's 55-openroad-stapostpnr/summary.rpt.
#
# Usage: spikes/r2_latch/post_route_sta.sh [path/to/runs/wokwi]   (default: build/ci/r2/GDS_logs/runs/wokwi)
# Needs the OpenSTA and liberty caches that spikes/r1_lane/run_r1.sh sets up.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${1:-$ROOT/build/ci/r2/GDS_logs/runs/wokwi}"
OUT="$ROOT/build/ci/r2/post_route_sta"
mkdir -p "$OUT"
OR="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire/openroad"
L=$(ls -d "${XDG_CACHE_HOME:-$HOME/.cache}"/tripwire/pdk-*/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib | head -1)

for c in typ_1p20V_25C slow_1p08V_125C fast_1p32V_m40C; do
  cat > "$OUT/sta_$c.tcl" <<T
read_liberty $L/sg13cmos5l_stdcell_$c.lib
read_verilog final/nl/tt_um_tripwire.nl.v
link_design tt_um_tripwire
read_spef final/spef/nom/tt_um_tripwire.nom.spef
create_clock -name clk -period 20 [get_ports clk]
set_clock_uncertainty 0.25 [get_clocks clk]
set_clock_transition 0.15 [get_clocks clk]
set_timing_derate -early 0.95
set_timing_derate -late 1.05
set_input_delay 4 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 4 -clock clk [all_outputs]
set_load 0.006 [all_outputs]
set_propagated_clock [all_clocks]
proc regs_of {pat} {
  set cells {}
  foreach n [get_nets -quiet \$pat] {
    foreach p [get_pins -quiet -of_objects \$n -filter "direction == output"] {
      set c [get_cells -of_objects \$p]
      if {[string match "sg13cmos5l_d*" [get_property [get_lib_cells -of_objects \$c] name]]} { lappend cells \$c }
    }
  }
  return \$cells
}
set eval_regs [concat [regs_of {u_lane.state[*]}] [regs_of {u_lane.pend[*]}] [regs_of u_lane.rb] \
  [regs_of {u_lane.resv[*]}] [regs_of u_lane.ex_slot] [regs_of u_lane.ex_rt] [regs_of {u_lane.ex_op[*]}] \
  [regs_of {u_lane.ex_dst[*]}] [regs_of {u_lane.ex_asrc[*]}] [regs_of {u_lane.ex_bsel[*]}] \
  [regs_of {u_lane.ex_imm[*]}] [regs_of u_lane.ex_dfe] [regs_of {u_lane.ex_df[*]}] [regs_of {u_lane.ex_ot[*]}] \
  [regs_of u_lane.ex_kt] [regs_of {u_lane.a_lat[*]}] [regs_of {u_lane.a_tag[*]}] [regs_of u_lane.call_req] \
  [regs_of {u_lane.call_idx[*]}] [regs_of u_i0.last_seq]]
set exec_regs [concat [regs_of {u_lane.regs[*]}] [regs_of {u_lane.f[*]}] [regs_of u_lane.rz] \
  [regs_of {u_lane.out_valid[*]}] [regs_of {u_lane.out_seq[*]}] [regs_of {u_lane.out_tok[*]}]]
puts "EVAL regs [llength \$eval_regs], EXEC regs [llength \$exec_regs], flop D pins [llength [all_registers -edge_triggered -data_pins]], latch D pins [llength [all_registers -level_sensitive -data_pins]]"
puts "== EVAL"; report_checks -path_delay max -to \$eval_regs -format end -group_count 1
puts "== EXEC"; report_checks -path_delay max -to \$exec_regs -format end -group_count 1
puts "== all flop endpoints"; report_checks -path_delay max -to [all_registers -edge_triggered -data_pins] -format end -group_count 1
puts "== outputs"; report_checks -path_delay max -to [all_outputs] -format end -group_count 1
puts "== latch endpoints (borrow)"; report_checks -path_delay max -to [all_registers -level_sensitive -data_pins] -format end -group_count 1
puts "== hold"; report_checks -path_delay min -format end -group_count 1
puts "== EVAL path"; report_checks -path_delay max -to \$eval_regs -fields {nets} -digits 3
exit
T
  echo "######## $c"
  LD_LIBRARY_PATH="$OR/x/usr/lib/x86_64-linux-gnu" TCL_LIBRARY="$OR/x/usr/share/tcltk/tcl8.6" \
    "$OR/x/usr/bin/sta" -no_init -no_splash -exit "$OUT/sta_$c.tcl" </dev/null > "$OUT/sta_$c.txt" 2>&1 || true
  grep -E "regs|^== (EVAL|EXEC|all|outputs|latch|hold)$|MET|VIOL" "$OUT/sta_$c.txt" | head -14
done
echo "post_route_sta: reports in $OUT"
