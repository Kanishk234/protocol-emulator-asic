# Read-only ODB exports, not physical repair or timing-constraint changes.
# Native RepairAntennas exports ODB/DEF but inherits the older NL/PNL views.
if {![info exists ::env(STEP_DIR)]} {error "Missing STA step output directory"}
write_verilog [file join $::env(STEP_DIR) native_antenna.nl.v]
write_verilog -include_pwr_gnd [file join $::env(STEP_DIR) native_antenna.pnl.v]
puts "TRIPWIRE native antenna ODB netlist readback exported"
source [file join [file dirname [info script]] electrical_margin_probe.tcl]
