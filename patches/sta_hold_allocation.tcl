# WARP D-089: read-only per-delay timing queries in LibreLane's supported STA hook.
# Original corner script, libraries, constraints and placement remain unchanged.
puts "%OL_CREATE_REPORT delay-paths.tsv"
puts "CELL\tMODE\tSTATE\tSLACK_NS\tSTART\tEND"
set warp_delay_count 0
foreach warp_inst [[ord::get_db_block] getInsts] {
    if {[[$warp_inst getMaster] getName] ne "sg13cmos5l_dlygate4sd3_1"} {continue}
    incr warp_delay_count
    set warp_name [$warp_inst getName]
    set warp_pin [get_pins -quiet ${warp_name}/A]
    if {[llength $warp_pin] != 1} {error "Missing unique delay input: $warp_name"}
    foreach warp_mode {min max} {
        set warp_paths [find_timing_paths -through $warp_pin -path_delay $warp_mode -sort_by_slack -group_path_count 1 -endpoint_path_count 1 -corner $corner_name]
        if {[llength $warp_paths] == 0} {
            puts "$warp_name\t$warp_mode\tNO_CONSTRAINED_PATH\tNA\tNA\tNA"
            continue
        }
        set warp_worst [lindex $warp_paths 0]
        foreach warp_path $warp_paths {
            if {[get_property $warp_path slack] < [get_property $warp_worst slack]} {set warp_worst $warp_path}
        }
        set warp_start [get_property [get_property $warp_worst startpoint] full_name]
        set warp_end [get_property [get_property $warp_worst endpoint] full_name]
        puts "$warp_name\t$warp_mode\tCONSTRAINED\t[get_property $warp_worst slack]\t$warp_start\t$warp_end"
    }
}
if {$warp_delay_count != 590} {error "Delay allocation differs: $warp_delay_count"}
puts "%OL_END_REPORT"
