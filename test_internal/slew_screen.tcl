# D-049 diagnostic only: immutable inputs, in-memory cell substitution, no
# placement/routing/output DB. Old wire parasitics do not qualify a new layout.
read_liberty $::env(WARP_SCREEN_STD_LIB)
read_liberty $::env(WARP_SCREEN_IO_LIB)
read_db $::env(WARP_SCREEN_ODB)
read_sdc $::env(WARP_SCREEN_SDC)
set_propagated_clock [all_clocks]
read_spef $::env(WARP_SCREEN_SPEF)
set block [ord::get_db_block]
set target [$block findInst u_cfg._54_]
if {$target eq "NULL"} {error "Missing measured driver"}
set oldmaster [$target getMaster]
if {[$oldmaster getName] ne "sg13cmos5l_a21oi_1"} {error "Unexpected measured driver master"}
set newmaster [[ord::get_db] findMaster sg13cmos5l_a21oi_2]
if {$newmaster eq "NULL"} {error "Missing candidate master"}
proc connections {inst} {
    set result {}
    foreach term [$inst getITerms] {
        set net [$term getNet]
        set name ""
        if {$net ne "NULL"} {set name [$net getName]}
        lappend result [list [[$term getMTerm] getName] [[$term getMTerm] getIoType] $name]
    }
    return [lsort $result]
}
set signature [connections $target]
set out $::env(WARP_SCREEN_OUT)
report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 6 > "$out/baseline_checks.rpt"
report_checks -path_delay min_max -fields {slew capacitance fanout} -digits 6 > "$out/baseline_paths.rpt"
report_parasitic_annotation -report_unannotated > "$out/baseline_annotation.rpt"
if {![$target swapMaster $newmaster]} {error "Diagnostic driver substitution failed"}
if {[connections $target] ne $signature} {error "Driver connectivity changed"}
# Rebind the identical SPEF after swapping; no wire or configuration change.
read_spef $::env(WARP_SCREEN_SPEF)
report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 6 > "$out/candidate_checks.rpt"
report_checks -path_delay min_max -fields {slew capacitance fanout} -digits 6 > "$out/candidate_paths.rpt"
report_parasitic_annotation -report_unannotated > "$out/candidate_annotation.rpt"
puts "WARP_SCREEN complete: same-wire slow-corner diagnostic, macro black-boxed, no physical/timing acceptance"
