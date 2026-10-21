# Same full electrical, fresh ODB exports and capture-path measurements.
source [file join [file dirname [info script]] native_timing_headroom_audit.tcl]
# Diagnostic route coverage only, never a replacement for DRT/extraction.
set trw_block [ord::get_db_block]
set trw_signal_nets 0
set trw_guide_nets 0
set trw_wire_nets 0
set trw_missing_nets 0
set trw_report [open [file join $::env(STEP_DIR) route_coverage.rpt] w]
puts $trw_report "TRIPWIRE_ROUTE_COVERAGE_BEGIN $corner_name"
foreach trw_net [$trw_block getNets] {
    if {[$trw_net getSigType] ne "SIGNAL"} {continue}
    set trw_count [expr {[llength [$trw_net getITerms]] + [llength [$trw_net getBTerms]]}]
    if {$trw_count < 2} {continue}
    incr trw_signal_nets
    if {[llength [$trw_net getGuides]] > 0} {
        incr trw_guide_nets
    } elseif {[$trw_net getWire] ne "NULL"} {
        incr trw_wire_nets
    } else {
        incr trw_missing_nets
        puts $trw_report "MISSING_NET_HEX [binary encode hex [$trw_net getName]]"
    }
}
puts $trw_report "SIGNAL_NETS $trw_signal_nets"
puts $trw_report "GUIDE_NETS $trw_guide_nets"
puts $trw_report "WIRE_ONLY_NETS $trw_wire_nets"
puts $trw_report "MISSING_NETS $trw_missing_nets"
puts $trw_report "TRIPWIRE_ROUTE_COVERAGE_END"
close $trw_report
