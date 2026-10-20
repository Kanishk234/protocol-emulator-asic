# Read-only slow-corner measurements of the exact failed TX screen.
if {$corner_name ne "nom_slow_1p08V_125C"} {error "Wrong diagnostic corner"}
write_verilog [file join $::env(STEP_DIR) stage_readback.v]
puts "%OL_CREATE_REPORT electrical_margin.rpt"
puts "TRIPWIRE_MARGIN_BEGIN $corner_name"
foreach n {_09431_ _21816_} {
    set obj [get_nets -quiet $n]
    if {[llength $obj] != 1} {error "Missing unique diagnostic net $n"}
    puts "TRIPWIRE_NET_HEX [binary encode hex $n]"
    report_check_types -max_slew -max_capacitance -max_fanout -net $obj \
        -corner $corner_name -format end -digits 6 -no_line_splits
}
puts "TRIPWIRE_MARGIN_END $corner_name 2"
puts "%OL_END_REPORT"
set capture [all_registers -edge_triggered -data_pins]
if {[llength $capture] == 0} {error "Missing capture pins"}
report_checks -sort_by_slack -path_delay max -to $capture -group_path_count 20 \
    -endpoint_path_count 1 -format full_clock_expanded -fields {slew cap input net fanout} \
    -digits 6 -corner $corner_name > [file join $::env(STEP_DIR) capture_setup.rpt]
