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
        set net [$block findNet $net_name]
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
        set source [$block findNet $source_name]
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
