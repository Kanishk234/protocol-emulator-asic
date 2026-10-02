# Chip: pre-layout static timing of the Yosys netlist of trw_chip (ideal clock, no wires), as R4's sta.tcl.
# Env: CHIP_LIB, CHIP_MACRO_LIB, CHIP_NET, CHIP_PERIOD. Keep latch outputs as timed startpoints: D-066
# allows pin configuration writes after units are live, and the updated value reaches unit state next clock.
# Latch D pins borrow time by design (R2), so the reported paths end at flop D pins and outputs.
read_liberty $::env(CHIP_LIB)
read_liberty $::env(CHIP_MACRO_LIB)
read_verilog $::env(CHIP_NET)
link_design trw_chip
create_clock -name clk -period $::env(CHIP_PERIOD) [get_ports clk]
set_clock_uncertainty -setup 0.25 [get_clocks clk]
set_input_delay 0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0 -clock clk [all_outputs]
set_load 0.01 [all_outputs]
set latches {}
set flop_d {}
foreach c [get_cells *] {
    set lc [get_property [get_lib_cells -of_objects $c] name]
    if {[string match "sg13cmos5l_dlhq*" $lc]} { lappend latches $c }
    if {[string match "sg13cmos5l_df*" $lc]} { lappend flop_d [get_pins -of_objects $c -filter "direction == input && name == D"] }
}
puts "latch cells: [llength $latches]; flop D pins: [llength $flop_d]"
puts "latch outputs remain timed startpoints (including pin configuration, D-066)"
puts "\n==== worst path to a flop"
report_checks -path_delay max -to $flop_d -digits 3 -fields {nets}
puts "\n==== worst path from the SRAM macro's outputs (fetched word into EVAL, D-045)"
report_checks -path_delay max -through [get_pins -hierarchical *sram*A_DOUT*] -to $flop_d -digits 3
puts "\n==== ten worst flop endpoints"
report_checks -path_delay max -to $flop_d -group_count 10 -endpoint_count 1 -format end
puts "\n==== summary"
report_worst_slack -max
report_worst_slack -min
exit
