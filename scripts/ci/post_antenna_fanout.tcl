# Bounded identity buffering after native antenna repair, in the initialized
# global-router process. No clock/reset/exposed nets or functional cells change.
proc tripwire_json_string {value} {
    set safe [tripwire_electrical_net_name $value]
    if {![regexp {^[A-Za-z0-9_./\[\]-]+$} $safe]} {error "Unsafe post-antenna identity"}
    return "\"$safe\""
}

proc tripwire_post_antenna_groups {iteration} {
    set block [ord::get_db_block]
    set groups {}
    foreach net [$block getNets] {
        if {[$net getSigType] in {POWER GROUND CLOCK}} {continue}
        set drivers {};set sinks {};set protected 0
        foreach term [$net getITerms] {
            set pin [[$term getMTerm] getName]
            if {$pin in {CLK GCLK GATE RESET_B}} {set protected 1}
            if {$pin in {X Y Q}} {lappend drivers $term} else {lappend sinks $term}
        }
        if {$protected || [llength [$net getBTerms]]} {continue}
        if {[llength $sinks]<=8} {continue}
        if {[llength $sinks]>32} {error "Post-antenna source exceeds bounded fanout tree"}
        if {[llength $drivers]!=1} {error "Ambiguous overloaded post-antenna data net"}
        set driver [lindex $drivers 0];set anchor [$driver getInst]
        if {![string match sg13cmos5l_* [[$anchor getMaster] getName]]} {error "Post-antenna driver is not a standard cell"}
        set ordered {}
        foreach term $sinks {
            set inst [$term getInst]
            lassign [$inst getLocation] x y
            lappend ordered [list $x $y [$inst getName] [[$term getMTerm] getName] $term]
        }
        set ordered [lsort -integer -index 0 $ordered]
        for {set start 0} {$start<[llength $ordered]} {incr start 4} {
            set selected [lrange $ordered $start [expr {$start+3}]]
            set name tripwire_postant_${iteration}_[llength $groups]
            lappend groups [list $name ${name}_net $net $anchor $selected]
        }
    }
    if {[llength $groups]>32} {error "Post-antenna buffer budget exceeded"}
    return $groups
}

proc tripwire_post_antenna_apply {groups receipt} {
    set block [ord::get_db_block];set master [[ord::get_db] findMaster sg13cmos5l_buf_4]
    if {$master eq "NULL"} {error "Missing post-antenna BUF4"}
    set master_pins {}
    foreach term [$master getMTerms] {lappend master_pins [$term getName]}
    if {[lsort $master_pins] ne {A VDD VSS X}} {error "Wrong post-antenna identity pins"}
    # Preflight the complete batch before the first mutation.
    foreach g $groups {
        lassign $g name newnet source anchor selected
        foreach value [list $name $newnet [$source getName]] {tripwire_json_string $value}
        if {[$block findInst $name] ne "NULL" || [$block findNet $newnet] ne "NULL" || [llength $selected]<1 || [llength $selected]>4} {error "Repeated or invalid post-antenna group"}
        foreach pin {VDD VSS} {
            set term [$anchor findITerm $pin]
            if {$term eq "NULL" || [$term getNet] eq "NULL"} {error "Missing post-antenna power anchor"}
        }
        foreach sink $selected {
            lassign $sink x y inst pin term
            tripwire_json_string $inst;tripwire_json_string $pin
            if {$pin in {CLK GCLK GATE RESET_B} || [$term getNet] ne $source} {error "Changed or protected post-antenna sink"}
        }
    }
    set json_groups {}
    foreach g $groups {
        lassign $g name newnet source anchor selected
        set buffer [odb::dbInst_create $block $master $name]
        set downstream [odb::dbNet_create $block $newnet];$downstream setSigType SIGNAL
        [$buffer findITerm A] connect $source;[$buffer findITerm X] connect $downstream
        foreach pin {VDD VSS} {[$buffer findITerm $pin] connect [[$anchor findITerm $pin] getNet]}
        $buffer setOrient [$anchor getOrient];lassign [$anchor getLocation] x y
        $buffer setLocation $x $y;$buffer setPlacementStatus PLACED
        set json_sinks {}
        foreach sink $selected {
            lassign $sink x y inst pin term
            $term disconnect;$term connect $downstream
            lappend json_sinks "\[[tripwire_json_string $inst],[tripwire_json_string $pin]\]"
        }
        lappend json_groups "{\"buffer\":[tripwire_json_string $name],\"net\":[tripwire_json_string $newnet],\"source_net\":[tripwire_json_string [$source getName]],\"master\":\"sg13cmos5l_buf_4\",\"sinks\":\[[join $json_sinks ,]\]}"
    }
    set f [open $receipt w];puts $f "{\"groups\":\[[join $json_groups ,]\]}";close $f
}

proc tripwire_post_antenna_finish {antenna_args} {
    for {set iteration 0} {$iteration<3} {incr iteration} {
        set groups [tripwire_post_antenna_groups $iteration]
        if {![llength $groups]} {puts "TRIPWIRE post-antenna fanout: converged after $iteration batches";return}
        # Iterations0/1 may mutate at most32 cells each. Iteration2 is a check.
        if {$iteration==2} {error "Post-antenna fanout did not converge within two batches"}
        set prefix $::env(STEP_DIR)/postant_$iteration
        write_verilog ${prefix}.before.nl.v
        set saved [tripwire_freeze_existing_placement]
        global_route -start_incremental
        tripwire_post_antenna_apply $groups ${prefix}.json
        source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
        tripwire_restore_placement_status $saved
        global_route -end_incremental -verbose
        write_verilog ${prefix}.after.nl.v
        log_cmd repair_antennas {*}$antenna_args
        puts "TRIPWIRE post-antenna fanout: batch $iteration added [llength $groups] BUF4 cells"
    }
}
