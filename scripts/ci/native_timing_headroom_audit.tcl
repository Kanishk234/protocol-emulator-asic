# Preserve the same ODB connectivity export and electrical reserve audit.
source [file join [file dirname [info script]] native_post_antenna_audit.tcl]
# Report FF capture paths separately: latch endpoints at zero slack can occupy
# the generic report's entire top-N list. These are read-only diagnostics.
set trw_capture_pins [all_registers -edge_triggered -data_pins]
if {[llength $trw_capture_pins] == 0} {error "Missing edge-triggered capture pins"}
report_checks -sort_by_slack -path_delay max -to $trw_capture_pins -group_path_count 20 -endpoint_path_count 1 -format full_clock_expanded -fields {slew cap input net fanout} -digits 6 -corner $corner_name > [file join $::env(STEP_DIR) capture_setup.rpt]
report_checks -sort_by_slack -path_delay min -to $trw_capture_pins -group_path_count 20 -endpoint_path_count 1 -format full_clock_expanded -fields {slew cap input net fanout} -digits 6 -corner $corner_name > [file join $::env(STEP_DIR) capture_hold.rpt]
puts "TRIPWIRE read-only FF capture headroom reports exported"
