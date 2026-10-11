# Compact shell congestion: measured locality and next experiment

**October10 verified continuation:** broad151-cell padding failed bounded
legalization38102423038; five-cell global legalization38111705881 reversed an
unrelated cell's vertical phase; same-row all-right38112069098 exceeded a real
row boundary. Each was rejected before STA/routing. Refined exact-source
left/right placement38112272623 passes native legality and all six estimated
shell STA screens. Exactly five cells move by at most1.44µm, preserving all
3606 masters/orientations/statuses/terminals and the fixed macro. Five selected
cells have proved gaps; NL remains3e3e9fd0… and new ODB is13e88cf8….
This is placement/electrical screening, not routing closure. D-075 compares its
actual routing with the fixed-original146-overflow baseline under identical
original50-iteration policy. The historical investigations below retain their
original scope and rejected results.

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

## October10 actual native hotspot result

[Run38100978078](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38100978078)
successfully collects both native reports while preserving failed routing:
cluster8 overflow148 and ten-buffer169. The reports have114 and116 markers,
respectively; their horizontal/vertical marker-overflow sums happen to equal
the corresponding final table totals in this run. The parser does not assume
that equality in general.

Authentic report hashes:

- cluster8: `c49fcfb2dfe5f8ae9333cd8345c020cbb645792524a496969ddf1c5e91e36a22`
- ten buffers: `a33e207b5e5f5f0a96f8264ffb8bc0d4f106a32645a7d1938a4623688c37a53b`

The dominant native coordinate band is x0–121.44,y475.2–525.6: baseline62
markers/90 overflow, candidate55 markers/95 overflow. None of these markers
has zero capacity. Their real net sources repeatedly include shell CRC/SPI
logic and clock leaf25. Baseline worst is overflow7 at
(43.2,504)–(50.4,511.2); buffered worst in this band is overflow6 at
(7.2,504)–(14.4,511.2). The narrow bottom band y0–15.12 accounts for only
11 and13 overflow. Clock-only or bottom configuration-only fixes therefore
miss most of the observed congestion. Net appearances are not independent
contributions: one marker can name many nets.

