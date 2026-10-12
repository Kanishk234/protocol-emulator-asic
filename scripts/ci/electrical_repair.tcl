# Normalize only bracket escapes. Refuse ambiguous canonical aliases; compare
# actual source connections by net object, and preserve those objects on resize.
proc tripwire_electrical_net_name {name} {
    return [string map [list [format %c%c 92 91] [format %c 91] [format %c%c 92 93] [format %c 93]] $name]
}
proc tripwire_electrical_find_net {block name} {
    set wanted [tripwire_electrical_net_name $name]
    set matches {}
    foreach net [$block getNets] {
        if {[tripwire_electrical_net_name [$net getName]] eq $wanted} {lappend matches $net}
    }
    if {[llength $matches] != 1} {error "Missing or ambiguous electrical source net: $name"}
    return [lindex $matches 0]
}

proc tripwire_size_electrical {targets} {
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
            if {[dict exists $expected $pin] && $net ne [tripwire_electrical_find_net [ord::get_db_block] [dict get $expected $pin]]} {
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
        puts "TRIPWIRE electrical sizing: $name $old -> $new; physical qualification required"
    }
}

# Exact NL/DEF and canonical-plan audit must precede this binding. Preflight all
# groups before mutation. Caller must legalize, clear old signal wires, reroute,
# check topology, antennas and fresh allcorner setup/hold. Only buffer inputs may be moved on the reviewed clock branches; no leaf clock/reset pins.
proc tripwire_electrical_repair {master_name expectations groups} {
    set block [ord::get_db_block]
    set master [[ord::get_db] findMaster $master_name]
    if {$master eq "NULL"} {error "Missing residual buffer master"}
    set master_pins {}
    foreach term [$master getMTerms] {lappend master_pins [$term getName]}
    if {[lsort $master_pins] ne {A VDD VSS X}} {error "Wrong identity buffer pins"}
    foreach expected $expectations {
        lassign $expected net_name pins masters
        set net [tripwire_electrical_find_net $block $net_name]
        if {$net eq "NULL" || [llength [$net getBTerms]]} {error "Missing or exposed residual source net"}
        set actual {}
        foreach term [$net getITerms] {
            lappend actual "[[$term getInst] getName]/[[$term getMTerm] getName]"
        }
        if {[lsort $actual] ne [lsort $pins]} {error "Residual source net connectivity changed"}
        foreach pair $masters {
            lassign $pair name old
            set inst [$block findInst $name]
            if {$inst eq "NULL" || [[$inst getMaster] getName] ne $old} {error "Residual master changed"}
        }
    }
    set saved {}
    foreach group $groups {
        lassign $group buffer_name net_name source_name rail_name location sinks
        if {[$block findInst $buffer_name] ne "NULL" || [$block findNet $net_name] ne "NULL"} {error "Repeated residual repair"}
        if {[llength $location] != 3 || [lindex $location 2] ni {N FS}} {error "Invalid repair placement"}
        set source [tripwire_electrical_find_net $block $source_name]
        set rail_inst [$block findInst $rail_name]
        set rails {}
        foreach pin {VDD VSS} {
            set term [$rail_inst findITerm $pin]
            if {$term eq "NULL" || [$term getNet] eq "NULL"} {error "Disconnected residual power"}
            lappend rails [$term getNet]
        }
        set terms {}
        foreach sink $sinks {
            lassign $sink name pin
            if {$pin in {CLK GCLK GATE RESET_B}} {error "Residual repair must not move clock/reset pins"}
            set term [[$block findInst $name] findITerm $pin]
            if {$term eq "NULL" || [$term getNet] ne $source} {error "Residual sink changed"}
            lappend terms $term
        }
        lappend saved [list $buffer_name $net_name $source $rails $location $terms]
    }
    foreach group $saved {
        lassign $group buffer_name net_name source rails location terms
        set buffer [odb::dbInst_create $block $master $buffer_name]
        set downstream [odb::dbNet_create $block $net_name]
        $downstream setSigType [$source getSigType]
        [$buffer findITerm A] connect $source
        [$buffer findITerm X] connect $downstream
        foreach term $terms {$term disconnect; $term connect $downstream}
        foreach pin {VDD VSS} rail $rails {[$buffer findITerm $pin] connect $rail}
        lassign $location x y orient
        if {$orient eq "N"} {$buffer setOrient R0} elseif {$orient eq "FS"} {$buffer setOrient MX} else {error "Invalid repair orientation"}
        $buffer setLocation $x $y
        $buffer setPlacementStatus PLACED
        puts "TRIPWIRE electrical repair: $buffer_name $master_name; moved [llength $terms] sink pins; all prior cells retained"
    }
}

proc tripwire_place_electrical_resize {name master location} {
    set inst [[ord::get_db_block] findInst $name]
    if {$name ne "_25245_" || $master ne "sg13cmos5l_nor4_2" || $inst eq "NULL" || [[$inst getMaster] getName] ne $master} {
        error "Unreviewed electrical resize placement"
    }
    lassign $location x y orient
    if {[llength $location] != 3 || $orient ni {N FS}} {error "Invalid resize location"}
    if {$orient eq "N"} {$inst setOrient R0} else {$inst setOrient MX}
    $inst setLocation $x $y
    $inst setPlacementStatus PLACED
}
