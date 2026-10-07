# Read-only isolated library-cell check with the same pinned Magic deck.
gds read $::env(WARP_FILLER_GDS)
gds read "$::env(WARP_FILLER_OUT)/filler_arrays.gds"
drc style drc(full)
foreach cell {sg13cmos5l_fill_1 sg13cmos5l_fill_2 sg13cmos5l_decap_4 sg13cmos5l_decap_8 sg13cmos5l_inv_1 warp_fill1_horizontal warp_fill2_horizontal warp_fill1_rows_same warp_fill2_rows_same warp_fill1_rows_mirrored warp_fill2_rows_mirrored} {
    puts "WARP_CELL $cell"
    load $cell
    select top cell
    drc check
    drc catchup
    set report [open "$::env(WARP_FILLER_OUT)/${cell}.rpt" w]
    puts $report "cell $cell"
    drc count total
    set findings [drc listall why]
    puts $report "has_findings [expr {[llength $findings] > 0}]"
    puts $report $findings
    close $report
}
quit -noprompt
