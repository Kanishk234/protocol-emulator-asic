# WARP D099 native API regression; no chip, contention, or timing qualification.
# Fixture commands follow OpenROAD src/grt/test/gcd.tcl at dcf36133 (BSD-3-Clause).
# Keep the upstream LICENSE and untouched fixture files with run artifacts.
read_lef $::env(WARP_REGRESSION_LEF)
read_def $::env(WARP_REGRESSION_DEF)
source $::env(WARP_REGRESSION_CENSUS)
set warp_out $::env(WARP_REGRESSION_OUT)
set warp_mode $::env(WARP_REGRESSION_MODE)
if {$warp_mode ni {stock custom}} {error "Unknown native regression mode"}

global_route -verbose
write_global_route_segments $warp_out/before-segments.txt
census $warp_out/before-census.tsv

proc warp_guides {path} {
    set out [open $path w]
    foreach net [[ord::get_db_block] getNets] {
        puts $out "NET\t[$net getName]\t[$net getTermCount]\t[llength [$net getGuides]]\t[$net isConnectedByAbutment]"
    }
    close $out
}
warp_guides $warp_out/before-guides.tsv

if {$warp_mode eq "stock"} {
    puts "WARP_REGRESSION_STOCK_DEFAULT_COMPLETE"
    exit
}
if {[llength [info commands grt::force_reroute_pair]] != 1} {error "Force API missing"}
set warp_candidates {}
foreach net [[ord::get_db_block] getNets] {
    set name [$net getName]
    if {[$net getSigType] eq "SIGNAL" && ![$net isSpecial] &&
        [$net getTermCount] >= 2 && [llength [$net getGuides]] > 2 &&
        ![string match -nocase *clk* $name] && ![string match -nocase *clock* $name]} {
        lappend warp_candidates [list $name $net]
    }
}
set warp_candidates [lsort -index 0 $warp_candidates]
if {[llength $warp_candidates] < 2} {error "No two long-guide signal candidates"}
lassign [lindex $warp_candidates 0] warp_first_name warp_first
lassign [lindex $warp_candidates 1] warp_second_name warp_second
if {$warp_first eq $warp_second} {error "Distinct candidate handles required"}
set warp_selected [open $warp_out/selected.tsv w]
puts $warp_selected "SELECTED\t$warp_first_name"
puts $warp_selected "SELECTED\t$warp_second_name"
close $warp_selected

proc warp_rejected {name command} {
    set code [catch {uplevel 1 $command} message]
    if {$code != 1 || ![string match {*Invalid/duplicate force-reroute signal net*} $message]} {
        error "Invalid API case $name did not reject as expected: $message"
    }
    set out [open $::env(WARP_REGRESSION_OUT)/invalid-cases.tsv a]
    puts $out "INVALID\t$name\tREJECTED"
    close $out
}
warp_rejected duplicate [list grt::force_reroute_pair $warp_first $warp_first]
write_global_route_segments $warp_out/duplicate-segments.txt
census $warp_out/duplicate-census.tsv
warp_guides $warp_out/duplicate-guides.tsv
warp_rejected null [list grt::force_reroute_pair NULL $warp_second]
write_global_route_segments $warp_out/null-segments.txt
census $warp_out/null-census.tsv
warp_guides $warp_out/null-guides.tsv

# Restore the intentionally changed signal type even if the rejection test fails.
set warp_signal_type [$warp_first getSigType]
$warp_first setSigType CLOCK
set warp_clock_code [catch {
    warp_rejected clock [list grt::force_reroute_pair $warp_first $warp_second]
} warp_clock_message warp_clock_options]
$warp_first setSigType $warp_signal_type
if {$warp_clock_code != 0} {return -options $warp_clock_options $warp_clock_message}
write_global_route_segments $warp_out/clock-segments.txt
census $warp_out/clock-census.tsv
warp_guides $warp_out/clock-guides.tsv

puts "WARP_REGRESSION_FORCE_BEGIN"
grt::force_reroute_pair $warp_first $warp_second
write_global_route_segments $warp_out/after-segments.txt
census $warp_out/after-census.tsv
warp_guides $warp_out/after-guides.tsv
puts "WARP_REGRESSION_FORCE_COMPLETE"
