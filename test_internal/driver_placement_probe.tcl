# Scratch placement preflight only. Existing routes/parasitics become invalid.
read_liberty $::env(WARP_SCREEN_STD_LIB)
read_liberty $::env(WARP_SCREEN_IO_LIB)
read_db $::env(WARP_SCREEN_ODB)
set block [ord::get_db_block]
set out $::env(WARP_SCREEN_OUT)
# Pinned check_placement_cmd is void; illegal placement raises DPL-0033.
# Comparing its empty successful return with numeric zero falsely fails.
check_placement -verbose -report_file_name "$out/baseline_placement.json"
proc normalized {name} {return [string map {\\ ""} $name]}
proc find_unique {block name} {
    set found {}
    foreach inst [$block getInsts] {
        if {[normalized [$inst getName]] eq $name} {lappend found $inst}
    }
    if {[llength $found] != 1} {error "Missing/ambiguous instance $name"}
    return [lindex $found 0]
}
proc connectivity {block} {
    set result {}
    foreach inst [$block getInsts] {
        if {[string match sg13cmos5l_fill_* [[$inst getMaster] getName]]} {continue}
        set pins {}
        foreach term [$inst getITerms] {
            set net [$term getNet]
            set name "UNCONNECTED"
            if {$net ne "NULL"} {set name [$net getName]}
            lappend pins [list [[$term getMTerm] getName] $name]
        }
        lappend result [list [$inst getName] [lsort $pins]]
    }
    return [lsort $result]
}
set signature [connectivity $block]
set original {}
foreach inst [$block getInsts] {
    if {[string match sg13cmos5l_fill_* [[$inst getMaster] getName]]} {continue}
    dict set original [$inst getName] [list [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient]]
}
set driver [find_unique $block {u_cfg._54_}]
if {[[$driver getMaster] getName] ne "sg13cmos5l_a21oi_1"} {error "Unexpected driver"}
set stronger [[ord::get_db] findMaster sg13cmos5l_a21oi_2]
if {$stronger eq "NULL"} {error "Missing stronger driver"}
# Free existing filler space; do not remove any logic/tap/antenna cells.
remove_fillers
if {![$driver swapMaster $stronger]} {error "Driver substitution failed"}
# Three cells shift left exactly three sites; wider driver keeps right edge.
set allowed {}
foreach {name oldx newx} {
    u_cfg._54_ 46080 44640
    u_cfg._72_ 44160 42720
    {u_cfg.g_row[4].u_row._124__468} 42240 40800
} {
    set inst [find_unique $block $name]
    if {[$inst getLocation] ne [list $oldx 52920]} {error "Unexpected source location for $name"}
    $inst setLocation $newx 52920
    lappend allowed [$inst getName]
}
if {[connectivity $block] ne $signature} {error "Logical/power connectivity changed"}
foreach inst [$block getInsts] {
    set name [$inst getName]
    if {![dict exists $original $name]} {error "Unexpected added non-filler instance"}
    set before [dict get $original $name]
    set after [list [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient]]
    if {$name ni $allowed && $before ne $after} {error "Unexpected placement/master change $name"}
    if {[lindex $before 2] ne [$inst getOrient]} {error "Orientation changed $name"}
    if {$inst ne $driver && [lindex $before 0] ne [[$inst getMaster] getName]} {error "Unexpected master change $name"}
}
check_placement -verbose -report_file_name "$out/candidate_placement.json"
write_db "$out/placement_only.odb"
write_def "$out/placement_only.def"
set channel [open "$out/placement_result.json" w]
puts $channel {{"placement_legal":true,"changed_logic_masters":1,"moved_logic_cells":3,"shift_um":1.44,"added_cell_area_um2":5.4432,"connectivity_unchanged":true,"routes_validated":false,"timing_validated":false,"physical_acceptance":false}}
close $channel
puts "WARP_PLACEMENT legal three-cell placement only; routes and parasitics invalid; no acceptance"
