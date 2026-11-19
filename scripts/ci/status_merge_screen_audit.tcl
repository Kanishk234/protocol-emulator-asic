# Read-only exports and functional path reporting from the final native ODB.
if {![info exists ::env(STEP_DIR)]} {error "Missing STA output directory"}
write_verilog [file join $::env(STEP_DIR) screen_native.nl.v]
write_verilog -include_pwr_gnd [file join $::env(STEP_DIR) screen_native.pnl.v]
source [file join [file dirname [info script]] functional_setup_frontier.tcl]
