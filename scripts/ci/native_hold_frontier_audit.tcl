# Read-only diagnostics on the loaded checkpoint; no repair or routing commands.
if {![info exists corner_name] || ![info exists ::env(STEP_DIR)]} {
    error "Missing hold-frontier corner/output directory"
}
write_verilog [file join $::env(STEP_DIR) checkpoint_readback.nl.v]
write_verilog -include_pwr_gnd [file join $::env(STEP_DIR) checkpoint_readback.pnl.v]
set trw_frontier_pins [all_registers -edge_triggered -data_pins]
if {[llength $trw_frontier_pins] == 0} {error "No FF data endpoints"}
puts "%OL_CREATE_REPORT hold_frontier.rpt"
puts "TRIPWIRE_HOLD_FRONTIER_BEGIN $corner_name 0.05 100000"
report_checks -sort_by_slack -path_delay min -to $trw_frontier_pins \
    -slack_max 0.05 -group_path_count 100000 -endpoint_path_count 1 \
    -format full_clock_expanded -fields {slew cap input net fanout} \
    -digits 6 -corner $corner_name
puts "TRIPWIRE_HOLD_FRONTIER_END $corner_name"
puts "%OL_END_REPORT"
