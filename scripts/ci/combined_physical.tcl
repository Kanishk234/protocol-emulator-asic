# Exact generated proposal preflights all identities/connectivity before sizing.
proc tripwire_place_combined {name master location} {
    set allowed [dict create place7221 sg13cmos5l_buf_2 _24876_ sg13cmos5l_inv_2 _30202_ sg13cmos5l_nor3_2 _37732_ sg13cmos5l_nand2_2 _29918_ sg13cmos5l_nor3_2 hold12828 sg13cmos5l_dlygate4sd1_1 _24812_ sg13cmos5l_inv_2 _25926_ sg13cmos5l_and4_2]
    set inst [[ord::get_db_block] findInst $name]
    if {![dict exists $allowed $name] || [dict get $allowed $name] ne $master || $inst eq "NULL" || [[$inst getMaster] getName] ne $master} {
        error "Unreviewed combined resize placement"
    }
    lassign $location x y orient
    if {[llength $location]!=3 || $orient ni {N FS} || ![string is integer -strict $x] || ![string is integer -strict $y] || $x<0 || $y<0} {error "Invalid combined resize location"}
    if {$orient eq "N"} {$inst setOrient R0} else {$inst setOrient MX}
    $inst setLocation $x $y
    $inst setPlacementStatus PLACED
}
