# Couple electrical repair to antenna cleanup in the live GRT process.
# The existing two-batch/64-BUF4 limit, protected-pin rules and final gates stay.
proc tripwire_margin_sources {iteration} {
    estimate_parasitics -global_routing
    set failing {}
    set corners [lln::get_corner_dict]
    if {[lsort [dict keys $corners]] ne [lsort {nom_fast_1p32V_m40C nom_slow_1p08V_125C nom_typ_1p20V_25C}]} {error "Inline margin requires all three pinned corners"}
    foreach {corner object} $corners {
        set path $::env(STEP_DIR)/postant_margin_${iteration}_${corner}.rpt
        set f [open $path w];puts $f "TRIPWIRE_MARGIN_BEGIN $corner";close $f
        set count 0
        foreach net [get_nets -hierarchical *] {
            set name [get_full_name $net]
            set f [open $path a];puts $f "TRIPWIRE_NET_HEX [binary encode hex $name]";close $f
            report_check_types -max_slew -max_capacitance -net $net -corner $corner \
                -format end -digits 6 -no_line_splits >> $path
            incr count
        }
        set f [open $path a];puts $f "TRIPWIRE_MARGIN_END $corner $count";close $f
        set f [open $path r];set text [read $f];close $f
        set current {};set kind {}
        foreach line [split $text \n] {
            if {[regexp {^TRIPWIRE_NET_HEX (\S+)$} $line -> hex]} {
                set current [encoding convertfrom utf-8 [binary decode hex $hex]]
                set kind {}
            }
            if {[regexp {^max (slew|capacitance)$} [string trim $line] -> measured]} {set kind $measured}
            if {$current ne {} && $kind ne {} && [regexp {^\S+\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)(?:\s|$)} [string trim $line] -> limit actual]} {
                if {![string is double -strict $limit] || ![string is double -strict $actual] || $limit<0 || $actual<0} {error "Invalid inline margin measurement"}
                if {($limit==0 && $actual>0) || ($limit>0 && $actual/$limit>0.45)} {dict set failing $current 1}
            }
        }
    }
    puts "TRIPWIRE inline electrical margin: iteration $iteration found [dict size $failing] nets above 0.45"
    return $failing
}

rename tripwire_post_antenna_groups tripwire_post_antenna_fanout_groups
proc tripwire_post_antenna_groups {iteration} {
    set margin_sources [tripwire_margin_sources $iteration]
    return [tripwire_post_antenna_fanout_groups $iteration $margin_sources]
}
