# D-057: route the authenticated one-driver ECO; bounded hosted runner only.
# Derived from our proven late_route_repair.tcl; source baseline is measured.
# Placement-only ECO invalidates pre-existing pin escapes and parasitics.
# Pinned OpenROAD dcf36133a369abc8f3c5e5738cd4d82e4903c0e0:
# src/drt/src/global.h: ROUTESHAPECOST=8, MARKERCOST=32.
# src/drt/src/dr/FlexDR.cpp: strategy52/53 use
# {7 offset 32 32*shapeCost 8*markerCost 100*shapeCost .999 DRC false}.
# src/drt/src/TritonRoute.{tcl,i,cpp}: single_step_dr initializes routing;
# step_dr takes nine arguments; step_end commits the result to OpenDB.
# A database reload resets router state. These are late-cost experiments,
# not continuation of the original iteration52 or reproduction of iteration53.
# The caller must authenticate input SHA256, pin the tool, and subsequently
# run stock antenna/connectivity, extraction, DRC/LVS and timing checks.
foreach key {WARP_REPAIR_SOURCE WARP_REPAIR_OUT WARP_REPAIR_EXPECTED_MARKERS} {
    if {![info exists ::env($key)] || $::env($key) eq ""} {
        error "Missing required environment variable $key"
    }
}
foreach command {drt::step_dr drt::step_end drt::check_drc drt::detailed_route_num_drvs} {
    if {![llength [info commands $command]]} {
        error "Pinned router API missing: $command"
    }
}
set out $::env(WARP_REPAIR_OUT)
file mkdir $out
set expected $::env(WARP_REPAIR_EXPECTED_MARKERS)
if {$expected ne "measure"} {error "Driver ECO must measure its fresh starting markers"}
read_db $::env(WARP_REPAIR_SOURCE)
check_placement -verbose -report_file_name "$out/source_placement.json"
set_thread_count 4
set_routing_layers -signal Metal1-Metal4
set block [ord::get_db_block]

# Exact instance masters/placements and all instance/port net memberships.
# Routing is the only allowed mutation; keep lists in memory before routing.
proc warp_repair_topology {block} {
    set instances {}
    foreach inst [$block getInsts] {
        set pins {}
        foreach term [$inst getITerms] {
            set net [$term getNet]
            set name "UNCONNECTED"
            if {$net ne "NULL"} {set name [$net getName]}
            lappend pins [list [[$term getMTerm] getName] $name]
        }
        lappend instances [list [$inst getName] [[$inst getMaster] getName] \
            [$inst getOrigin] [$inst getOrient] [lsort $pins]]
    }
    set nets {}
    foreach net [$block getNets] {
        set members {}
        foreach term [$net getITerms] {
            lappend members [list instance [[$term getInst] getName] [[$term getMTerm] getName]]
        }
        foreach term [$net getBTerms] {lappend members [list port [$term getName]]}
        lappend nets [list [$net getName] [$net getSigType] [lsort $members]]
    }
    return [list [lsort $instances] [lsort $nets]]
}
proc warp_repair_count {path} {
    if {![file exists $path]} {error "Missing native DRC report $path"}
    set channel [open $path r]
    set report [read $channel]
    close $channel
    return [regexp -all -line {^violation type:} $report]
}
set topology [warp_repair_topology $block]
puts "WARP_REPAIR checking authenticated source before mutation"
drt::check_drc -output_file "$out/before.drc.rpt" -marker_name WARP_REPAIR_BEFORE
set before [warp_repair_count "$out/before.drc.rpt"]
puts "WARP_REPAIR before=$before expected=$expected"
# The caller binds the legal ECO by exact SHA; its stale-wire marker count
# is measured here, never reused as acceptance. Final native zero remains required.

detailed_route -single_step_dr -or_seed 42 -verbose 1 \
    -drc_report_iter_step 1 -output_drc "$out/repair.drc.rpt"
# DRC-only steps return immediately when initialization has an empty markerlist.
# Bootstrap with INCR (mode3), preserving pre-existing routed nets, as the stock
# main loop does for an incremental input. This also runs connectivity checking.
drt::step_dr 7 0 3 8 0 8 0.950 3 true
set bootstrap [drt::detailed_route_num_drvs]
puts "WARP_REPAIR bootstrap=$bootstrap"
set final $bootstrap
if {$bootstrap > 0} {
    # Continue through a guide plateau so the native state machine can enter
    # STUBBORN. The first pair alone improved17->7->3 and remained GUIDES.
    # Same costs (offset changes are ignored by the FSM argument comparison),
    # at most six steps; the outer hosted timeout also bounds stubborn work.
    foreach offset {-2 -3 -2 -3 -2 -3} {
        puts "WARP_REPAIR late_offset=$offset starting=$final"
        drt::step_dr 7 $offset 32 256 256 800 0.999 0 false
        set final [drt::detailed_route_num_drvs]
        puts "WARP_REPAIR late_offset=$offset markers=$final"
        if {$final == 0} {break}
    }
}
drt::step_end
if {[warp_repair_topology $block] ne $topology} {
    error "Routing changed an instance master/placement or net/port connectivity"
}
# Save actual committed final views even when remaining markers make this fail.
write_db "$out/final.odb"
write_def "$out/repair.def"
write_verilog "$out/repair.nl.v"
write_verilog -include_pwr_gnd "$out/repair.pnl.v"
puts "WARP_REPAIR committed final ODB/DEF/netlists; running fresh full-chip check"
# Run a full fresh native check after step_end. check_drc during the active
# step sequence would reinitialize router data and is deliberately avoided.
drt::check_drc -output_file "$out/after.drc.rpt" -marker_name WARP_REPAIR_AFTER
set checked [warp_repair_count "$out/after.drc.rpt"]
set channel [open "$out/result.json" w]
puts $channel "{\"before_markers\":$before,\"bootstrap_markers\":$bootstrap,\"step_markers\":$final,\"checked_markers\":$checked,\"topology_unchanged\":true,\"physical_acceptance\":false}"
close $channel
puts "WARP_REPAIR final_step=$final full_check=$checked topology_unchanged=true"
if {$final != 0 || $checked != 0} {error "Native routing remains nonzero"}
