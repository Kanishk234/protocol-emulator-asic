# Preflight every target before any mutation. Caller audits prior source history.
proc tripwire_size_residual_setup {} {
    set targets {
{place6860 sg13cmos5l_buf_1 sg13cmos5l_buf_2 {A _02510_ X net6860}}
{_44061_ sg13cmos5l_a21oi_1 sg13cmos5l_a21oi_2 {A1 _16769_ A2 _16770_ B1 _16773_ Y _16774_}}
{_27962_ sg13cmos5l_nor4_1 sg13cmos5l_nor4_2 {A _02614_ B _02615_ C _02616_ D _02618_ Y _02619_}}
    }
    set saved {}
    foreach target $targets {
        lassign $target name old new expected
        set inst [[ord::get_db_block] findInst $name]
        set replacement [[ord::get_db] findMaster $new]
        if {$inst eq "NULL" || $replacement eq "NULL"} {error "Missing residual target/master"}
        if {[[$inst getMaster] getName] ne $old} {error "Residual master changed or repair repeated"}
        set pins [concat [dict keys $expected] {VDD VSS}]
        set actual {}
        foreach term [$inst getITerms] {lappend actual [[$term getMTerm] getName]}
        set next {}
        foreach term [$replacement getMTerms] {lappend next [$term getName]}
        if {[lsort $actual] ne [lsort $pins] || [lsort $next] ne [lsort $pins]} {error "Residual incompatible pins"}
        set nets {}
        foreach pin $pins {
            set net [[$inst findITerm $pin] getNet]
            if {$net eq "NULL"} {error "Residual disconnected pin"}
            if {[dict exists $expected $pin] && [$net getName] ne [dict get $expected $pin]} {error "Residual connectivity changed"}
            dict set nets $pin $net
        }
        dict set saved $name $nets
    }
    foreach target $targets {
        lassign $target name old new expected
        set inst [[ord::get_db_block] findInst $name]
        replace_cell $name $new
        if {[[$inst getMaster] getName] ne $new} {error "Residual sizing failed"}
        dict for {pin net} [dict get $saved $name] {
            if {[[$inst findITerm $pin] getNet] ne $net} {error "Residual sizing changed nets"}
        }
        puts "TRIPWIRE residual setup: $name $old -> $new; physical qualification required"
    }
}
