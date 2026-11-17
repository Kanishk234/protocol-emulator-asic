# Read-only reports and fresh ODB exports; no physical repair or SDC changes.
if {![info exists ::env(STEP_DIR)]} {error "Missing STA output directory"}
write_verilog [file join $::env(STEP_DIR) native_antenna.nl.v]
write_verilog -include_pwr_gnd [file join $::env(STEP_DIR) native_antenna.pnl.v]
source [file join [file dirname [info script]] functional_setup_frontier.tcl]
