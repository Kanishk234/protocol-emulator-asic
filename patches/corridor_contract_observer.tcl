# WARP read-only OpenDB facts for a future corridor-model contract.
# Source after an authenticated loaded/routed checkpoint. This does not expose
# live FastRoute costs, raw edge arrays, or detailed via feasibility.
if {![info exists ::env(WARP_CORRIDOR_DIR)] ||
    ![file isdirectory $::env(WARP_CORRIDOR_DIR)]} {
    error "WARP_CORRIDOR_DIR must name a preexisting writable artifact directory"
}
set warp_corridor_block [ord::get_db_block]
if {$warp_corridor_block eq "NULL"} {error "No OpenDB block for corridor observation"}
set warp_corridor_grid [$warp_corridor_block getGCellGrid]
if {$warp_corridor_grid eq "NULL"} {error "No native reporting grid"}
set warp_corridor_macro [$warp_corridor_block findInst u_fabric]
if {$warp_corridor_macro eq "NULL" || [$warp_corridor_macro getOrient] ne "R0"} {
    error "Expected R0 fabric macro missing"
}
proc warp_corridor_row {stream values} {
    foreach value $values {
        if {[regexp {[\t\r\n]} $value]} {error "Unrepresentable corridor TSV field"}
    }
    puts $stream [join $values "\t"]
}
proc warp_corridor_rect {stream prefix rect} {
    warp_corridor_row $stream [concat $prefix [list [$rect xMin] [$rect yMin] [$rect xMax] [$rect yMax]]]
}
set warp_corridor_facts [open $::env(WARP_CORRIDOR_DIR)/odb-facts.tsv {WRONLY CREAT EXCL}]
warp_corridor_row $warp_corridor_facts [list SCOPE OpenDB_only_not_live_FastRoute]
warp_corridor_row $warp_corridor_facts [list DBU [$warp_corridor_block getDbUnitsPerMicron]]
warp_corridor_row $warp_corridor_facts [list GRID_X [join [$warp_corridor_grid getGridX] { }]]
warp_corridor_row $warp_corridor_facts [list GRID_Y [join [$warp_corridor_grid getGridY] { }]]
warp_corridor_row $warp_corridor_facts [list VIA_FEASIBILITY NOT_EXPORTED]
warp_corridor_rect $warp_corridor_facts [list DIE] [$warp_corridor_block getDieArea]
foreach warp_corridor_layer [[[ord::get_db] getTech] getLayers] {
    if {[$warp_corridor_layer getRoutingLevel] > 0} {
        warp_corridor_row $warp_corridor_facts [list LAYER [$warp_corridor_layer getName] [$warp_corridor_layer getRoutingLevel] [$warp_corridor_layer getDirection]]
    }
}
foreach warp_corridor_net [$warp_corridor_block getNets] {
    set warp_corridor_ndr [$warp_corridor_net getNonDefaultRule]
    set warp_corridor_ndr_name NULL
    if {$warp_corridor_ndr ne "NULL"} {set warp_corridor_ndr_name [$warp_corridor_ndr getName]}
    warp_corridor_row $warp_corridor_facts [list NET [$warp_corridor_net getName] [$warp_corridor_net getSigType] [$warp_corridor_net isSpecial] [$warp_corridor_net getTermCount] $warp_corridor_ndr_name]
}
foreach warp_corridor_inst [$warp_corridor_block getInsts] {
    warp_corridor_row $warp_corridor_facts [list INST [$warp_corridor_inst getName] [[$warp_corridor_inst getMaster] getName] [$warp_corridor_inst getOrigin] [$warp_corridor_inst getOrient]]
    foreach warp_corridor_term [$warp_corridor_inst getITerms] {
        set warp_corridor_net [$warp_corridor_term getNet]
        if {$warp_corridor_net eq "NULL"} {continue}
        foreach warp_corridor_shape [$warp_corridor_term getGeometries] {
            lassign $warp_corridor_shape warp_corridor_layer warp_corridor_rect
            warp_corridor_rect $warp_corridor_facts [list PIN [$warp_corridor_inst getName] [[$warp_corridor_term getMTerm] getName] [$warp_corridor_net getName] [$warp_corridor_layer getName]] $warp_corridor_rect
        }
    }
}
foreach warp_corridor_term [$warp_corridor_block getBTerms] {
    set warp_corridor_net [$warp_corridor_term getNet]
    if {$warp_corridor_net eq "NULL"} {continue}
    foreach warp_corridor_pin [$warp_corridor_term getBPins] {
        foreach warp_corridor_box [$warp_corridor_pin getBoxes] {
            warp_corridor_rect $warp_corridor_facts [list BOUNDARY [$warp_corridor_term getName] [$warp_corridor_net getName] [[$warp_corridor_box getTechLayer] getName]] $warp_corridor_box
        }
    }
}
foreach warp_corridor_box [[$warp_corridor_macro getMaster] getObstructions] {
    warp_corridor_rect $warp_corridor_facts [list MACRO_OBS_LOCAL [[$warp_corridor_box getTechLayer] getName]] $warp_corridor_box
}
foreach warp_corridor_obs [$warp_corridor_block getObstructions] {
    set warp_corridor_box [$warp_corridor_obs getBBox]
    warp_corridor_rect $warp_corridor_facts [list BLOCK_OBS [[$warp_corridor_box getTechLayer] getName]] $warp_corridor_box
}
close $warp_corridor_facts
puts "WARP_CORRIDOR_ODB_FACTS_COMPLETE"