These coordinates are micrometers, preserved as exact native decimal text
without conversion. The [pinned TR writer](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/src/db/dbMarker.cpp#L215)
divides each bounding-box coordinate by the native block database units per
micrometer before formatting four decimals. Configured macro location is
121.44,15.12µm, with source LEF size1120.32×669.06µm. Thus this dominant
band is physically in the left shell. The existing instance-origin census is
not a substitute for actual placed cell rectangles.

The revised next isolated experiment is **local one-site placement padding
around actual CRC/SPI cells overlapping the dominant band**, using native block units and actual placed rectangles. Keep cluster8, the exact macro/RTL/masters, layers and timing
constraints unchanged. Require legal placement, preserved connections/config
storage, bounded displacement, six-corner STA and strict GRT. Padding changes
placement whitespace, not intrinsic cell area; report any actual displacement
and congestion improvement or regression. This is a hypothesis, not a measured
fix. Adding bottom-column buffers or more routing iterations is lower priority:
the actual150-iteration run38100977984 still fails149/169 overflow.

`test_internal/audit_congestion_report.py` strictly validates every four-line
marker, source, native layer, box ordering and overflow arithmetic, and can
require the manifest SHA. It retains all marker coordinates and net names.
Positive parsing of actual reports and arithmetic/box/truncation/category/hash
negative controls pass without EDA.

The [pinned FastRoute marker implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/utility.cpp#L2635)
creates horizontal/vertical planar marker boxes, capacity/usage/overflow comments
and net sources; it does not assign a physical layer. Consequently every actual
`Layer -` remains unset in our output. It also writes a report only if a marker
category exists: the collector now records legitimate native zero-overflow with
no file as `report_present:false`, without inventing a report hash or count.

### Concrete bounded padding implementation plan

Start from cluster8 ODB SHA
`0a0af0c1a0e4c413f52c43de70772dfff857a7c98402fa9b5b7e8dac19a53f99`
and the existing authenticated NL/SDC. Keep the ten-buffer insertion out of this
first experiment so exactly one placement policy changes. The remaining five
configuration fanout violations are unchanged baseline blockers, not waivers.

Inside the pinned container, read the native block's database units per micron,
rows/site width and every instance's real `getBBox`. Select only original
standard-cell instances with names under `u_shell.u_crc.` or `u_shell.u_spi.`
whose actual box intersects x0–121.44,y475.2–525.6µm. Exclude macros and fixed
instances; require a nonempty exact selection census recording names, masters,
boxes, original placement statuses and the single site width. Match masters
and complete pin connectivity with the pre-existing strict census.

Apply `set_placement_padding -instances <selected native names> -left 1 -right 1`
and native detailed placement. The original resolved `DPL_CELL_PADDING` is0.
Because OpenDP has padding precedence rules, prove this instance rule actually
takes effect before running the experiment; retain native padding/bounding-box
evidence. Do not substitute a global rule or master rule, which would change
the experimental scope. Native legality must pass, every original master,
orientation, status and connection must remain unchanged, and fixed macro
geometry must match exactly. Reject if any original cell moves more than22µm
on either axis; this is an audit bound, not an added placement optimization knob.
Record every displacement and the exact changed output ODB/NL hashes.

Run the existing explicit fast/slow/typ STA mechanism on both baseline and
candidate. Require candidate fanout count no greater than the existing five
at each corner, zero slew/capacitance violations, positive setup/hold and
unchanged20ns shell clock. This does not establish configured-fabric timing.
Run identical50-iteration native GRT plus the already reviewed copied reporting
script on both, preserving strict zero overflow for route acceptance and all
failures. Limit each STA process180s and each route900s in a standard hosted
45-minute job, with image pull before observer timeouts and always-uploaded
artifacts. Do not advance to DRT merely because overflow decreases.

This plan needs a new controlled placement producer plus six explicit STA
processes, source authentication and native effective-padding proof. No partial
workflow is shipped that could report success without those gates. Existing
map collector and parser are ready to consume the resulting native reports.

### Actual padding rejection and bounded correction

Padding run38102082569 selects151 cells and produces the requested spacing,
but correctly fails its placement-preservation audit. Actual native boxes show
334 physically moved instances, including32 beyond22µm and a maximum56.7µm.
Separately, OpenDP normalizes1,602 orientations, often changing the instance
origin while retaining exactly the same physical box:1,377 orientation changes
have unchanged boxes. For example `_117_` keeps box
(82.56,589.68)–(84.96,593.46)µm despite R180→MX origin normalization.
The distinction does not rescue the32 excessive real moves.

The correction uses native `detailed_placement -max_displacement {22 22}`.
Both entries are positive because the pinned implementation substitutes default
displacement when either native argument is zero. The pinned Tcl converts the
micrometer bounds to integral sites/rows, so these bounds are conservative for
the480DBU site width and3780DBU row height. Retain the canonicalized intermediate
census, restore each original orientation with `setOrient` followed by
`setLocation` at the captured legalized box's lower-left corner, and require
all four actual box coordinates to remain identical through this restoration.
Re-run native legality and effective-spacing proof afterward. Original statuses,
orientations, dimensions and connections remain strict; both instance-origin
and actual-box displacement must stay within22µm. A failed bounded placement
or invalid restored row orientation rejects the trial rather than relaxing it.

The source mapping is pinned
[OpenDP Tcl](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/src/Opendp.tcl)
and [native detailed placement](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/src/Opendp.cpp#L99).
Lightweight controls confirm positive bounds and anchor capture precedes
orientation restoration. Reconstructing original orientation anchors for the
failed actual geometry still rejects its excessive physical displacement.
No corrected native run or improvement is claimed here.

The orientation-restoration correction also requires identical **vertical
mirror phase before restoration**. R0/MY preserve the vertical axis, whereas
MX/R180 reverse it. Actual38102082569 contains142 cross-group transitions;
these cannot be treated as harmless horizontal normalization because restoring
the old orientation could invert power-pin alignment on the new row. The
collector retains canonical intermediate census/geometry, checks native
canonical legality, then rejects any vertical-phase change before modifying
orientation. Only same-phase normalization can reach the restoration and final
native legality/spacing checks. Unknown orientations also reject. Lightweight
controls accept the two same-phase normalizations and reject all four observed
cross-phase classes plus an unsupported orientation. This is a strict extra
guard, not a claim of extracted power connectivity signoff.

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
# 2026-10-11 continuation: actual endpoint hypothesis

**Actual routing follow-up:** [38163542037](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38163542037) collects two genuine native routing failures: baseline146 versus relocated136 overflow under identical50iterations, libraries, margins and routing policy. Baseline111 versus candidate100 planar markers; the old targeted4-overflow marker and net683 source marker disappear. Fully-contained left band remains85 planar overflow (53 versus54 markers); new worst marker is6 atx7.2–14.4,y504–511.2µm. Candidate marker SHA1f886f3f39691ae01b20708f41f2a29d9aa2bd226bbe7836762dff151a16b54a; resultSHA97b9a2e5a83f526da7290fad7324c70ed037740a17c5c7e46db9ffc9c9913a09. This establishes a measured improvement at unchanged cell area/source/timing policy, not routing closure or equal-area architecture superiority.

Read-only actual relocated census finds445 two-terminal tiehi→RESET_B nets. Of these,116 have source/receiver bbox-row separation≥30µm (maximum139.86µm). Seven such source nets appear in the new worst marker: net565,643,665,668,670,675,679. Their bbox-row separations range37.80–117.18µm. This supports investigating receiver-local placement of existing reset constants with actual native row/site/power legality and unchanged masters/connectivity; it does not prove all congestion comes from ties or measure actual routed wirelength. Wider relocation needs its own decision, exact placement bounds, electrical checks and paired native measurement.

The one-cell producer [38163199430](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38163199430) passes native legality, exact one-cell placement and all six estimated shell STA/electrical guards. Candidate ODB SHA8a2091f16365ba2eb3391b610fbb401bbf4f632f8d2b24118dcbbc086234852a; NL stays3e3e9fd0a7632c1669858c99ff968aebcd671550488736f4c51c8d2222722136. Actual result SHA0d2375d73627d7ac4d766883c3d68619ddd5e92651b28c97021419cb1b47e70c. Baseline and relocated estimated slacks match: fast setup14.5141/hold.116141ns, slow12.7828/.635476ns, typical13.8665/.304198ns, all fanout/slew/cap counts0. This producer has not run routing; the hypothesis below still needs its paired native GRT result.

Actual paired38113003427 has unchanged146 overflow and byte-identical baseline/five-move marker maps. The successful spacing producer is not a routing improvement. Native endpoint census shows _150_,_181_,_189_ are not attached to the source nets named in the worst marker. Existing tiehi_251__684/L_HI and register_251_/RESET_B are the only two terminals on marker source net683.

The pinned [OpenROAD makeItermPins implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp) transforms each master pin rectangle into placed coordinates. Subsequent access-point/grid choices use router-specific logic; cell bounding-box intersection or pin centroid alone does not prove a congestion contribution.

Using the pinned [CMOS5L LEF](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lef/sg13cmos5l_stdcell.lef), the actual MY tie origin91.20,510.30µm places L_HI at x89.615–89.900,y512.465–513.210µm. Proposed bbox91.68–93.60,y502.74–506.52µm gives MY origin93.60,502.74 and L_HI x92.015–92.300,y504.905–505.650µm. Actual R180 receiver RESET_B is x89.890–90.495,y508.335–508.790µm. These transformed shapes motivate testing removal of a coarse511.2µm vertical-band crossing, not an asserted routing fix. D-078 requires exact one-cell movement, unchanged connectivity/all other instances, same vertical power phase, native legality and six shell STA/electrical guards before routing comparison. No new hardware source change or protocol-specific resource.
