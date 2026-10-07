# Same full Magic rules; no standalone raw-library import can shadow overlays.
gds noduplicates true
gds readonly true
gds maskhints true
gds read "$::env(WARP_FILLER_OUT)/chip_trial.gds"
drc euclidean on
drc style drc(full)
load tt_um_warp
select top cell
drc check
drc catchup
set report [open "$::env(WARP_FILLER_OUT)/chip_trial.rpt" w]
set findings [drc listall why]
set count 0
foreach {reason boxes} $findings { incr count [llength $boxes] }
puts $report "count $count"
puts $report $findings
close $report
quit -noprompt
