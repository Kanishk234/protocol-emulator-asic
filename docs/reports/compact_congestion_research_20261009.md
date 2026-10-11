# Compact shell congestion: measured locality and next experiment

The highest-leverage next step is to capture **native overflow coordinates**
on the unchanged cluster8 baseline. Configuration-buffer insertion is a
secondary comparison: the baseline already fails before those ten cells exist.
Preserve the routing policy and add diagnostic output rather than relaxing
capacity, skipping nets, or changing multiple CTS knobs.

## Evidence from the actual paired run

[Run37958932549](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37958932549)
reports148 cluster8 and169 ten-buffer overflow after50 native iterations.
Both cases explicitly disable clock NDR during congestion recovery on exactly
`clk`, `clknet_0_clk_regs`, `delaynet_0_clk`, and `delaynet_3_clk`.
This implicates clock routing as an investigation target; it does **not** prove
those nets are the sole cause of the final overflow.

The resolved clock NDR policy is `half`; signal routing remains Metal1–Metal4.
Global resource usage is33.19% and33.86%, respectively. Low average usage does
not identify narrow local access bottlenecks. The router counts53,494 blockages
and94 clock nets in the buffered case. These figures describe this checkpoint,
not the entire eFPGA's usable routing capacity.

The strict existing census comparison authenticates3,596 original instances,
18,073 original terminals, exactly ten added identity buffers, and unchanged
fixed macro and contracted connectivity. Detailed legalization moves1,550
original instances by up to21.6µm. A read-only census analysis finds59 moved
instances whose names begin `clk` or `delaybuf`; this is a name heuristic,
not an STA clock classification. Existing configuration branch nets in column3
increase their instance-origin HPWL proxy by19.2µm; one clock leaf increases by
12.96µm. Instance-origin proxies omit pin shapes and cannot establish actual
wire length or routed delay.

Reproduce the read-only analysis, without starting EDA:

```sh
source .venv/bin/activate
python test_internal/cloud_congestion_probe.py build/cloud_fanout_grt_37958932549
```

## Native output before a physical change

The pinned [OpenROAD GRT command reference](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/README.md)
supports `-congestion_report_file` and `-congestion_report_iter_step`. Request a
report at the final iteration and retain it even when the strict route command
returns an error. Keep the existing native script and its library, SDC,
routing-layer, macro-extension and resource-adjustment settings; append only
these reporting options. Do not use `-allow_congestion` to obtain the report.
The pinned implementation saves congestion state before reporting failure.

Compare the actual overflow boxes with macro boundaries, bottom configuration
branches, and the four reported clock nets' endpoint geometry. Collect real
ITerm/BTerm rectangles and their layers from OpenDB for this comparison;
macro instance origins alone are inadequate. A hotspot report is a diagnostic,
never a routing or timing pass. If the150-iteration run converges, inspect its
final coordinates and route timing before any further placement experiment.

## One isolated physical counterfactual

If congestion persists, reuse the exact cluster8 ODB and identical ten-buffer
connectivity edits, changing **only legalization policy**:

1. Save all original instances' placement statuses, origins and orientations.
2. Temporarily mark every original movable cell `FIRM`; leave existing fixed
   cells and macro untouched. Insert the same ten buffers and six-load groups.
3. Run native detailed placement for the new buffers, then restore each
   original status. Require all3,596 original origin/orientation/master records
   to match exactly, all original pins to match after buffer contraction,
   and native `check_placement` to pass. A no-free-site failure rejects the
   candidate; it is evidence to plan explicit whitespace rather than permission
   to overlap cells.
4. Run the same six explicit corner STA screens and identical strict GRT.
   Compare with the unchanged cluster8 baseline. Keep150 iterations only if
   used identically by both cases; retain zero-overflow as the acceptance gate.

The [pinned detailed-placement reference](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/README.md)
provides legalization, displacement controls and legality checks. Original-cell
freezing must first be verified against the pinned bindings and legalizer;
the census audit, not an assumed status semantic, determines whether it worked.
This experiment distinguishes buffer wire demand from incidental movement of
1,550 pre-existing cells. It cannot fix the baseline's148 overflow by itself.

## Subsequent clock experiment, conditional on hotspot evidence

The [pinned CTS reference](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/cts/README.md)
offers obstruction-aware buffering, which can reduce legalization movement
around macros, and independently controls cluster size and spatial diameter.
If real overflow boxes concentrate at macro/clock crossings, rebuild from the
authenticated original preCTS state with **only obstruction awareness enabled**,
keeping cluster size8 and all existing electrical/routing constraints. Compare
native displacement, all-corner fanout/slew/capacitance, GRT overflow and cost
before considering detailed route. There is no measured improvement yet.

Changing NDR strategy is lower priority: the current router already falls back
on the four congested clock nets. Blanket NDR removal would change physical
clock policy without establishing the cause; increasing artificial routing
capacity or skipping high-fanout nets would invalidate the experiment.

No new physical checkpoint was produced for this report. No area/timing benefit
is claimed for the proposed counterfactuals, no source hardware was edited,
and no phase or competition acceptance gate was completed.

## October 10 continuation

Actual150-iteration run37960021920 leaves the buffered overflow at169. Its
control case never reaches routing because image download consumes the observer
timeout, so it does not supply a new150-iteration control measurement.

Reviewed cloud_congestion_map.py uses a pinned native GlobalRouting subclass
and attributed local Tcl copies, adding only the two report flags from
patches/librelane-congestion-report.patch. Exact original-script hashes and
protected library/macro/routing/clock policies are mandatory. The workflow
pulls the pinned image separately before native observers. Its successful
report collection is explicitly distinct from the retained route failure.
This launches no new hardware or placement change; actual hotspot data still
needs to be collected and interpreted before the proposed counterfactual.
