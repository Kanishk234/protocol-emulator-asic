# Read-only isolated library-cell check with the same pinned Magic deck.
gds read $::env(WARP_FILLER_GDS)
drc style drc(full)
foreach cell {sg13cmos5l_fill_1 sg13cmos5l_fill_2 sg13cmos5l_decap_4 sg13cmos5l_decap_8 sg13cmos5l_inv_1} {
    load $cell
    select top cell
    drc check
    drc catchup
    set report [open "$::env(WARP_FILLER_OUT)/${cell}.rpt" w]
    puts $report "cell $cell"
    puts $report "count [drc count total]"
    puts $report [drc listall why]
    close $report
}
quit -noprompt
