# Audited extracted checkpoint: route37807978035 / extraction37815131590.
# Single-driver trial from hold screen37806209914; caller verifies provenance.
# Each change requires fresh legalization, routing, antennas and extracted STA.
proc tripwire_size_drop_driver {target} {
    if {$target ne "driver"} {error "Unreviewed dropped-event driver target"}
    set name _38386_
    set old sg13cmos5l_a21oi_1
    set new sg13cmos5l_a21oi_2
    set expected [dict create A1 _12085_ A2 _12163_ B1 _12191_ Y _12192_]
    set inst [[ord::get_db_block] findInst $name]
    set replacement [[ord::get_db] findMaster $new]
    if {$inst eq "NULL" || $replacement eq "NULL"} {
        error "Missing audited dropped-event instance or master"
    }
    if {[[$inst getMaster] getName] ne $old} {
        error "Dropped-event master changed or repair repeated"
    }
    set pins [concat [dict keys $expected] {VDD VSS}]
    set original_pins {}
    foreach term [$inst getITerms] {lappend original_pins [[$term getMTerm] getName]}
    set replacement_pins {}
    foreach term [$replacement getMTerms] {lappend replacement_pins [$term getName]}
    if {[lsort $pins] ne [lsort $original_pins]
            || [lsort $pins] ne [lsort $replacement_pins]} {
        error "Incompatible dropped-event cell pins"
    }
    set nets {}
    foreach pin $pins {
        set net [[$inst findITerm $pin] getNet]
        if {$net eq "NULL"} {error "Disconnected dropped-event pin $pin"}
        if {[dict exists $expected $pin] && [$net getName] ne [dict get $expected $pin]} {
            error "Audited dropped-event connectivity changed"
        }
        dict set nets $pin $net
    }
    replace_cell $name $new
    if {[[$inst getMaster] getName] ne $new} {error "Dropped-event sizing failed"}
    foreach pin $pins {
        if {[[$inst findITerm $pin] getNet] ne [dict get $nets $pin]} {
            error "Dropped-event sizing changed connectivity"
        }
    }
    puts "TRIPWIRE drop-driver sizing: $name $old -> $new; physical qualification required"
}
