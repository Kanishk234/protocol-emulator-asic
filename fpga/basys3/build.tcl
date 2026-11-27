set root [lindex $argv 0]
cd [lindex $argv 1]
read_verilog [lrange $argv 2 end]
read_xdc [file join $root fpga basys3 tripwire_basys3.xdc]
synth_design -top tripwire_basys3 -part xc7a35tcpg236-1 \
    -include_dirs [list [file join $root src]] \
    -verilog_define {TRW_SLOTS_FLOPS TRW_PIN_CFG_FLOPS}
opt_design
place_design
route_design

report_route_status -file route_status.rpt
report_utilization -file utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file timing.rpt
report_drc -file drc.rpt
write_checkpoint -force tripwire_basys3_routed.dcp

set mmcm [get_cells -hierarchical -filter {REF_NAME =~ MMCME2_*}]
set output_pin [get_pins -of_objects $mmcm -filter {REF_PIN_NAME == CLKOUT0}]
set core_clock [get_clocks -of_objects $output_pin]
if {[llength $core_clock] != 1 || abs([get_property PERIOD $core_clock] - 20.0) > 0.001} {
    error "Expected a single 20 ns clock at the MMCM output"
}

foreach {check delay_type} {setup max hold min} {
    set path [get_timing_paths -from $core_clock -to $core_clock -delay_type $delay_type \
        -sort_by slack -max_paths 1 -no_report_unconstrained]
    if {[llength $path] != 1} {
        error "No constrained 50 MHz $check timing path found"
    }
    set slack [get_property SLACK $path]
    puts "50 MHz internal $check slack: $slack ns"
    if {![string is double -strict $slack] || $slack < 0.0} {
        error "50 MHz internal $check timing failed"
    }
}
write_bitstream -force tripwire_basys3.bit
