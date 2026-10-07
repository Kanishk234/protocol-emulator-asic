# Same full Magic rules; no standalone raw-library import can shadow overlays.
crashbackups disable
locking disable
units internal
gds noduplicates true
gds readonly true
gds maskhints true
gds read "$::env(WARP_FILLER_OUT)/chip_trial.gds"
magic::suspendall
puts "WARP_CHIP loading tt_um_warp; full rules enabled"
flush stdout
load tt_um_warp
select top cell
drc euclidean on
drc style drc(full)
drc check
# Match stock LibreLane's synchronous selected-chip result query; catchup
# also drains unrelated queued library-cell checks in the imported layout.
set report [open "$::env(WARP_FILLER_OUT)/chip_trial.rpt" w]
set findings [drc listall why]
set count 0
foreach {reason boxes} $findings { incr count [llength $boxes] }
puts $report "count $count"
puts $report $findings
close $report
puts "WARP_CHIP reported_boxes=$count"
flush stdout
quit -noprompt
