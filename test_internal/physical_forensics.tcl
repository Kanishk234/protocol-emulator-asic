# Read-only geometry inventory of the authenticated iteration52 database.
# This snapshot still has3 routing markers; it is not the final zero-DRC ODB.
read_db $::env(WARP_FORENSIC_ODB)
set block [ord::get_db_block]
set units [$block getDbUnitsPerMicron]
set out $::env(WARP_FORENSIC_OUT)
file mkdir $out
proc box_values {box units} {
    return [list [expr {[$box xMin]/double($units)}] [expr {[$box yMin]/double($units)}] \
                 [expr {[$box xMax]/double($units)}] [expr {[$box yMax]/double($units)}]]
}
set rows [open "$out/rows.tsv" w]
puts $rows "name\torient\tsite\txmin\tymin\txmax\tymax"
foreach row [$block getRows] {
    puts $rows [join [concat [list [$row getName] [$row getOrient] [[$row getSite] getName]] \
                           [box_values [$row getBBox] $units]] "\t"]
}
close $rows
set cells [open "$out/cells.tsv" w]
puts $cells "instance\tmaster\torient\torigin_x\torigin_y\txmin\tymin\txmax\tymax"
set pins [open "$out/metal1_pins.tsv" w]
puts $pins "instance\tmaster\tpin\tnet\txmin_local\tymin_local\txmax_local\tymax_local"
foreach inst [$block getInsts] {
    set master [$inst getMaster]
    lassign [$inst getOrigin] x y
    puts $cells [join [concat [list [$inst getName] [$master getName] [$inst getOrient] \
                                   [expr {$x/double($units)}] [expr {$y/double($units)}]] \
                                   [box_values [$inst getBBox] $units]] "\t"]
    foreach term [$inst getITerms] {
        set mterm [$term getMTerm]
        set net [$term getNet]
        set net_name "UNCONNECTED"
        if {$net ne "NULL"} {set net_name [$net getName]}
        foreach mpin [$mterm getMPins] {
            foreach shape [$mpin getGeometry] {
                if {[$shape isVia]} {continue}
                set layer [$shape getTechLayer]
                if {[$layer getName] ne "Metal1"} {continue}
                puts $pins [join [concat [list [$inst getName] [$master getName] [$mterm getName] $net_name] \
                                      [box_values $shape $units]] "\t"]
            }
        }
    }
}
close $cells
close $pins
set rails [open "$out/metal1_special.tsv" w]
puts $rails "net\txmin\tymin\txmax\tymax"
foreach net [$block getNets] {
    foreach wire [$net getSWires] {
        foreach shape [$wire getWires] {
            if {[$shape isVia]} {continue}
            if {[[$shape getTechLayer] getName] ne "Metal1"} {continue}
            puts $rails [join [concat [list [$net getName]] [box_values $shape $units]] "\t"]
        }
    }
}
close $rails
puts "Read-only physical inventory complete; no database write or routing performed."
