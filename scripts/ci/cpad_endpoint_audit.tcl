# Expand reports without editing the design, parasitics or constraints.
if {![info exists corner_name]} {error "Missing current corner"}
foreach endpoint {_48106_ _48079_ _46963_ _48094_ _48293_} {
    set target [get_pins "$endpoint/D"]
    if {[llength $target] != 1} {error "Missing exact endpoint $endpoint"}
    foreach delay {min max} {
        puts "%OL_CREATE_REPORT cpad_${endpoint}_${delay}.rpt"
        report_checks -to $target -path_delay $delay -group_path_count 12 \
            -endpoint_path_count 12 -format full_clock_expanded \
            -fields {slew cap input net fanout} -digits 6 -corner $corner_name
        puts "%OL_END_REPORT"
    }
}

# Actual functional path margins supplement, never replace, all-endpoint gates.
source [file join [file dirname [info script]] functional_setup_frontier.tcl]
