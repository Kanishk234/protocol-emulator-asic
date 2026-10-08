# Exact source: successful drop-event screen37803300460; caller checks provenance.
# Preflight ALL nine leaves before insertion. Fresh legalization/routing/STA required.
proc tripwire_delay_drop_leaves {} {
    set inventory {
        {_46568_ _00384_ _34844_ sg13cmos5l_inv_1}
        {_46523_ _00339_ _34677_ sg13cmos5l_a21oi_1}
        {_46565_ _00381_ _34838_ sg13cmos5l_inv_1}
        {_47657_ _01449_ _42488_ sg13cmos5l_nor3_1}
        {_48411_ _00010_ _28711_ sg13cmos5l_nor4_1}
        {_46522_ _00338_ _34661_ sg13cmos5l_a21oi_1}
        {_47656_ _01448_ _42482_ sg13cmos5l_nor2_1}
        {_47559_ _01351_ _42037_ sg13cmos5l_a21oi_1}
        {_46519_ _00335_ _34611_ sg13cmos5l_a21oi_1}
    }
    set block [ord::get_db_block]
    set master [[ord::get_db] findMaster sg13cmos5l_buf_1]
    if {$master eq "NULL"} {error "Missing pinned drop-hold BUF1"}
    set pins {}
    foreach pin [$master getMTerms] {lappend pins [$pin getName]}
    if {[lsort $pins] ne [lsort {A X VDD VSS}]} {error "Incompatible drop-hold buffer pins"}
    set units [$block getDbUnitsPerMicron]
    if {$units <= 0} {error "Invalid drop-hold placement units"}
    set checked {}
    foreach row $inventory {
        lassign $row sink_name net_name driver_name driver_master
        set sink [$block findInst $sink_name]
        set driver [$block findInst $driver_name]
        set net [$block findNet $net_name]
        if {$sink eq "NULL" || $driver eq "NULL" || $net eq "NULL"} {error "Missing drop-hold branch"}
        if {[[$sink getMaster] getName] ne "sg13cmos5l_dfrbpq_1"
                || [[$driver getMaster] getName] ne $driver_master} {error "Drop-hold masters changed"}
        set actual {}
        foreach pin [$net getITerms] {
            lappend actual "[[$pin getInst] getName]/[[$pin getMTerm] getName]"
        }
        if {[lsort $actual] ne [lsort [list "$driver_name/Y" "$sink_name/D"]]
                || [llength [$net getBTerms]]} {error "Drop-hold connectivity changed"}
        set input [$sink findITerm D]
        set output [$driver findITerm Y]
        if {$input eq "NULL" || $output eq "NULL"
                || [$input getNet] ne $net || [$output getNet] ne $net} {error "Drop-hold data pins changed"}
        set buffer_name "tripwire_drop_hold_buf$sink_name"
        set downstream_name "tripwire_drop_hold_net$sink_name"
        if {[$block findInst $buffer_name] ne "NULL" || [$block findNet $downstream_name] ne "NULL"} {
            error "Duplicate drop-hold insertion"
        }
        set rails {}
        foreach name {VDD VSS} {
            set dpin [$driver findITerm $name]
            set spin [$sink findITerm $name]
            if {$dpin eq "NULL" || $spin eq "NULL"} {error "Missing drop-hold supply pin"}
            set rail [$spin getNet]
            if {$rail eq "NULL" || [$dpin getNet] ne $rail} {error "Inconsistent drop-hold supplies"}
            lappend rails $rail
        }
        lassign [$sink getLocation] x y
        lappend checked [list $sink_name $net $input $output $buffer_name $downstream_name $rails $x $y]
    }
    foreach row $checked {
        lassign $row sink_name net input output buffer_name downstream_name rails x y
        set buffer [odb::dbInst_create $block $master $buffer_name]
        set downstream [odb::dbNet_create $block $downstream_name]
        if {$buffer eq "NULL" || $downstream eq "NULL"} {error "Drop-hold creation failed"}
        [$buffer findITerm A] connect $net
        [$buffer findITerm X] connect $downstream
        $input disconnect
        $input connect $downstream
        foreach name {VDD VSS} rail $rails {[$buffer findITerm $name] connect $rail}
        $buffer setLocation [expr {max(0, $x - 2 * $units)}] $y
        $buffer setPlacementStatus PLACED
        if {[$input getNet] ne $downstream || [$output getNet] ne $net} {error "Drop-hold reconnection failed"}
    }
    puts "TRIPWIRE drop-leaf hold: exactly9 BUF1 data leaves; fresh physical validation required"
}
