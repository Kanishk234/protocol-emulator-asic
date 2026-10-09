# Compact closure plan, October 9

The improved compact design has a working routed C2 tile, but the complete
successor is not qualified. G1 remains frozen. Phase5 exit gates stay open.

| Evidence | What it establishes | What remains |
|---|---|---|
| [37814078650](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37814078650), [37958116371](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37958116371) | Actual C2 native route/antenna/Magic/KLayout/GDS LVS0; original306signal+2PG interfaces exact |62fanout; deferred virtual-clock setup fails; no configured timing |
| [37958116481](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37958116481) | Actual final C2 substituted into passing native control passes9164 actual loaded latches,28TX/28RX,STOP/reset | No SDF; other regenerated tiles lack matching qualified physical views |
| [37956470190](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37956470190) | Cluster8 plus ten buffers clears shell fanout at three explicit estimated corners; estimated electrical/timing gates pass | Placement changes1550cells; fresh route/extracted checks required |
| [37708459393](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37708459393) | Different stronger-driver layout passes physical and extracted shell slew/setup/hold/cap | Fanout33; cannot transfer its wires to the changed clock/buffer layout |

## Next physical experiments

1. D066 official precheck: keep source driver GDS/ODB immutable, derive only
   valid existing external PG accesses, require exact native remaining-pin and
   conductor census, then run all nine unmodified checks. Pinned Tcl API
   compatibility fix follows37958116017;37958932525 is the fresh run.
2. D067 paired GRT screen37958932549: compare authentic cluster8 and ten-buffer
   sources with identical settings. Actual result: control148 and candidate169
   overflow; both fail. Investigate localized congestion before another
   placement/route experiment. Native complete final overflow must be
   zero; retain actual congestion/wirelength/guides and exact placements.
   This screens routing cost without another long detailed-route trial.
3. If routing evidence supports continuation, route from this actual source
   afresh and repeat native antenna/connectivity, physical geometry/LVS and
   extracted all-corner shell timing. The old stronger driver is absent from
   this source. Resize only if the new measured wires reproduce its violation;
   that would be a separate single-change experiment.
4. Remedy actual C2 fanout without touching configuration storage or original
   tile interfaces. Separate49 configuration distribution nets from13 user/data
   nets; measure added buffers, congestion and loaded native functionality.
5. Establish genuine configuration-specific timing and qualify remaining
   regenerated physical tiles, then assemble a matching complete fabric and
   rerun full-chip official precheck and real loaded protocols. Partial tile
   success or passing shell timing cannot replace these checks.

## Acceptance discipline

Keep every electrical limit, timing target and native check enabled. A static
configuration mode can be used only in a separately specified functional timing
diagnostic, with the exact real loaded latch values and real user clocks;
it must not erase configuration-loader electrical validation. No tied-off
configuration or state forcing in the chip. No architecture superiority claim
without an equal-total-area comparison. The failed identical-original remap
proof still cannot adjudicate remapping until its feedback construction is sound.

These experiments run on standard GitHub cloud runners with bounded jobs.
Local work uses only lightweight source, hash, parser and mock checks. Saved
CI artifacts are temporary; preserve authenticated source views/manifests and
reproduction instructions before retention expires. No submission view or
frozen hardware is replaced by these diagnostics.

## Next tile diagnostics prepared from actual retained C2

Actual37814078650 fanout inventory splits49 configuration nets from13 user/data
nets. A configuration-only buffering candidate can retain the49 existing
forwarding buffers directly on their original inputs and add equal-depth leaf
branches only to529 latch D and529 latch GATE sinks. Count-derived estimate:
82 FrameData plus67 FrameStrobe buffers (149 total) with at most8 latch loads
per leaf. These are analytical buffer counts, not measured area/timing/routing
results. Keep forwarding routes and all storage instances/pin bindings exact;
configuration data/strobe skew and loaded operation must be tested again.
Thirteen user/data violations require separate treatment. Generic repair_design
also resizes and repairs slew/capacitance, so it would not isolate this change.

Timing must use the clock actually selected by the loaded configuration.
The exact final C2 has529 configuration latches and8 userFF; the latter share
clock mux _1288_. In the tested UART image, C2 instances X2Y1/X2Y3 select
N_GBUF_END[3] using Frame0 bits20/21 both high. There is no physical tile port
named GCLK. A tile-local diagnostic must trace the selected port through its
real clock mux/buffers; complete-fabric analysis must trace the upstream
configured network as well. User reset operates through data logic and must
remain timed. Exact real latch values and all8 FF clock endpoints need audit
before any case analysis is accepted. These are planning observations from
37958116481's authenticated source, not a configured timing pass.
