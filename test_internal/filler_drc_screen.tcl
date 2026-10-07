# Read-only isolated library-cell check with the same pinned Magic deck.
gds noduplicates true
gds readonly true
gds maskhints $::env(WARP_FILLER_MASKHINTS)
gds read $::env(WARP_FILLER_GDS)
gds read "$::env(WARP_FILLER_OUT)/filler_arrays.gds"
drc euclidean on
drc style drc(full)
set cells {sg13cmos5l_fill_1 sg13cmos5l_fill_2 sg13cmos5l_fill_4 sg13cmos5l_fill_8 sg13cmos5l_decap_4 sg13cmos5l_decap_8 sg13cmos5l_inv_1}
foreach width {1 2 4 8} {
    foreach fixture {horizontal rows_mirrored rows_ground} {
        lappend cells warp_fill${width}_${fixture}
    }
}
lappend cells warp_fill1_rows_same warp_fill2_rows_same
lappend cells warp_fill2_ground_gap005 warp_fill2_ground_gap030 warp_fill2_ground_gap300
foreach cell $cells {
    puts "WARP_CELL $cell"
    load $cell
    select top cell
    drc check
    drc catchup
    set report [open "$::env(WARP_FILLER_OUT)/${cell}.rpt" w]
    puts $report "cell $cell"
    drc count total
    set findings [drc listall why]
    set count 0
    foreach {reason boxes} $findings {
        incr count [llength $boxes]
    }
    puts $report "count $count"
    puts $report "has_findings [expr {[llength $findings] > 0}]"
    puts $report $findings
    close $report
}
quit -noprompt
