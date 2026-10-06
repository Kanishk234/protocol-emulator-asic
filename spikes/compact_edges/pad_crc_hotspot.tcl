# D-043: isolated post-CTS placement screen; never run on an active run's ODB.
# Give only endpoints of the measured CRC/net37 conflict extra routing space.
foreach key {WARP_PAD_OUTPUT WARP_PAD_DEF WARP_PAD_REPORT} {
    if {[file exists $::env($key)]} {error "Refusing to overwrite $::env($key)"}
}
read_db $::env(WARP_PAD_INPUT)
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set selected {}
foreach name {net37 {u_shell.crc[2]}} {
    set found 0
    foreach net [$block getNets] {
        if {[string map {\\ ""} [$net getName]] ne $name} {continue}
        set found 1
        foreach term [$net getITerms] {
            set inst [$term getInst]
            if {[[$inst getMaster] isBlock] || [$inst isFixed]} {
                error "Unexpected fixed/macro endpoint: [$inst getName]"
            }
            dict set selected [$inst getName] $inst
        }
    }
    if {!$found} {error "Missing measured hotspot net: $name"}
}
if {[dict size $selected] != 12} {
    error "Expected the baseline's 12 CRC endpoints, found [dict size $selected]"
}

# Placement must preserve every instance/master and net connection.
proc signature {block} {
    set result {}
    foreach inst [$block getInsts] {
        set pins {}
        foreach term [$inst getITerms] {
            set net [$term getNet]
            set netname ""
            if {$net ne "NULL"} {set netname [$net getName]}
            lappend pins [list [[$term getMTerm] getName] $netname]
        }
        lappend result [list [$inst getName] [[$inst getMaster] getName] [lsort $pins]]
    }
    return [lsort $result]
}
set before [signature $block]
set locations {}
foreach inst [$block getInsts] {
    dict set locations [$inst getName] [list [$inst getOrigin] [$inst getOrient]]
}
# The pinned legalizer has no incremental flag. Temporarily anchor remote
# cells so re-legalization does not shift unrelated shell/configuration rows.
set xmin 1e30
set ymin 1e30
set xmax -1e30
set ymax -1e30
foreach inst [dict values $selected] {
    set box [$inst getBBox]
    set xmin [expr {min($xmin, [$box xMin])}]
    set ymin [expr {min($ymin, [$box yMin])}]
    set xmax [expr {max($xmax, [$box xMax])}]
    set ymax [expr {max($ymax, [$box yMax])}]
}
set halo [expr {20*$dbu}]
set anchored {}
foreach inst [$block getInsts] {
    if {[$inst isFixed]} {continue}
    set box [$inst getBBox]
    if {[$box xMax] < $xmin-$halo || [$box xMin] > $xmax+$halo ||
        [$box yMax] < $ymin-$halo || [$box yMin] > $ymax+$halo} {
        dict set anchored [$inst getName] [$inst getPlacementStatus]
        $inst setPlacementStatus FIRM
    }
}
puts "PAD_ANCHORED\t[dict size $anchored]"
foreach name [lsort [dict keys $selected]] {puts "PAD_ENDPOINT\t$name"}
set pad_sites 2
if {[info exists ::env(WARP_PAD_SITES)]} {set pad_sites $::env(WARP_PAD_SITES)}
if {![string is integer -strict $pad_sites] || $pad_sites < 1} {
    error "WARP_PAD_SITES must be a positive site count"
}
set_placement_padding -instances [dict keys $selected] -left $pad_sites -right $pad_sites
detailed_placement -max_displacement {20 20} -report_file_name $::env(WARP_PAD_REPORT)
check_placement -verbose
if {[signature $block] ne $before} {error "Placement changed logical connectivity"}
set moved 0
set maxdist 0
foreach inst [$block getInsts] {
    set name [$inst getName]
    lassign [dict get $locations $name] oldxy oldorient
    lassign $oldxy ox oy
    lassign [$inst getOrigin] nx ny
    if {$oldxy eq [$inst getOrigin] && $oldorient eq [$inst getOrient]} {continue}
    if {[$inst isFixed]} {error "Fixed instance moved: $name"}
    incr moved
    set dist [expr {(abs($nx-$ox)+abs($ny-$oy))/double($dbu)}]
    set maxdist [expr {max($maxdist,$dist)}]
    puts "MOVED\t$name\t$dist"
}
puts "PAD_SUMMARY\tselected=[dict size $selected]\tsites_per_side=$pad_sites\tmoved=$moved\tmax_manhattan_um=$maxdist\tconnectivity=unchanged"
dict for {name status} $anchored {[$block findInst $name] setPlacementStatus $status}
write_db $::env(WARP_PAD_OUTPUT)
write_def $::env(WARP_PAD_DEF)
