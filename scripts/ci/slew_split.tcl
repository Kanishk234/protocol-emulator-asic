# Source checkpoint: placement-multicorner 37408506116, before any mutation.
# Same procedure name lets the established wrapper inject after read_current_odb.
proc tripwire_split_critical_branch {} {
    set target $::env(TRIPWIRE_SLEW_TARGET)
    if {$target eq "none"} {puts "TRIPWIRE slew baseline: no connectivity change"; return}
    switch -- $target {
        lane {
            set driver_name _33713_
            set net_name _07896_
            set loads {_34060_/B _34059_/B _33936_/B place7396/A place7402/A}
            set xy {298.56 287.28}
        }
        sram {
            set driver_name _30323_
            set net_name _04725_
            set loads {_30324_/A2}
            set xy {852.0 192.78}
        }
        default {error "Unknown slew split target $target"}
    }
    set block [ord::get_db_block]
    set net [$block findNet $net_name]
    set driver [$block findInst $driver_name]
    if {$net eq "NULL" || $driver eq "NULL"} {error "Missing audited slew source"}
    if {[[$driver getMaster] getName] ne "sg13cmos5l_nor4_1"} {error "Wrong slew driver master"}
    set actual {}
    foreach pin [$net getITerms] {
        lappend actual "[[$pin getInst] getName]/[[$pin getMTerm] getName]"
    }
    if {[lsort $actual] ne [lsort [concat [list $driver_name/Y] $loads]] || [llength [$net getBTerms]]} {
        error "Audited slew connectivity changed: $actual"
    }
    set master [[ord::get_db] findMaster sg13cmos5l_buf_4]
    if {$master eq "NULL"} {error "Missing pinned BUF4"}
    set inst_name tripwire_slew_${target}_buf
    set new_net_name tripwire_slew_${target}_net
    if {[$block findInst $inst_name] ne "NULL" || [$block findNet $new_net_name] ne "NULL"} {
        error "Duplicate slew split"
    }
    set rails {}
    foreach name {VDD VSS} {
        set rail [[$driver findITerm $name] getNet]
        if {$rail eq "NULL"} {error "Disconnected driver supply"}
        lappend rails $rail
    }
    set buffer [odb::dbInst_create $block $master $inst_name]
    set downstream [odb::dbNet_create $block $new_net_name]
    [$buffer findITerm A] connect $net
    [$buffer findITerm X] connect $downstream
    foreach load $loads {
        lassign [split $load /] name pin_name
        set pin [[$block findInst $name] findITerm $pin_name]
        $pin disconnect
        $pin connect $downstream
    }
    foreach name {VDD VSS} rail $rails {[$buffer findITerm $name] connect $rail}
    set units [$block getDbUnitsPerMicron]
    lassign $xy x y
    $buffer setLocation [expr {int(round($x * $units))}] [expr {int(round($y * $units))}]
    $buffer setPlacementStatus PLACED
    puts "TRIPWIRE slew split: $target $net_name -> BUF4 -> $loads at $xy"
}
