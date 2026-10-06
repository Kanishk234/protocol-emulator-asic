# D-045: one-cell pin-geometry experiment from a saved pre-GRT database.
# Outputs must be fresh; no existing run or generated/upstream RTL is edited.
foreach key {WARP_SIZE_INPUT WARP_SIZE_OUTPUT WARP_SIZE_DEF WARP_SIZE_REPORT WARP_SIZE_LIB} {
    if {![info exists ::env($key)]} {error "Missing $key"}
}
foreach key {WARP_SIZE_OUTPUT WARP_SIZE_DEF WARP_SIZE_REPORT} {
    if {[file exists $::env($key)]} {error "Refusing to overwrite $::env($key)"}
}
# dbSta's swap callback needs Liberty cells even when this is a geometry-only
# screen. A bare read_db followed by swapMaster crashes the pinned OpenROAD.
read_liberty $::env(WARP_SIZE_LIB)
read_db $::env(WARP_SIZE_INPUT)
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set name u_shell._1073_
set target [$block findInst $name]
if {$target eq "NULL" || [$target isFixed]} {error "Missing/movable target $name"}
set oldmaster [$target getMaster]
if {[$oldmaster getName] ne "sg13cmos5l_nor3_1"} {error "Unexpected target master"}
set newmaster [[ord::get_db] findMaster sg13cmos5l_nor3_2]
if {$newmaster eq "NULL"} {error "PDK has no larger NOR3 master"}
proc ports {master} {
    set result {}
    foreach term [$master getMTerms] {
        lappend result [list [$term getName] [$term getIoType] [$term getSigType]]
    }
    return [lsort $result]
}
if {[ports $oldmaster] ne [ports $newmaster]} {error "Master port contract differs"}
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
        lappend result [list [$inst getName] [lsort $pins]]
    }
    return [lsort $result]
}
set before [signature $block]
set original {}
foreach inst [$block getInsts] {
    dict set original [$inst getName] [list [$inst getOrigin] [$inst getOrient] \
        [$inst getPlacementStatus] [[$inst getMaster] getName]]
}
set mode legalize
if {[info exists ::env(WARP_SIZE_MODE)]} {set mode $::env(WARP_SIZE_MODE)}
if {$mode ni {legalize slide_right}} {error "Unknown placement mode"}
set box [$target getBBox]
set target_old_right [$box xMax]
set target_ymin [$box yMin]
set target_ymax [$box yMax]
set halo_um 20
if {[info exists ::env(WARP_SIZE_HALO)]} {set halo_um $::env(WARP_SIZE_HALO)}
if {![string is double -strict $halo_um] || $halo_um <= 0} {error "Invalid local halo"}
set halo [expr {$halo_um*$dbu}]
set xmin [expr {[$box xMin]-$halo}]
set xmax [expr {[$box xMax]+$halo}]
set ymin [expr {[$box yMin]-$halo}]
set ymax [expr {[$box yMax]+$halo}]
set anchored {}
foreach inst [$block getInsts] {
    if {$mode eq "slide_right"} {break}
    if {[$inst isFixed]} {continue}
    set box [$inst getBBox]
    if {[$box xMax] < $xmin || [$box xMin] > $xmax ||
        [$box yMax] < $ymin || [$box yMin] > $ymax} {
        dict set anchored [$inst getName] [$inst getPlacementStatus]
        $inst setPlacementStatus FIRM
    }
}
set added_area [expr {([$newmaster getWidth]*double([$newmaster getHeight]) - \
    [$oldmaster getWidth]*double([$oldmaster getHeight]))/($dbu*double($dbu))}]
if {![$target swapMaster $newmaster]} {error "Master swap failed"}
if {$mode eq "legalize"} {
    detailed_placement -max_displacement {20 20} -report_file_name $::env(WARP_SIZE_REPORT)
} else {
    # Minimal same-row compaction: shift only successive overlapping cells
    # right until existing whitespace absorbs the added width. No row/order/
    # orientation change or remote legalization. check_placement is mandatory.
    set following {}
    foreach inst [$block getInsts] {
        if {$inst eq $target} {continue}
        set b [$inst getBBox]
        if {[$b yMin] == $target_ymin && [$b yMax] == $target_ymax &&
            [$b xMin] >= $target_old_right} {
            lappend following [list [$b xMin] $inst]
        }
    }
    set end [[$target getBBox] xMax]
    foreach item [lsort -integer -index 0 $following] {
        lassign $item left inst
        if {$left >= $end} {break}
        if {[$inst isFixed]} {error "Cannot shift a fixed row neighbor"}
        set dx [expr {$end-$left}]
        if {$dx > 20*$dbu} {error "Excessive row shift"}
        lassign [$inst getOrigin] ox oy
        $inst setOrigin [expr {$ox+$dx}] $oy
        set end [[$inst getBBox] xMax]
    }
}
check_placement -verbose
if {$mode eq "slide_right"} {
    set report [open $::env(WARP_SIZE_REPORT) w]
    puts $report {{"method": "slide_right", "check_placement": "pass"}}
    close $report
}
if {[signature $block] ne $before} {error "Resize changed net connectivity"}
set moved 0
set maxdist 0
foreach inst [$block getInsts] {
    set instname [$inst getName]
    lassign [dict get $original $instname] oldxy oldorient oldstatus oldcell
    set expected $oldcell
    if {$instname eq $name} {set expected sg13cmos5l_nor3_2}
    if {[[$inst getMaster] getName] ne $expected} {error "Unexpected master change: $instname"}
    if {$oldxy eq [$inst getOrigin] && $oldorient eq [$inst getOrient]} {continue}
    if {$oldstatus in {LOCKED FIRM} || [dict exists $anchored $instname]} {
        error "Anchored/fixed instance moved: $instname"
    }
    lassign $oldxy ox oy
    lassign [$inst getOrigin] nx ny
    set dist [expr {(abs($nx-$ox)+abs($ny-$oy))/double($dbu)}]
    set maxdist [expr {max($dist,$maxdist)}]
    incr moved
    puts "SIZE_MOVED\t$instname\t$dist"
}
dict for {instname status} $anchored {[$block findInst $instname] setPlacementStatus $status}
puts "SIZE_SUMMARY\t$name\tsg13cmos5l_nor3_1->sg13cmos5l_nor3_2\tmode=$mode\tadded_area_um2=$added_area\thalo_um=$halo_um\tanchored=[dict size $anchored]\tmoved=$moved\tmax_manhattan_um=$maxdist\tconnectivity=unchanged"
write_db $::env(WARP_SIZE_OUTPUT)
write_def $::env(WARP_SIZE_DEF)
