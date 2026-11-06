# Read-only report expansion; do not modify constraints or loaded design.
if {![info exists corner_name]} {error "Missing current corner"}
puts "%OL_CREATE_REPORT c_select_setup_frontier.rpt"
puts "TRIPWIRE_C_SELECT_FRONTIER $corner_name"
report_checks -sort_by_slack -path_delay max -group_path_count 20 \
    -endpoint_path_count 2 -format full_clock_expanded \
    -fields {slew cap input net fanout} -digits 6 -corner $corner_name
puts "%OL_END_REPORT"
set trw_slew_pin [get_pins _48011_/Y]
if {[llength $trw_slew_pin] != 1} {error "Missing exact slew driver"}
puts "%OL_CREATE_REPORT c_select_slew_path.rpt"
puts "TRIPWIRE_C_SELECT_SLEW_PATH $corner_name"
report_checks -sort_by_slack -path_delay max -through $trw_slew_pin \
    -group_path_count 4 -endpoint_path_count 1 -format full_clock_expanded \
    -fields {slew cap input net fanout} -digits 6 -corner $corner_name
puts "%OL_END_REPORT"
