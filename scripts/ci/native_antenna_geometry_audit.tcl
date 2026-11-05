# Read-only native route readback and four-net antenna reports.
source [file join [file dirname [info script]] native_hold_frontier_audit.tcl]
write_global_route_segments [file join $::env(STEP_DIR) checkpoint_segments.txt]
foreach trw_net {_10511_ _19518_ net11878 net12579} {
    if {[[ord::get_db_block] findNet $trw_net] == "NULL"} {error "Missing traced net $trw_net"}
    check_antennas -net $trw_net -verbose -report_file [file join $::env(STEP_DIR) antenna_${trw_net}.rpt]
}
