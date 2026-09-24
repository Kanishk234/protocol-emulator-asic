# R1 risk spike: static timing of the synthesized lane harness with OpenSTA.
# Env: R1_LIB (liberty), R1_NET (netlist), R1_PERIOD (ns), R1_CONFIG_STATIC (see below).
# Pre-layout: ideal clock, no wire parasitics. See README.md for what that leaves out.

read_liberty $::env(R1_LIB)
read_verilog $::env(R1_NET)
link_design trw_r1_top

set period $::env(R1_PERIOD)
create_clock -name clk -period $period [get_ports clk]
set_clock_uncertainty -setup 0.25 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst_n din}]
set_load 0.01 [all_outputs]

# The register driving each net of a name pattern (flop or latch instance).
proc regs_of {pat} {
    set cells {}
    foreach n [get_nets -quiet $pat] {
        foreach p [get_pins -quiet -of_objects $n -filter "direction == output"] {
            set c [get_cells -of_objects $p]
            if {[string match "sg13cmos5l_d*" [get_property [get_lib_cells -of_objects $c] name]]} {
                lappend cells $c
            }
        }
    }
    return $cells
}

set latches {}
foreach c [get_cells *] {
    if {[string match "sg13cmos5l_dlhq*" [get_property [get_lib_cells -of_objects $c] name]]} {
        lappend latches $c
    }
}
puts "latch cells: [llength $latches]"

# R1_CONFIG_STATIC = 1: host-written configuration only changes while the lane is halted
# (ARCHITECTURE.md §9), so paths from it are not single-cycle paths while running. That is the slot
# and K store, the consumer ports' en/sel/accept, and the subscribers' en/mode/sel. Offsets are the
# chain layout in trw_r1_top.v (O_CP = 180, O_SUB = 198, 7 bits per subscriber, last_seq at +6).
if {$::env(R1_CONFIG_STATIC) == 1} {
    set cfg [regs_of {u_slots.*}]
    for {set b 180} {$b < 198} {incr b} { set cfg [concat $cfg [regs_of "chain\[$b\]"]] }
    for {set q 0} {$q < 17} {incr q} {
        for {set b 0} {$b < 6} {incr b} {
            set cfg [concat $cfg [regs_of "chain\[[expr {198 + 7*$q + $b}]\]"]]
        }
    }
    set_false_path -from $cfg
    puts "configuration registers (slot store incl. its write-data register, ports) set as false-path startpoints: [llength $cfg]"
}

# Endpoint groups. EVAL ends in the registers EVAL loads at its edge (§14 L4, L6): STATE, PEND,
# RB, the reservations, the EXEC-stage fields, the A latch, CALL, and the consumer ports' last_seq.
# EXEC ends in r0-r3, f0-f2, RZ and the output producer registers (L5).
set eval_regs [concat \
    [regs_of {u_lane.state[*]}] [regs_of {u_lane.pend[*]}] [regs_of u_lane.rb] \
    [regs_of {u_lane.resv[*]}] [regs_of u_lane.ex_slot] [regs_of u_lane.ex_rt] \
    [regs_of {u_lane.ex_op[*]}] [regs_of {u_lane.ex_dst[*]}] [regs_of {u_lane.ex_asrc[*]}] \
    [regs_of {u_lane.ex_bsel[*]}] [regs_of {u_lane.ex_imm[*]}] [regs_of u_lane.ex_dfe] \
    [regs_of {u_lane.ex_df[*]}] [regs_of {u_lane.ex_ot[*]}] [regs_of u_lane.ex_kt] \
    [regs_of {u_lane.a_lat[*]}] [regs_of {u_lane.a_tag[*]}] [regs_of u_lane.call_req] \
    [regs_of {u_lane.call_idx[*]}] [regs_of u_i0.last_seq] [regs_of u_i1.last_seq]]
set exec_regs [concat \
    [regs_of {u_lane.regs[*]}] [regs_of {u_lane.f[*]}] [regs_of u_lane.rz] \
    [regs_of {u_lane.out_valid[*]}] [regs_of {u_lane.out_seq[*]}] [regs_of {u_lane.out_tok[*]}]]
puts "EVAL endpoint registers: [llength $eval_regs]; EXEC endpoint registers: [llength $exec_regs]"

puts "\n==== worst path overall"
report_checks -path_delay max -digits 3 -fields {fanout slew cap}
puts "\n==== worst EVAL path (ends in an EVAL-loaded register)"
report_checks -path_delay max -to $eval_regs -digits 3 -fields {fanout nets}
puts "\n==== worst EXEC path (ends in an EXEC-written register)"
report_checks -path_delay max -to $exec_regs -digits 3 -fields {fanout nets}
puts "\n==== ten worst EVAL endpoints"
report_checks -path_delay max -to $eval_regs -group_count 10 -endpoint_count 1 -format end
puts "\n==== worst hold"
report_checks -path_delay min -digits 3 -format end -group_count 5
puts "\n==== summary"
report_wns
report_tns
report_worst_slack -max
report_worst_slack -min
exit
