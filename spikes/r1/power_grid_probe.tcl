# Native overlap calibration only; not pdngen or full-chip power acceptance.
# Required environment: WARP_PG_PROBE_LEF, WARP_PG_PROBE_TECH,
# WARP_PG_PROBE_GUARD (src/pdn_cfg.tcl), WARP_PG_PROBE_OMIT (0 or 1).
# Run in an empty diagnostic output directory; writes top.v there.
set omit $::env(WARP_PG_PROBE_OMIT)
if {$omit ne "0" && $omit ne "1"} {error "Expected explicit control/omission selection"}
set channel [open $::env(WARP_PG_PROBE_GUARD) r]
set source [read $channel]
close $channel
set begin [string first "proc loom_check_macro_stripes \{\} \{" $source]
if {$begin < 0} {error "Missing original PG guard"}
set end [string first "\n\}\n" $source $begin]
if {$end < 0 || [string first {set ::loom_max_pin_gap 7.0} $source] < 0} {
    error "Unexpected original PG guard or gap policy"
}
eval [string range $source $begin [expr {$end+2}]]
set ::loom_max_pin_gap 7.0
set ::env(PDN_VERTICAL_LAYER) Metal4
read_lef $::env(WARP_PG_PROBE_TECH)
read_lef $::env(WARP_PG_PROBE_LEF)
set channel [open top.v w]
puts $channel {module pg_probe(inout VPWR,VGND); warp_r1_candidate u_fabric(.VPWR(VPWR),.VGND(VGND)); endmodule}
close $channel
read_verilog top.v
link_design pg_probe
set block [ord::get_db_block]
if {[$block getDbUnitsPerMicron] != 1000} {error "Unexpected native units"}
set inst [$block findInst u_fabric]
$inst setOrient R0
$inst setOrigin 121440 30240
$inst setPlacementStatus FIRM
set layer [[ord::get_db_tech] findLayer Metal4]
foreach name {VPWR VGND} {
    set net [$block findNet $name]
    if {$net eq "NULL"} {set net [odb::dbNet_create $block $name]}
    $net setSpecial
    $net setSigType [expr {$name eq "VPWR" ? "POWER" : "GROUND"}]
    odb::dbITerm_connect [$inst findITerm $name] $net
    set swire [odb::dbSWire_create $net ROUTED]
    for {set k 0} {$k < 12} {incr k} {
        set center [expr {23520+109920*$k+($name eq "VGND" ? 4100 : 0)}]
        if {$omit && $name eq "VGND" && $center == 797060} {continue}
        odb::dbSBox_create $swire $layer [expr {$center-1050}] 3780 [expr {$center+1050}] 706860 STRIPE
    }
}
set code [catch {loom_check_macro_stripes} message]
puts "PROBE_RESULT $code $message"
if {$code != !$omit} {error "PG control/omission result did not reproduce"}
if {!$omit && [string first {LOOMPDN: 1 stripe shape(s)} $message] < 0} {
    error "Original control failed for an unexpected reason"
}
puts "PROBE_DIAGNOSTIC_COMPLETE physical_acceptance=false"
