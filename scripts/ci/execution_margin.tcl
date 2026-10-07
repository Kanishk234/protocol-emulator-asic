# Source after linking the full chip, loading constraints and parasitics.
# Reporting only: preserve global checks and all configuration-latch paths.
proc tripwire_report_execution_margin {} {
    set flop_d [all_registers -edge_triggered -data_pins]
    set latch_d [all_registers -level_sensitive -data_pins]
    set outputs [all_outputs]
    if {![llength $flop_d] || ![llength $latch_d] || ![llength $outputs]} {
        error "Execution-margin audit requires full-chip flop, latch and output endpoints"
    }
    puts "TRIPWIRE GLOBAL SETUP"
    report_checks -path_delay max -group_count 5 -digits 6
    puts "TRIPWIRE GLOBAL HOLD"
    report_checks -path_delay min -group_count 5 -digits 6
    puts "TRIPWIRE FLOP SETUP: [llength $flop_d] endpoints"
    report_checks -path_delay max -to $flop_d -group_count 5 -digits 6
    puts "TRIPWIRE LATCH SETUP: [llength $latch_d] endpoints"
    report_checks -path_delay max -to $latch_d -group_count 5 -digits 6
    puts "TRIPWIRE OUTPUT SETUP: [llength $outputs] endpoints"
    report_checks -path_delay max -to $outputs -group_count 5 -digits 6
}

# Select flops by their preserved output-net names, not mapping cell numbers.
# Keep the global/flop/latch/output reports above alongside these cone reports.
proc tripwire_report_residual_cones {} {
    set rx_d {}
    set dropped_d {}
    foreach pin [all_registers -edge_triggered -data_pins] {
        # Pinned IHP mapped flops use D; exclude reset/control pins.
        if {![regexp {/D$} [get_full_name $pin]]} {continue}
        set cells [get_cells -of_objects $pin]
        foreach output [get_pins -of_objects $cells -filter {direction == output}] {
            foreach net [get_nets -of_objects $output] {
                set name [get_full_name $net]
                if {[regexp {\.u_rx\.rt\[[0-9]+\]$} $name]} {
                    lappend rx_d $pin
                }
                if {[regexp {\.dropped\[[0-9]+\]$} $name]} {
                    lappend dropped_d $pin
                }
            }
        }
    }
    set rx_d [lsort -unique $rx_d]
    set dropped_d [lsort -unique $dropped_d]
    set sram_addr [get_pins -regexp {^u_chip\.u_sram\.sram/A_ADDR\[[0-9]+\]$}]
    if {![llength $rx_d] || ![llength $dropped_d] || ![llength $sram_addr]} {
        error "Residual-cone audit requires RX timers, dropped counters and SRAM address pins"
    }
    foreach label {RX_TIMER DROPPED_COUNTER SRAM_ADDRESS} endpoints [list $rx_d $dropped_d $sram_addr] {
        puts "TRIPWIRE $label SETUP: [llength $endpoints] endpoints"
        report_checks -path_delay max -to $endpoints -group_count 5 -digits 6
        puts "TRIPWIRE $label HOLD: [llength $endpoints] endpoints"
        report_checks -path_delay min -to $endpoints -group_count 5 -digits 6
    }
}
