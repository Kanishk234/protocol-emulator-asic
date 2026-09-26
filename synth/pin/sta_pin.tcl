# Static timing of the synthesized pin-unit wrapper (trw_pin_meas) with OpenSTA, pre-layout: ideal clock,
# no wire parasitics (as spikes/r1_lane/sta.tcl).
# Env: PIN_LIB (liberty), PIN_NET (netlist), PIN_PERIOD (ns), PIN_CFG_STATIC (1: the configuration
# latches are false-path startpoints, since the host writes them only while halted, §14 H1, D-038).
# Latch D pins borrow time by design (0 slack, as in R2), so the reported paths end at flop D pins.
read_liberty $::env(PIN_LIB)
read_verilog $::env(PIN_NET)
link_design trw_pin_meas

create_clock -name clk -period $::env(PIN_PERIOD) [get_ports clk]
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
if {$::env(PIN_CFG_STATIC) == 1 && [llength $latches] > 0} {
    set_false_path -from $latches
    puts "configuration latches set as false-path startpoints"
}

puts "\n==== worst path to a flop"
report_checks -path_delay max -to $flop_d -digits 3 -fields {fanout nets}
puts "\n==== ten worst flop endpoints"
report_checks -path_delay max -to $flop_d -group_count 10 -endpoint_count 1 -format end
puts "\n==== worst path to an output"
report_checks -path_delay max -to [all_outputs] -digits 3 -fields {nets}
puts "\n==== worst hold"
report_checks -path_delay min -digits 3 -format end -group_count 5
puts "\n==== summary"
report_wns
report_worst_slack -max
report_worst_slack -min
exit
