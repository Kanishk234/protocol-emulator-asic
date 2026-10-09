# Preflight every target before any mutation. Caller audits prior source history.
proc tripwire_clear_native_signal_routes {} {
    if {[llength [info commands odb::dbWire_destroy]] != 1} {
        error "Pinned OpenDB wire cleanup API missing"
    }
    set saved {}
    foreach net [[ord::get_db_block] getNets] {
        if {[$net getSigType] in {POWER GROUND}} {continue}
        set wire [$net getWire]
        if {$wire ne "NULL"} {lappend saved [list $net $wire]}
    }
    if {![llength $saved]} {error "Expected routed native source; cleanup repeated or wrong source"}
    foreach entry $saved {
        lassign $entry net wire
        odb::dbWire_destroy $wire
        if {[$net getWire] ne "NULL"} {error "Native signal wire cleanup failed"}
    }
    puts "TRIPWIRE native route reset: cleared [llength $saved] ordinary routed wires; power/special routing preserved"
}

proc tripwire_size_native_hold100 {targets} {
    set saved {}
    foreach target $targets {
        lassign $target name old new expected
        set inst [[ord::get_db_block] findInst $name]
        set replacement [[ord::get_db] findMaster $new]
        if {$inst eq "NULL" || $replacement eq "NULL"} {error "Missing native hold100 target/master"}
        if {[[$inst getMaster] getName] ne $old} {error "Native hold100 master changed or repair repeated"}
        set pins [concat [dict keys $expected] {VDD VSS}]
        set actual {}
        foreach term [$inst getITerms] {lappend actual [[$term getMTerm] getName]}
        set next {}
        foreach term [$replacement getMTerms] {lappend next [$term getName]}
        if {[lsort $actual] ne [lsort $pins] || [lsort $next] ne [lsort $pins]} {error "Native hold100 incompatible pins"}
        set nets {}
        foreach pin $pins {
            set net [[$inst findITerm $pin] getNet]
            if {$net eq "NULL"} {error "Native hold100 disconnected pin"}
            if {[dict exists $expected $pin] && [$net getName] ne [dict get $expected $pin]} {
                error "Native hold100 connectivity changed at $name/$pin: expected '[dict get $expected $pin]', actual '[$net getName]'"
            }
            dict set nets $pin $net
        }
        dict set saved $name $nets
    }
    foreach target $targets {
        lassign $target name old new expected
        set inst [[ord::get_db_block] findInst $name]
        replace_cell $name $new
        if {[[$inst getMaster] getName] ne $new} {error "Native hold100 sizing failed"}
        dict for {pin net} [dict get $saved $name] {
            if {[[$inst findITerm $pin] getNet] ne $net} {error "Native hold100 sizing changed nets"}
        }
        puts "TRIPWIRE native hold100 setup: $name $old -> $new; physical qualification required"
    }
}
