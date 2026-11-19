# Read-only path expansion. Configuration latch launch paths remain timed.
# Latch-data borrowing endpoints remain covered by the ordinary all-path checks.
if {![info exists corner_name]} {error "Missing current corner"}
set trw_flop_d {}
foreach trw_cell [get_cells *] {
    set trw_master [get_property [get_lib_cells -of_objects $trw_cell] name]
    if {[string match "sg13cmos5l_df*" $trw_master]} {
        foreach trw_pin [get_pins -of_objects $trw_cell -filter "direction == input && name == D"] {
            lappend trw_flop_d $trw_pin
        }
    }
}
if {[llength $trw_flop_d] == 0} {error "Missing functional flop endpoints"}
set trw_functional_ends [concat $trw_flop_d [all_outputs]]
puts "%OL_CREATE_REPORT functional_setup_frontier.rpt"
puts "TRIPWIRE_FUNCTIONAL_SETUP $corner_name"
puts "FLOP_DATA_ENDPOINTS [llength $trw_flop_d]"
puts "OUTPUT_ENDPOINTS [llength [all_outputs]]"
report_checks -path_delay max -to $trw_functional_ends -sort_by_slack \
    -group_count 5 -endpoint_count 1 -format full_clock_expanded \
    -fields {slew cap input net fanout} -digits 6 -corner $corner_name
puts "%OL_END_REPORT"
