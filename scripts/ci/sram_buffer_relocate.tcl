# Caller must validate route37954320974 NL/DEF hashes before loading its ODB.
# One existing buffer moved; no sizing, buffering, or diode deletion here.
proc tripwire_relocate_sram_output0 {} {
    set block [ord::get_db_block]
    set inst [$block findInst wire9447]
    if {$inst eq "NULL"} {error "Missing SRAM output buffer"}
    if {[[$inst getMaster] getName] ne "sg13cmos5l_buf_4" || [$inst isFixed]} {
        error "Wrong or fixed SRAM output buffer"
    }
    set before [$inst getBBox]
    if {[$before xMin] != 473760 || [$before yMin] != 230580 ||
        [$before xMax] - [$before xMin] != 3840 ||
        [$before yMax] - [$before yMin] != 3780 || [$inst getOrient] ne "R0"} {
        error "Wrong SRAM output buffer placement or repeated relocation"
    }
    set expected [dict create A {u_chip.g_lane\[0\].u_lane.mem_rdata\[0\]} X net9447]
    set pins {}
    set nets {}
    foreach term [$inst getITerms] {
        set pin [[$term getMTerm] getName]
        lappend pins $pin
        set net [$term getNet]
        if {$net eq "NULL"} {error "Disconnected SRAM output buffer pin"}
        if {[dict exists $expected $pin] && [$net getName] ne [dict get $expected $pin]} {
            error "Wrong SRAM output buffer net"
        }
        dict set nets $pin $net
    }
    if {[lsort $pins] ne [lsort {A X VDD VSS}]} {error "Wrong SRAM buffer pins"}
    # Row65 candidate from pinned DEF/LEF occupancy audit; units are nm.
    set x 20640
    set y 249480
    foreach other [$block getInsts] {
        if {$other eq $inst} {continue}
        set box [$other getBBox]
        if {[$box xMin] < $x + 3840 && [$box xMax] > $x &&
            [$box yMin] < $y + 3780 && [$box yMax] > $y} {
            error "SRAM relocation site is occupied"
        }
    }
    # Orient first: OpenDB setLocation uses lower-left DEF coordinates.
    $inst setOrient MX
    $inst setLocation $x $y
    set after [$inst getBBox]
    if {[$after xMin] != $x || [$after yMin] != $y || [$inst getOrient] ne "MX" ||
        [[$inst getMaster] getName] ne "sg13cmos5l_buf_4"} {
        error "SRAM relocation failed"
    }
    dict for {pin net} $nets {
        if {[[$inst findITerm $pin] getNet] ne $net} {error "SRAM relocation changed nets"}
    }
    set ::tripwire_sram_relocation_nets $nets
    puts "TRIPWIRE SRAM relocation: wire9447 473760,230580,R0 -> 20640,249480,MX; unchanged master/nets; physical qualification required"
}

proc tripwire_verify_sram_output0 {} {
    if {![info exists ::tripwire_sram_relocation_nets]} {error "No prior SRAM relocation"}
    set inst [[ord::get_db_block] findInst wire9447]
    set box [$inst getBBox]
    if {[[$inst getMaster] getName] ne "sg13cmos5l_buf_4" ||
        [$box xMin] != 20640 || [$box yMin] != 249480 || [$inst getOrient] ne "MX"} {
        error "Legalization moved SRAM buffer away from audited site"
    }
    dict for {pin net} $::tripwire_sram_relocation_nets {
        if {[[$inst findITerm $pin] getNet] ne $net} {error "Legalization changed SRAM nets"}
    }
    puts "TRIPWIRE SRAM relocation: exact site/master/nets retained after legalization"
}
