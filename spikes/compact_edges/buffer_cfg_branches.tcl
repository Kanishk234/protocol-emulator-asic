# Source after loading a pre-placement ODB. Pure combinational buffers only.
# Split the diagnosed frame-index bits into local per-column decode branches.
set warp_cfg_master [[ord::get_db] findMaster sg13cmos5l_buf_2]
if {$warp_cfg_master == "NULL"} {error "Missing sg13cmos5l_buf_2"}
set warp_cfg_added 0
set warp_cfg_diodes 0
if {[info exists ::env(WARP_CFG_BRANCH_DIODES)] && $::env(WARP_CFG_BRANCH_DIODES)} {
    set warp_diode_master [[ord::get_db] findMaster sg13cmos5l_antennanp]
    if {$warp_diode_master == "NULL"} {error "Missing antenna cell"}
}
foreach bit {0 1} {
    set original NULL
    foreach net [$block getNets] {
        if {[string map {\\ {}} [$net getName]] == "u_cfg.frame_idx\[$bit\]"} {
            set original $net
            break
        }
    }
    if {$original == "NULL"} {error "Missing frame_idx bit $bit"}
    for {set col 0} {$col < 7} {incr col} {
        set loads {}
        foreach term [$original getITerms] {
            if {[[$term getMTerm] getIoType] != "INPUT"} {continue}
            set name [string map {\\ {}} [[$term getInst] getName]]
            if {[regexp {^u_cfg\.g_col\[([0-6])\]\.u_col\.} $name -> idx] && $idx == $col} {
                lappend loads $term
            }
        }
        if {[llength $loads] == 0} {continue}
        set name [format {u_cfg.g_col\[%d\].u_col.WARP_CFG_BRANCH_%d} $col $bit]
        if {[$block findInst $name] != "NULL"} {error "Buffer experiment already applied"}
        set inst [odb::dbInst_create $block $warp_cfg_master $name]
        set branch [odb::dbNet_create $block ${name}_net]
        if {$inst == "NULL" || $branch == "NULL"} {error "Cannot create branch"}
        [$inst findITerm A] connect $original
        [$inst findITerm X] connect $branch
        foreach term [$inst getITerms] {
            set kind [[$term getMTerm] getSigType]
            if {$kind == "POWER" || $kind == "GROUND"} {
                set rail [$block findNet [expr {$kind == "POWER" ? "VPWR" : "VGND"}]]
                if {$rail == "NULL"} {error "Missing supply for added buffer"}
                $term connect $rail
            }
        }
        foreach term $loads {
            $term disconnect
            $term connect $branch
        }
        if {[info exists warp_diode_master]} {
            set diode_name [format {u_cfg.g_col\[%d\].u_col.WARP_CFG_PROTECT_%d} $col $bit]
            if {[$block findInst $diode_name] != "NULL"} {error "Diode experiment already applied"}
            set diode [odb::dbInst_create $block $warp_diode_master $diode_name]
            [$diode findITerm A] connect $original
            foreach term [$diode getITerms] {
                set kind [[$term getMTerm] getSigType]
                if {$kind == "POWER" || $kind == "GROUND"} {
                    set rail [$block findNet [expr {$kind == "POWER" ? "VPWR" : "VGND"}]]
                    if {$rail == "NULL"} {error "Missing diode supply"}
                    $term connect $rail
                }
            }
            incr warp_cfg_diodes
        }
        # Left unplaced for the normal placer; decoder fence membership uses
        # the same column prefix as existing cells. Normal PDN hook-up follows.
        incr warp_cfg_added
        puts "CFG_BRANCH bit=$bit col=$col loads=[llength $loads] master=sg13cmos5l_buf_2"
    }
}
if {$warp_cfg_added == 0} {error "No configuration branches buffered"}
puts "CFG_BRANCH_TOTAL $warp_cfg_added area_um2=[expr {$warp_cfg_added*[$warp_cfg_master getWidth]*[$warp_cfg_master getHeight]/1000000.0}]"
if {$warp_cfg_diodes > 0} {
    puts "CFG_DIODE_TOTAL $warp_cfg_diodes area_um2=[expr {$warp_cfg_diodes*[$warp_diode_master getWidth]*[$warp_diode_master getHeight]/1000000.0}]"
}
