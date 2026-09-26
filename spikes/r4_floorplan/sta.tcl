# R4: pre-layout static timing of the Yosys netlist (ideal clock, no wires), as spikes/r1_lane/sta.tcl.
# Env: R4_LIB, R4_MACRO_LIB, R4_NET, R4_PERIOD. Configuration latches (slots, K, pin configuration) are
# written only while halted (§14 H1), so they are false-path startpoints; latch D pins borrow time by
# design (R2), so the reported paths end at flop D pins and outputs.
read_liberty $::env(R4_LIB)
read_liberty $::env(R4_MACRO_LIB)
read_verilog $::env(R4_NET)
link_design tt_um_tripwire
create_clock -name clk -period $::env(R4_PERIOD) [get_ports clk]
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
set_false_path -from $latches
puts "\n==== worst path to a flop"
report_checks -path_delay max -to $flop_d -digits 3 -fields {nets}
puts "\n==== ten worst flop endpoints"
report_checks -path_delay max -to $flop_d -group_count 10 -endpoint_count 1 -format end
puts "\n==== summary"
report_worst_slack -max
report_worst_slack -min
exit
