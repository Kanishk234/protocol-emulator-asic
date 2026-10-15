# Read-only per-net checks: expose legal but marginal electrical constraints.
# Called after libraries, constraints and parasitics load in corner.tcl.
if {![info exists corner_name]} {error "Missing margin probe corner"}
puts "%OL_CREATE_REPORT electrical_margin.rpt"
puts "TRIPWIRE_MARGIN_BEGIN $corner_name"
set tripwire_margin_count 0
foreach tripwire_margin_net [get_nets -hierarchical *] {
    set tripwire_margin_name [get_full_name $tripwire_margin_net]
    puts "TRIPWIRE_NET_HEX [binary encode hex $tripwire_margin_name]"
    report_check_types -max_slew -max_capacitance -max_fanout \
        -net $tripwire_margin_net -corner $corner_name -format end \
        -digits 6 -no_line_splits
    incr tripwire_margin_count
}
puts "TRIPWIRE_MARGIN_END $corner_name $tripwire_margin_count"
puts "%OL_END_REPORT"
