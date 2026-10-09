# Extracted timing reserve: residual three-cell candidate

2026-10-08. Source extraction37844735445, from routing37837038264. Routed protocol regression37844735520 passes22/22, no skips. This is checkpoint evidence, not official clean-build closure.

## Measured results

Local cached OpenSTA used the actual extracted netlist and nominal SPEF from artifact11579821236, pinned standard-cell/SRAM corner libraries, and fully timed20ns constraints. Artifact effective-signoff.sdc sources LibreLane base.sdc; the standalone run uses the previously resolved fully timed constraints. All six20ns setup/hold metrics match CI within1e-6ns before accepting the sweep. No false paths or multicycle paths are present. Only clock period changes; parasitics, ports, uncertainties, derates and hardware stay fixed.

| Period ns | Slow setup WS ns | Typical setup WS ns | Fast setup WS ns |
|---|---:|---:|---:|
|20.00|0|0|0|
|19.90|0|0|0|
|19.85|0|0|0|
|19.75|-0.099644743|0|0|
|19.50|-0.349643886|0|0|
|19.00|-0.849643946|0|0|

Hold remains slow+0.315522939ns, typical+0.157048717ns, fast+0.062788613ns across the sweep.21 processes completed:12 initial sweeps and9 finer sweeps including repeated baseline validation.

The previously failing endpoint47775 has+0.150356174ns setup slack at20ns; endpoint47774 has+0.277061939ns. At19.75ns the failing path begins48909 and ends47775. Global setup WS remains0 because latch time borrowing can make reported required time equal arrival time. The original extracted max report explicitly shows a latch path borrowing4.056241ns out of9.828911ns maximum; that individual difference is not the full design's margin.

## Interpretation and limits

The complete analyzed extracted design tolerates a150ps period reduction from20ns to19.85ns with nonnegative setup and positive hold at all three corners. Its first tested failing period is19.75ns. This supports a modest timing reserve even though reported global WS stays zero. It does not prove a150ps margin for every timing check, every uncertainty model or an official reroute. No competition frequency change is proposed; the target remains20ns/50MHz.

Native stock37853023857 remains the clean-build dependency. Its AREA0/AREA1 results must establish whether closure survives fresh synthesis and stock repair; favorable screen results still need their own detailed routing, extraction, protocol regression and official GDS evidence.

Local raw evidence stays outside git: /tmp/tripwire-margin-37844735445/results.json and /tmp/tripwire-margin-fine-37844735445/results.json; scripts /tmp/run-residual-margin.py and /tmp/run-residual-margin-fine.py. Download failure during SPEF retrieval was retried successfully before any STA run.

## Electrical qualification limit

Subsequent exact checks.rpt audit finds slew violations slow91/typ3/fast1 and capacitance violations slow6/typ7/fast7 in this same extraction37844735445. These do not invalidate the reported setup/hold/period sweep, but the checkpoint is not electrically clean or official-ready. See PHASE2_NATIVE_EXTRACTED_PROBES.md.
