# Read-only floorplan/cell/pin audit from a preserved OpenDB snapshot.
# WARP_AUDIT_ODB and WARP_AUDIT_GEOMETRY (fresh TSV) are required.
if {[file exists $::env(WARP_AUDIT_GEOMETRY)]} {error "Audit output exists"}
read_db $::env(WARP_AUDIT_ODB)
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set out [open $::env(WARP_AUDIT_GEOMETRY) w]
puts $out [join [list DBU $dbu] "\t"]
set core [$block getCoreArea]
puts $out [join [list CORE [$core xMin] [$core yMin] [$core xMax] [$core yMax]] "\t"]
foreach row [$block getRows] {
    lassign [$row getOrigin] x y
    set site [$row getSite]
    set x2 [expr {$x + ([$row getSiteCount]-1)*[$row getSpacing] + [$site getWidth]}]
    puts $out [join [list ROW [$row getName] $x $y $x2 [expr {$y+[$site getHeight]}]] "\t"]
}
foreach inst [$block getInsts] {
    set master [$inst getMaster]
    set box [$inst getBBox]
    puts $out [join [list CELL [$inst getName] [$master getName] [$master isBlock] \
        [$box xMin] [$box yMin] [$box xMax] [$box yMax] [$inst getPlacementStatus]] "\t"]
    if {[$master isBlock]} {continue}
    foreach term [$inst getITerms] {
        set net [$term getNet]
        if {$net == "NULL" || [$net getSigType] == "POWER" || [$net getSigType] == "GROUND"} {continue}
        foreach geometry [$term getGeometries] {
            lassign $geometry layer rect
            puts $out [join [list PIN [$inst getName] [[$term getMTerm] getName] [$net getName] \
                [$layer getName] [$rect xMin] [$rect yMin] [$rect xMax] [$rect yMax]] "\t"]
        }
    }
}
close $out
puts "Geometry exported; database unchanged"
