# Controlled R4 physical experiment: split the measured long _19783_ branch.
# Apply only after reading the saved pre-route ODB, before legalization/GRT.
proc tripwire_split_critical_branch {} {
    set block [ord::get_db_block]
    set net [$block findNet _19783_]
    if {$net eq "NULL"} {error "Missing audited branch _19783_"}
    set expected [lsort {_25365_/Y _25366_/B1 rebuffer5871/A}]
    set actual {}
    foreach pin [$net getITerms] {
        lappend actual "[[$pin getInst] getName]/[[$pin getMTerm] getName]"
    }
    if {[lsort $actual] ne $expected || [llength [$net getBTerms]]} {
        error "Audited branch connectivity changed: $actual"
    }
    set driver [$block findInst _25365_]
    if {[[$driver getMaster] getName] ne "sg13cmos5l_o21ai_1"} {
        error "Audited branch driver changed"
    }
    set master [[ord::get_db] findMaster sg13cmos5l_buf_4]
    if {$master eq "NULL"} {error "Missing pinned BUF4 master"}
    if {[$block findInst tripwire_branch_buf] ne "NULL" ||
        [$block findNet tripwire_branch_net] ne "NULL"} {
        error "Refusing duplicate branch repair"
    }
    set rails {}
    foreach name {VDD VSS} {
        set rail [[$driver findITerm $name] getNet]
        if {$rail eq "NULL"} {error "Driver power pin $name is disconnected"}
        lappend rails $rail
    }
    set inst [odb::dbInst_create $block $master tripwire_branch_buf]
    set downstream [odb::dbNet_create $block tripwire_branch_net]
    [$inst findITerm A] connect $net
    [$inst findITerm X] connect $downstream
    foreach inst_name {_25366_ rebuffer5871} pin_name {B1 A} {
        set pin [[$block findInst $inst_name] findITerm $pin_name]
        $pin disconnect
        $pin connect $downstream
    }
    foreach name {VDD VSS} rail $rails {[$inst findITerm $name] connect $rail}
    set units [$block getDbUnitsPerMicron]
    # Midpoint of the measured 201.12 -> 925.92 um branch; DPL legalizes it.
    $inst setLocation [expr {int(round(563.52 * $units))}] [expr {int(round(570.78 * $units))}]
    $inst setPlacementStatus PLACED
    puts "TRIPWIRE critical branch: _19783_ -> BUF4 -> {_25366_/B1 rebuffer5871/A}, initial location {563.52 570.78}"
}
