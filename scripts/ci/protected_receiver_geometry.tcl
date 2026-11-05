# Read-only native geometry and per-net antenna evidence for preserved receivers.
write_global_route_segments [file join $::env(STEP_DIR) receiver_segments.txt]
foreach trw_inst [[ord::get_db_block] getInsts] {
    if {[string match *.trw_receiver_sink [$trw_inst getName]]} {
        set trw_net [[$trw_inst findITerm A] getNet]
        set trw_name [$trw_net getName]
        set trw_hex [binary encode hex [$trw_inst getName]]
        check_antennas -net $trw_name -verbose -report_file [file join $::env(STEP_DIR) receiver_${trw_hex}.rpt]
    }
}
