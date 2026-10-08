# Audited extracted checkpoint: route37737970080 / extraction37743628998.
# Call ONE target per physical experiment; caller verifies source provenance.
# Each change requires fresh legalization, routing, antennas and extracted STA.
proc tripwire_size_drop_cell {target} {
    switch -- $target {
        nor2 {
            set name _31567_
            set old sg13cmos5l_nor2_1
            set new sg13cmos5l_nor2_2
            set expected [dict create A _05964_ B _05968_ Y _05970_]
        }
        inv {
            set name _38387_
            set old sg13cmos5l_inv_1
            set new sg13cmos5l_inv_2
            set expected [dict create A _12192_ Y _12193_]
        }
        default {error "Unreviewed dropped-event sizing target"}
    }
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
    puts "TRIPWIRE dropped-event sizing: $name $old -> $new; physical qualification required"
}
