# Read-only geometry, clock and path probes on the C-selector checkpoint.
source [file join [file dirname [info script]] native_hold_frontier_audit.tcl]
write_global_route_segments [file join $::env(STEP_DIR) checkpoint_segments.txt]
set trw_block [ord::get_db_block]
set trw_targets [list _02001_ {u_chip.g_lane[1].ot[26]} \
    {clknet_2_0__leaf_u_chip.g_unit[0].u_cfg.g_word[0].g_stored.gclk} net14386]
puts "%OL_CREATE_REPORT antenna_target_connections.rpt"
set trw_index 0
foreach trw_name $trw_targets {
    set trw_net [$trw_block findNet $trw_name]
    if {$trw_net == "NULL"} {error "Missing reviewed antenna net: $trw_name"}
    puts "NET $trw_name TYPE [$trw_net getSigType]"
    foreach trw_term [$trw_net getITerms] {
        set trw_inst [$trw_term getInst]
        set trw_mterm [$trw_term getMTerm]
        puts "PIN [$trw_inst getName]/[$trw_mterm getName] DIRECTION [$trw_mterm getIoType] MASTER [[$trw_inst getMaster] getName] LOCATION [$trw_inst getLocation] ORIENT [$trw_inst getOrient]"
    }
}
puts "%OL_END_REPORT"
foreach trw_name $trw_targets {
    check_antennas -net $trw_name -verbose -report_file \
        [file join $::env(STEP_DIR) antenna_target_${trw_index}.rpt]
    incr trw_index
}

# Include the clock tree in both directions around the affected latch.
puts "%OL_CREATE_REPORT affected_latch_min.rpt"
report_checks -path_delay min -to [get_pins _51789_/D] \
    -format full_clock_expanded -digits 6 -group_path_count 20
puts "%OL_END_REPORT"
puts "%OL_CREATE_REPORT affected_latch_max.rpt"
report_checks -path_delay max -from [get_pins _51789_/Q] \
    -format full_clock_expanded -digits 6 -group_path_count 20
puts "%OL_END_REPORT"

# Track the functional source/endpoint of the previous extracted setup failure.
# Resolve cells by named Q nets rather than reusing old synthesized cell IDs.
proc trw_output_term {block name} {
    set net [$block findNet $name]
    if {$net == "NULL"} {error "Missing tracked Q net: $name"}
    set drivers {}
    foreach term [$net getITerms] {
        if {[[$term getMTerm] getIoType] == "OUTPUT"} {lappend drivers $term}
    }
    if {[llength $drivers] != 1} {error "Expected one driver for tracked Q net: $name"}
    return [lindex $drivers 0]
}
set trw_launch [trw_output_term $trw_block {u_chip.g_unit[0].bitsync_active}]
set trw_capture [trw_output_term $trw_block {u_chip.u_fab.u_c0.pending_drop}]
set trw_launch_pin [[ $trw_launch getInst] getName]/[[$trw_launch getMTerm] getName]
set trw_capture_inst [$trw_capture getInst]
if {[$trw_capture_inst findITerm D] == "NULL"} {error "Tracked capture has no D pin"}
set trw_capture_pin [$trw_capture_inst getName]/D
puts "%OL_CREATE_REPORT tracked_config_to_drop.rpt"
puts "TRACKED_FROM $trw_launch_pin TRACKED_TO $trw_capture_pin"
report_checks -path_delay max -from [get_pins $trw_launch_pin] \
    -to [get_pins $trw_capture_pin] -format full_clock_expanded -digits 6 -group_path_count 20
puts "%OL_END_REPORT"
