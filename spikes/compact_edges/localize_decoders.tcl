# Apply to a pre-placement ODB produced with deferred hierarchy flattening.
# Uses OpenDB EXCLUSIVE regions (DEF FENCE); no cell is fixed or removed.
# OpenDB types: https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/include/odb/dbTypes.h
read_db $::env(WARP_LOCALIZE_INPUT)
set block [ord::get_db_block]
if {[info exists ::env(WARP_LOCALIZE_RELEASE)] && $::env(WARP_LOCALIZE_RELEASE)} {
    # After placement/CTS, allow antenna diodes and repair buffers to use the
    # remaining sites under each column. Existing cell locations are retained.
    foreach group [$block getGroups] {
        if {[string match warp_decoder_* [$group getName]] ||
            [string match warp_cfgrow_* [$group getName]] ||
            [string match warp_shell_* [$group getName]]} {
            odb::dbGroup_destroy $group
        }
    }
    foreach region [$block getRegions] {
        if {[string match warp_decoder_* [$region getName]] ||
            [string match warp_cfgrow_* [$region getName]] ||
            [string match warp_shell_* [$region getName]]} {
            odb::dbRegion_destroy $region
        }
    }
    write_db $::env(WARP_LOCALIZE_OUTPUT)
    exit
}
set macro [$block findInst u_fabric]
if {$macro == "NULL"} {error "Missing u_fabric"}
lassign [$macro getOrigin] mx my
if {$my < 15120 || $my % 3780 != 0} {error "Expected row-aligned macro y >= 15.12 um"}
set offsets {0 68640 258720 448800 638880 828960 1019040 1120320}
if {[info exists ::env(WARP_CFG_BRANCH_BUFFERS)] && $::env(WARP_CFG_BRANCH_BUFFERS)} {
    source [file join [file dirname [info script]] buffer_cfg_branches.tcl]
}
for {set col 0} {$col < 7} {incr col} {
    set region [odb::dbRegion_create $block warp_decoder_$col]
    $region setRegionType EXCLUSIVE
    odb::dbBox_create $region [expr {$mx + [lindex $offsets $col]}] 3780 \
        [expr {$mx + [lindex $offsets [expr {$col + 1}]]}] $my
    set group [odb::dbGroup_create $block warp_decoder_$col]
    $region addGroup $group
    set count 0
    set area 0
    foreach inst [$block getInsts] {
        set name [string map {\\ {}} [$inst getName]]
        if {[regexp {^u_cfg\.g_col\[([0-6])\]\.u_col\.} $name -> idx] && $idx == $col} {
            $group addInst $inst
            incr count
            set master [$inst getMaster]
            set area [expr {$area + [$master getWidth] * [$master getHeight]}]
        }
    }
    if {$count == 0} {error "No preserved decoder cells in column $col"}
    puts "COLUMN $col: $count decoder cells, area [expr {$area / 1000000.0}] um2"
}
if {[info exists ::env(WARP_LOCALIZE_ROWS)] && $::env(WARP_LOCALIZE_ROWS)} {
    # Real 32-bit row registers next to the west-facing data pins. The driver
    # supplies edge heights from the same manifest used to check the macro.
    set bbox [$macro getBBox]
    set north 37800
    set south 49140
    if {[info exists ::env(WARP_LOCALIZE_NORTH_HEIGHT)]} {set north $::env(WARP_LOCALIZE_NORTH_HEIGHT)}
    if {[info exists ::env(WARP_LOCALIZE_SOUTH_HEIGHT)]} {set south $::env(WARP_LOCALIZE_SOUTH_HEIGHT)}
    set logic 196560
    set total [expr {$north + $south + 3 * $logic}]
    if {[expr {[$bbox yMax] - [$bbox yMin]}] != $total} {
        error "Row regions disagree with macro/manifest heights"
    }
    set bounds [list [expr {$south + 3 * $logic}] $total \
        [expr {$south + 2 * $logic}] [expr {$south + 3 * $logic}] \
        [expr {$south + $logic}] [expr {$south + 2 * $logic}] \
        $south [expr {$south + $logic}] 0 $south]
    for {set row 0} {$row < 5} {incr row} {
        set region [odb::dbRegion_create $block warp_cfgrow_$row]
        $region setRegionType EXCLUSIVE
        set xmin [expr {($row == 0 || $row == 4) ? 2880 : 49920}]
        if {$row > 0 && $row < 4 && [info exists ::env(WARP_LOCALIZE_ROW_WIDTH)]} {
            # The original large fences reserve mostly empty area and crowd
            # the rest of the shell. Isolate a narrower locality experiment.
            set width $::env(WARP_LOCALIZE_ROW_WIDTH)
            if {![string is integer -strict $width] || $width < 15360 || $width > 61440} {
                error "WARP_LOCALIZE_ROW_WIDTH must be 15360..61440 DBU"
            }
            set xmin [expr {$mx - 10080 - $width}]
        }
        odb::dbBox_create $region $xmin [expr {$my + [lindex $bounds [expr {2 * $row}]]}] \
            [expr {$mx - 10080}] [expr {$my + [lindex $bounds [expr {2 * $row + 1}]]}]
        set group [odb::dbGroup_create $block warp_cfgrow_$row]
        $region addGroup $group
        set count 0
        set area 0
        foreach inst [$block getInsts] {
            set name [string map {\\ {}} [$inst getName]]
            if {[regexp {^u_cfg\.g_row\[([0-4])\]\.u_row\.} $name -> idx] && $idx == $row} {
                $group addInst $inst
                incr count
                set master [$inst getMaster]
                set area [expr {$area + [$master getWidth] * [$master getHeight]}]
            }
        }
        if {$count == 0} {error "No row register cells in row $row"}
        puts "ROW $row: $count cells, area [expr {$area / 1000000.0}] um2"
    }
}
if {[info exists ::env(WARP_LOCALIZE_CRC_SPI)] && $::env(WARP_LOCALIZE_CRC_SPI)} {
    # Separate the CRC and SPI logic in the west shell channel. The boxes avoid
    # the x=90.24..111.36 um middle-row register fences and leave a 20 um
    # routing gap between the two blocks. Regions are removed after GPL.
    set dbu [$block getDbUnitsPerMicron]
    set shell_regions {
        crc u_shell.u_crc. 300 480
        spi u_shell.u_spi. 500 640
    }
    if {[info exists ::env(WARP_LOCALIZE_CRC_ONLY)] &&
            $::env(WARP_LOCALIZE_CRC_ONLY)} {
        set shell_regions {crc u_shell.u_crc. 300 480}
    }
    foreach {name prefix ymin ymax} $shell_regions {
        set region [odb::dbRegion_create $block warp_shell_$name]
        set shell_region_type EXCLUSIVE
        if {[info exists ::env(WARP_LOCALIZE_CRC_SPI_GUIDE)] &&
                $::env(WARP_LOCALIZE_CRC_SPI_GUIDE)} {
            set shell_region_type SUGGESTED
        }
        $region setRegionType $shell_region_type
        odb::dbBox_create $region [expr {int(2.88 * $dbu)}] [expr {$ymin * $dbu}] \
            [expr {int(87.36 * $dbu)}] [expr {$ymax * $dbu}]
        set group [odb::dbGroup_create $block warp_shell_$name]
        $region addGroup $group
        set count 0
        set area 0
        foreach inst [$block getInsts] {
            set cell_name [string map {\\ {}} [$inst getName]]
            if {[string first $prefix $cell_name] == 0} {
                $group addInst $inst
                incr count
                set master [$inst getMaster]
                set area [expr {$area + [$master getWidth] * [$master getHeight]}]
            }
        }
        if {$count == 0} {error "No cells found for shell region $name"}
        puts "SHELL $name: $count cells, area [expr {$area / 1000000.0}] um2"
    }
}
write_db $::env(WARP_LOCALIZE_OUTPUT)
