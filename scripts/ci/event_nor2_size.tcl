# Exact original event-late125ps checkpoint only. Caller validates provenance.
# Caller must subsequently legalize, reroute and repeat all-corner signoff.
proc tripwire_size_event_nor2 {} {
    set inst [[ord::get_db_block] findInst _27853_]
    set replacement [[ord::get_db] findMaster sg13cmos5l_nor2_2]
    if {$inst eq "NULL" || $replacement eq "NULL"} {
        error "Missing audited NOR2 instance or replacement master"
    }
    if {[[$inst getMaster] getName] ne "sg13cmos5l_nor2_1"} {
        error "Audited NOR2 master changed or repair repeated"
    }
    set expected [dict create A _21095_ B _02509_ Y _02510_]
    set pins {}
    foreach term [$inst getITerms] {
        lappend pins [[$term getMTerm] getName]
    }
    if {[lsort $pins] ne [lsort {A B Y VDD VSS}]} {
        error "Unexpected audited NOR2 pins"
    }
    set replacement_pins {}
    foreach term [$replacement getMTerms] {
        lappend replacement_pins [$term getName]
    }
    if {[lsort $replacement_pins] ne [lsort $pins]} {
        error "Replacement NOR2 pins are incompatible"
    }
    set nets {}
    foreach pin {A B Y VDD VSS} {
        set net [[$inst findITerm $pin] getNet]
        if {$net eq "NULL"} {error "Disconnected audited NOR2 pin $pin"}
        if {[dict exists $expected $pin] && [$net getName] ne [dict get $expected $pin]} {
            error "Audited NOR2 connectivity changed at $pin"
        }
        dict set nets $pin $net
    }
    replace_cell _27853_ sg13cmos5l_nor2_2
    if {[[$inst getMaster] getName] ne "sg13cmos5l_nor2_2"} {
        error "NOR2 replacement did not update physical master"
    }
    foreach pin {A B Y VDD VSS} {
        if {[[$inst findITerm $pin] getNet] ne [dict get $nets $pin]} {
            error "NOR2 replacement changed connectivity at $pin"
        }
    }
    puts "TRIPWIRE event NOR2: _27853_ strength1->2; legalization/routing/signoff required"
}
