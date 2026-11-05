# Diagnostic-only exact three-cell substitution; no official-flow authority.
source [file join [file dirname [info script]] native_hold100_size.tcl]
set trw_targets {
 {wire13568 sg13cmos5l_buf_2 sg13cmos5l_buf_8 {{A} {_19518_} {X} {net13567}}}
 {wire12579 sg13cmos5l_buf_2 sg13cmos5l_buf_4 {{A} {net12579} {X} {net12578}}}
 {_38673_ sg13cmos5l_nand2_1 sg13cmos5l_nand2_2 {{Y} {_11579_} {A} {net11878} {B} {u_chip.g_lane\[1\].slots\[626\]}}}
}
tripwire_size_native_hold100 $trw_targets
# Native legalization is mandatory: BUF4 growth conflicts with a neighbor.
detailed_placement
check_placement -verbose
if {![info exists ::env(STEP_DIR)]} {error "Missing diagnostic output directory"}
set trw_snapshot [file join $::env(STEP_DIR) targeted_sizing]
write_db ${trw_snapshot}.odb
write_def ${trw_snapshot}.def
write_verilog ${trw_snapshot}.nl.v
write_verilog -include_pwr_gnd ${trw_snapshot}.pnl.v
puts "TRIPWIRE targeted sizing snapshot exported; fresh rerouting/STA/antenna checks required"
