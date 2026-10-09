# Caller must validate route37954320974 NL/DEF hashes before loading its ODB.
# Independent REN move only; do not combine with DOUT0 relocation.
# Physical routing and all-corner timing must qualify this prototype.
proc tripwire_relocate_sram_ren {} {
    set block [ord::get_db_block]
    set inst [$block findInst _29426_]
    if {$inst eq "NULL"} {error "Missing SRAM REN driver"}
    if {[[$inst getMaster] getName] ne "sg13cmos5l_nor2b_1" || [$inst isFixed]} {
        error "Wrong or fixed SRAM REN driver"
    }
    set before [$inst getBBox]
    if {[$before xMin] != 438720 || [$before yMin] != 226800 ||
        [$before xMax] - [$before xMin] != 2400 ||
        [$before yMax] - [$before yMin] != 3780 || [$inst getOrient] ne "MX"} {
        error "Wrong SRAM REN driver placement or repeated relocation"
    }
    set expected [dict create A _04439_ B_N _04440_ Y _00076_]
    set pins {}
    set nets {}
    foreach term [$inst getITerms] {
        set pin [[$term getMTerm] getName]
        lappend pins $pin
        set net [$term getNet]
        if {$net eq "NULL"} {error "Disconnected SRAM REN driver pin"}
        if {[dict exists $expected $pin] && [$net getName] ne [dict get $expected $pin]} {
            error "Wrong SRAM REN driver net"
        }
        dict set nets $pin $net
    }
    if {[lsort $pins] ne [lsort {A B_N Y VDD VSS}]} {error "Wrong SRAM REN pins"}
    # Row64 candidate from pinned DEF/LEF occupancy audit; units are nm.
    set x 123840
    set y 245700
    foreach other [$block getInsts] {
        if {$other eq $inst} {continue}
        set box [$other getBBox]
        if {[$box xMin] < $x + 2400 && [$box xMax] > $x &&
            [$box yMin] < $y + 3780 && [$box yMax] > $y} {
            error "SRAM relocation site is occupied"
        }
    }
    # Orient first: OpenDB setLocation uses lower-left DEF coordinates.
    $inst setOrient R0
    $inst setLocation $x $y
    set after [$inst getBBox]
    if {[$after xMin] != $x || [$after yMin] != $y || [$inst getOrient] ne "R0" ||
        [[$inst getMaster] getName] ne "sg13cmos5l_nor2b_1"} {
        error "SRAM relocation failed"
    }
    dict for {pin net} $nets {
        if {[[$inst findITerm $pin] getNet] ne $net} {error "SRAM relocation changed nets"}
    }
    set ::tripwire_sram_ren_relocation_nets $nets
    puts "TRIPWIRE SRAM REN relocation: _29426_ 438720,226800,MX -> 123840,245700,R0; unchanged master/nets; physical qualification required"
}

proc tripwire_verify_sram_ren {} {
    if {![info exists ::tripwire_sram_ren_relocation_nets]} {error "No prior SRAM relocation"}
    set inst [[ord::get_db_block] findInst _29426_]
    set box [$inst getBBox]
    if {[[$inst getMaster] getName] ne "sg13cmos5l_nor2b_1" ||
        [$box xMin] != 123840 || [$box yMin] != 245700 || [$inst getOrient] ne "R0"} {
        error "Legalization moved SRAM REN driver away from audited site"
    }
    dict for {pin net} $::tripwire_sram_ren_relocation_nets {
        if {[[$inst findITerm $pin] getNet] ne $net} {error "Legalization changed SRAM nets"}
    }
    puts "TRIPWIRE SRAM REN relocation: exact site/master/nets retained after legalization"
}
