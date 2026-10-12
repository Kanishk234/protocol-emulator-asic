# WARP D-088: alternate engine, unchanged physical capacity and placement.
lappend arg_list -use_cugr
# WARP D-087 read-only observer. Preserve the router's original error status.
set warp_route_code [catch {log_cmd global_route {*}$arg_list} warp_route_message warp_route_options]
set warp_grid [[ord::get_db_block] getGCellGrid]
if {$warp_grid eq "NULL"} {error "No native congestion grid"}
set warp_x [$warp_grid getGridX]
set warp_y [$warp_grid getGridY]
if {[llength $warp_x] < 2 || [llength $warp_y] < 2} {error "Invalid native grid coordinates"}
set warp_grid_file [open $::env(STEP_DIR)/native-grid.tsv w]
puts $warp_grid_file "META\t[llength $warp_x]\t[llength $warp_y]"
puts $warp_grid_file "X\t[join $warp_x { }]"
puts $warp_grid_file "Y\t[join $warp_y { }]"
foreach warp_layer [[[ord::get_db] getTech] getLayers] {
    set warp_level [$warp_layer getRoutingLevel]
    if {$warp_level < 1 || $warp_level > 4} {continue}
    for {set warp_ix 0} {$warp_ix < [llength $warp_x]-1} {incr warp_ix} {
        for {set warp_iy 0} {$warp_iy < [llength $warp_y]-1} {incr warp_iy} {
            puts $warp_grid_file "CELL\t[$warp_layer getName]\t$warp_ix\t$warp_iy\t[$warp_grid getCapacity $warp_layer $warp_ix $warp_iy]\t[$warp_grid getUsage $warp_layer $warp_ix $warp_iy]"
        }
    }
}
close $warp_grid_file
set warp_guides_file [open $::env(STEP_DIR)/native-guides.tsv w]
foreach warp_net [[ord::get_db_block] getNets] {
    if {[$warp_net getSigType] eq "POWER" || [$warp_net getSigType] eq "GROUND"} {continue}
    puts $warp_guides_file "NET\t[$warp_net getName]\t[$warp_net getTermCount]\t[llength [$warp_net getGuides]]\t[$warp_net isConnectedByAbutment]"
}
close $warp_guides_file
if {$warp_route_code != 0} {return -options $warp_route_options $warp_route_message}
