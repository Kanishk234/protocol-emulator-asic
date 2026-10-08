# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

## 2026-10-07 (session67: route the legal ECO; independent reproduction/native audits)
**Done:** proactively checked corrected placement37689324316; success.
Downloaded actual placement-only ODB7b2811c291443d4208bcb1154fbe37ab6eeb7be6702c52060f135d0318509adf
and strict one-master/three-cell/legal-placement/connectivity evidence. BUG45
coverage updated. Prepared D-057 route of this exact placement: measured
starting stale-wire markers, incremental bootstrap plus at most six late-cost
passes, unchanged topology/masters/placement, fresh native0, stock antenna/
critical connectivity, then fresh extraction/full geometry/LVS and strict
all-corner slew/setup/hold/cap. Fanout remains explicitly open. Generalized
physical helper with explicit ECO provenance and exact fresh-DEF filler counts;
original defaults/gates remain. No frozen hardware/PDK edit. Local Python AST,
Tcl completeness, YAML and whitespace checks pass; no local EDA.
Reactivated existing bounded agents for clean-readme reproduction and read-only
matched-native/fanout audit; no additional agents or local heavy work.
**Boxes ticked:** none.
**Next:** launch/monitor routed ECO, cancel only redundant baseline repeats
autoqueued by shared diagnostic-helper edits, review agents' independent work
and inspect any failure immediately. Native mapping/function, configured timing,
fanout, precheck and clean reproduction remain before successor promotion.

**Launched/audited:**3d48519 pushes routed ECO37690243797, setup succeeds and
route stage active. Canceled redundant old-layout37690243661/37690243635 only;
accepted baseline artifacts and new trial/regressions retained. Fresh user
failure report audited: no new failures; old placement37688867787 is already
fixed by passing37689324316. Independent audit confirms33 real Liberty fanout
violations (27 clock leaves/6 configuration drivers), not solved by driver size.
Prepared reviewed fresh README reproduction from agent: new workflow/script
only, standard cloud runner, strict tool/README/XML/source provenance, no
build cache or local EDA. AST/YAML/README lookup/XML negative controls pass
locally. Native audit recommends stage isolation with passing original-control
mapping before paying for new tile hardening; no unsupported mux-only claim.

**Independent gate passed:** clean README37690896748 on962da93 succeeds.
Downloaded result/command provenance and all XMLs: all stages0, loaded30/30
no skips and cosim1/1, default idle17/default UART1 documented skips only.
Tool/package/README/source checks pass. Ticked Phase5 clean reproduction task
and exit item with this evidence; remaining phase items stay unchecked.
Main ECO37690243797 fails native DRT-0206 on moved-input net u_cfg._17_ after
source22/bootstrap27. BUG46: stale pin escapes. Prepared exact affected-signal
wire ripup before incremental routing; PG rails/other routing and all logical
topology preserved, final connectivity gate unchanged. Primary pinned API
verified; Tcl completeness/whitespace checks pass. Automatic approval review
timed out on one status query; allowed single retry succeeds, no bypass.
Prepared small hash-bound historical C2 synthesis input with Apache license/
attribution for native stage isolation; agent prepares separate cloud probe.

## 2026-10-07 (session66: access restored; same-layout physical closure)
**Done:** user requested continued work and explanation of the review limit.
Fresh authorized GitHub retry succeeds; no bypass used. Downloaded successful
37674839060 evidence and previously blocked37673567925 failed report. New
native0 source gives Magic0/KLayout0/GDS-based shell LVS0 in22m14s; final GDS
hash7475586c234ce15f0d51b47a9882990b58a703e9c4f387083bd3f09aa4cf7a7a.
All supplied shell setup/hold corners pass at20ns, but slow slew9 and fanout33
remain. Old3-marker source has LVS16/power pin matching failure; exact cause
not isolated. Latest frozen G1 gds37659595229 and HEAD33191 lint/docs/test/unit
pass. Native resynthesis stress37659112021/37659171115 both pass, but those
netlists still lack matching physical views. Recorded rejected containment
pins, claim/report/phase summary and physical run duration; no phase box ticked.
Prepared D-049 same-wire driver refresh on authenticated new extracted ODB
02b8bd30f3fb12e4a66e2322b5f3906c236dd93eed8b8cd1eeeff95f6e796a61,
strict physical-source and nine-pin checks, hash-recorded SPEF/SDC, standard
cloud20min bound. Python AST/YAML/whitespace checks pass locally; no local EDA.
**Next:** read fresh driver screen; if promising, prepare one-cell physical
resize/legalization/routing/extraction with unchanged gates. Matching native
tile hardening, configured timing, precheck and clean reproduction remain
required before any compact promotion. No current failure is waived.

**Launched:** scoped c070159/27b7b6a/ec9121f pushed; fresh same-wire slew
37688389888 active, latest lint/docs/unit/test active at launch audit.
Read-only actual DEF/LEF audit finds stronger driver adds3 sites/5.4432um2
and overlaps adjacent hold1096 by1.44um at unchanged origin. Its left neighbor
is also packed. Record nearby fillers and cells; a direct physical master
swap is illegal, so future ECO must legalize neighbors and reroute, not reuse
old wires as acceptance. No local route or original view mutated.

**Fresh diagnostic verified:**37688389888 succeeds; downloaded result has
baseline slew9/candidate0/fanout33 both. Prepared D-056 exact three-cell
placement preflight, source hash and Liberty checked, unchanged connectivity/
orientation/all other placement, one master only, strict placement gates.
Retained trial is explicitly not valid routing/parasitics. Python AST/YAML,
Tcl completeness/JSON-output and whitespace checks pass; no local EDA.

**Immediate failure fix:** placement37688867787 fails before mutation because
our numeric test misreads the pinned native void return (BUG45), not observed
placement violations. Downloaded full log and exact pinned Opendp.i/
CheckPlacement.cpp confirm void API plus DPL-0033 on actual illegal placement.
Invoke checker directly with baseline/candidate report files; preserve native
failure gate. Corrected cloud result pending. No master/placement promotion.

## 2026-10-07 (session65: continue physical closure and loaded phase stress)
**Done:** proactively checked current runs/failures at user's request to
continue without repeated confirmation. Native late repair37669731197 and
stock-aligned Magic37669173193 still active; no newer failure in initial
audit. Prepared independent frozen-G1 UART check using actual committed image
loaded through SPI,48 RX bytes across3 deterministic seeds, all-early/all-late
boundary phases and per-bit random phases, delayed reads0..128clocks, empty
channel after each read, framing/overrun flags, USER_RESET and STOP parking.
Trace preserves bitfile hash, every seed/byte/phase/read delay, status and
failure; XML requires exactly1 non-skipped successful case and48 verified
trace entries. New separate bounded standard-runner workflow; no test/src/
macro/arch edits to trigger or interfere with hardening. Python AST/YAML/shell
checks local only; simulation acceptance pending in cloud. No new native/SDF/
physical rate claim. No additional agents spawned.
**Boxes ticked:** none.
**Next:** inspect physical/native results and targeted stress trace, then
repair the specific remaining failures without relaxing gates.

**Verified progress:** UART phase37671919707 succeeds; downloaded strict XML
and trace verify48 correct bytes/3 seeds/all phase endpoint cases, actual
read-delay range0..125clocks and no framing/overrun. Full-chip filler
37669173193 reports Magic0 (baseline6350),20714 replacements/empty non-pSD
XOR and exact GDS hash3ee36af59b8b5964f1796b7b2756e7dad859572d3e23266c848b05fc58ae9f9b.
This qualifies only that scratch Magic check, not native/LVS/timing.
Prepared bounded KLayout/GDS-based shell LVS follow-up; copied config uses
MAGIC_EXT_USE_GDS true, because original DEF-based extraction would silently
ignore implant overlays. Stock macro abstraction unchanged and explicit.
Actual LEF/DEF intersection audit exactly reproduces NAND ground-spur and NOR
B-to-C pin short boxes; documents a concrete next access hypothesis if active
late-cost repair fails. Source/clock/RTL untouched. Python/YAML/shell checks
pass locally. Native37669731197 still active.

**Next independent preflight:** D-054 prepares native pin_access with fully
contained Metal1 via enclosures on the authenticated source. Exact standard
options reviewed against official docs/pinned API; tool10min/job15, no reroute.
Analysis result must be read for inaccessible pins before any long constrained
route. Existing native job untouched. Tcl/YAML/shell/whitespace checks pass.

**Native closure verified:**37669731197 succeeds26m53s. Downloaded reports
verify source3/bootstrap17 then7→3→3→0; fourth repair uses native stubborn
mode. Fresh DRC0, stock antenna nets/pins0 and critical disconnected0;
exact masters/placement/topology unchanged. Retained post-check ODB hash
9cac79d86dd15707efdd385c32d3990347cb4695874bc802d0bfe20a5e90e9ba verified.
Prepared D-055 fresh extraction/shell STA, measured filler policy and full
Magic/KLayout/GDS-based shell LVS on that exact route. Older-source Magic0
cannot be asserted as same-layout pass, so no skipped check or promotion.
Helper gains explicit fresh-source hash/provenance metadata; original source
mode stays default. Python AST/YAML/shell/whitespace checks pass locally.

**Latest failure audit:** pin-containment37673914480 fails DRT-0073 for
sg13cmos5l_nand4_1 A pins u_cfg.u_fsm._097_ and
u_cfg.g_col[0].u_col._24_; downloaded analysis log confirms no access.
Reject global containment hypothesis; no constrained reroute or waiver.
Older-layout GDS/LVS37673567925 also fails, but its report download was not
executed: automatic approval review hit an account usage limit, explicitly
a review failure rather than an unsafe-action judgment. Its exact failure
cause remains unknown; do not infer LVS counts or bypass the review.
Fresh same-layout verification37674839060 was active at the last successful
GitHub audit, alongside redundant older-layout Magic37674839230. Current
statuses cannot be refreshed while approval review is unavailable.
All scoped changes through33191e2 were pushed before that limit; these latest
evidence notes are local. No boxes ticked. Next: when review is available,
inspect fresh clean-layout checks and download the failed older-layout
report, cancel only redundant older Magic if still active, and repair the
specific remaining failure. Native0, older-source Magic0 and48 UART phase
cases remain separate verified results, not full combined acceptance.

## 2026-10-07 (session64: parallel diagnosis and independent board fix)
**Done:** user explicitly authorized agents; assigned two bounded independent
agents for primary-source routing research and fallback-compatible software
improvements, root handles fresh physical workflow. No heavy local EDA.
Whole-chip filler37662990606 fails strict non-pSD XOR guard before Magic;
this is not accepted DRC evidence. Retained log inspected. Added stable
instance list before master mutation and explicit per-layer delta diagnostics;
strict gate remains. Pushed4311509; diagnostic37663775123 active.

Independent board audit reproduces malformed chunk/unsigned fields/length
silently corrupting load transactions. Fixed BUG44 in MicroPython-compatible
board API with pre-I/O validation and boundary/no-I/O tests. Agent's venv
board+host317 tests pass in0.84s; reviewed source/tests/report. Existing unit
workflow will verify hosted. Frozen hardware unchanged.
Routing research finds database reload restarts optimization schedule rather
than resuming prior iteration53 costs. Exact pinned late-schedule APIs under
review; no identical route rerun or unverified acceptance claim.
**Boxes ticked:** none.
**Next:** read layer-delta report from full-chip trial, run verified targeted
late-schedule repair in cloud, check board hosted result and ongoing regressions.

**Parallel research/action:** verified pinned OpenROAD schedule and prepared
D-053 native late-cost bootstrap plus two late repair steps from original
3-marker iteration52, with exact topology/master/placement checks and a fresh
whole-chip native DRC gate. Pinned80minute hosted cap; downstream stock antenna/
critical disconnected gates retained; no geometry/timing claim. Tcl completeness,
Python AST, workflow YAML and shell syntax pass locally. Two agents completed;
no extra agent fan-out. Added source-linked border-config, failure-trace and
clock-phase/backpressure ideas to existing improvement roadmap; pending tests,
not accepted hardware changes or competitor rankings.

**Latest cloud evidence:** board unit37663965540 green on675a03c. Pushed
697499b/98c24b0/1731c08; late-cost native37668791436 active. Automatic approval
review initially timed out before executing the git command; one retry succeeds.
Whole-chip37663775123 verifies20714 replacements and empty non-pSD XOR, then
Magic hits30min cap with no report. Baseline stock check12m19s. Align scratch
Tcl with stock suspendall/selected-chip listall query, avoiding global catchup;
full rules unchanged,45min step/55min job bound. No DRC acceptance yet.
**Launch/status:**944ef1f/7bf9901/36f9527 pushed; stock-aligned whole-chip
Magic37669173193 active alongside late-route37668791436. Both use standard
cloud runners. Agent tasks complete; no further agent expansion. Official
OpenAI documentation confirms subagents can increase token usage; exact
account consumption is not available here. All authorized changes recorded.
**Fresh targeted result:**37668791436 fails correctly: source3, bootstrap17,
late guides7→3, fresh whole-chip3 and unchanged topology. Residual shorts are
shell_0489_/_0490_ and shell_0331_/VGND. Both late passes remained GUIDES
because effective; verified pinned FlexDRFlow transition then extended same
costs to at most6 alternating-offset steps, preserving80minute cap and all
gates. This reaches possible stubborn work without resetting the router.
**Current runs/user alert audit:**9bba1c1/cae28d7 pushed; revised late repair
37669731197 active, alongside selected-chip Magic37669173193. Latest efpga
and all-branch failure lists show no additional WARP failure beyond the two
already diagnosed; main gds-placement-route37557256170 is unrelated TRIPWIRE.
Recent standard checks pass or remain active. No final physical/timing claim.

## 2026-10-07 (session63: inspect fresh route failure and isolate filler remedy)
**Done:** checked newly failed37657068016 and downloaded artifact. Job32m09s,
router29m42s, exit2 because5 native routing violations, not timeout. Both
stubborn passes finish (~7m55s/~7m34s) without eliminating markers. Remaining
2 Metal2 shorts join shell_0489_/_0490_ near(59,474.2);3 Metal2 spacing markers
involve CRC r[29]/clock near(39.2–40.4,451.4–452.2). Antenna0/critical
disconnected0; geometry correctly skipped. Collector now retains checked final
ODB hash785a0afb8ab8e09e9c8db2c11dde54155aeba06f46979abd2599921d047be7f5,
not merely intermediate iteration17. No physical or configured timing pass.
Ordinary latest lint/docs/test/unit/capture queue green; fabric and frozen
G1 gds remain active. No identical route retry queued.

Verified gap37660478954 yields81 boxes at5/30nm and32 contact-spacing boxes
at300nm; gap-only policy rejected. Prepared D-052 wider pSD scratch clones
plus geometry-identical flattened control. Non-pSD layer XOR and unchanged
bbox/source hash assertions; full Magic controls, original positive invalid
fixture retained. Code in patches/, upstream unchanged. Python AST/YAML/shell
checks local; all EDA executes on standard hosted runners. Frozen hardware
and ongoing jobs unchanged.
**Boxes ticked:** none.
**Next:** inspect hosted flattened/pSD trial reports; select targeted routing
repair using remaining marker geometry rather than repeating identical cleanup.
Native all-check closure, whole-chip filler DRC/LVS and configured timing remain open.
**Launch:** scoped4b6dcb1/982f7da/fd7239c pushed; filler37662382228 active.
Final-view artifact hashes verified locally. No frozen-hardware push.

**Verified filler remedy on reproducer:**37662382228 completes successfully.
Downloaded reports verify both import modes: scratch fill1/fill2 isolated,
horizontal and both mirrored boundaries0; original ground pair17 and flattened
identical control17; invalid orientation retains findings. Geometry assertions
pass. Added pSD0.186/0.330um2 per cell; other layers/bboxes unchanged. Supports
physical abutment cause rather than tested hierarchy/import explanation.
Prepared manual whole-chip Magic diagnostic on authenticated no-decap GDS,
replacing exactly20714 filler references in scratch output and asserting all
non-pSD chip regions identical. Original source has3 native markers; whole
DRC/LVS/power/timing still unqualified. No frozen edits or rerouting.
**Cloud follow-up:** pushedd188de1/378b304/8b1a3d5/b265211; whole-chip
filler37662990606 active. Initial branch-only workflow dispatch404 required
a narrow efpga push trigger to register it; source artifact exists and name
confirmed. Latest failure audit still identifies37657068016 as freshest
failed efpga run. No acceptance gates relaxed.

## 2026-10-07 (session62: identify residual shorts and screen filler abutments)
**Done:** proactively checked hosted outcomes after user asked to continue.
Initial GitHub request stalled; retried with explicit network time limits.
Latest ordinary test37653829438/unit37653829463/lint37653829575/
docs37653829484 all green. Bounded route37652533986 fails at15minute native
step limit; geometry correctly skipped. Downloaded retained iteration15 ODB
hash714d957e71587ed63a2c256cc7016f632d048543370b0c0114ecb6acce3a75ac.
Native reports identify three Metal1 shorts at two locations: shell nets
_0489_/_0490_ near(59.38,474.065) and crc.r[29]/VGND near(39.775,450.370).
These agree with remaining LVS mismatch nets. Native count17→3 early,
then15minute cap interrupts iteration16 stubborn repair. Earlier successful
iteration53 took50m43s (35m14s was only90percent progress, corrected user
update). No zero-route recovery or new physical acceptance.

Isolated filler37653631748 reports five zero-error checks in full-style Magic
log: fill1/fill2/decap4/decap8/inverter. Individual report count fields empty
because Magic count prints instead of returning a value (BUG43); log plus
empty reason lists establish this limited result. It does not clear assembled
chip errors. Extended D-051 with tiny untouched-GDS horizontal/same-row/
mirrored-row filler fixtures generated by KLayout, named report markers and
returned reason-list flag. No PDK or fabricated geometry editing.

Prepared D-050 follow-up with authenticated retained source,17iterations and
80minute native cap so one stubborn pass can finish;120minute job cap.
DECAP_CELLS empty remains the only physical field change; original driver.
Added bounded live progress, stock native acceptance and geometry gates stay.
Python/YAML/Tcl completeness, source hash, five isolated zero log records and
whitespace checks pass locally. No heavy local EDA.
**Boxes ticked:** none.
**Next:** inspect hosted array diagnostics and longer bounded native cleanup;
retain final checked views and test whether repairing those shorts resolves
LVS12. Macro function, filler DRC and configured timing still need closure.

**Cloud launch/results:** pushed6a97584/e66e0be/0f0e67b; extended native
37657068016 active, filler arrays37657067983 complete. Horizontal and correctly
mirrored pair fixtures have empty findings; intentionally same-orientation
rows produce overlap/well/tap errors, including pSD.e/f with0.56x0.03um boxes
matching the dominant chip marker shape. This is a positive checker control,
not proof chip rows are wrongly oriented. Exact flow-script comparison also
finds stream-in differences: stock enables maskhints/readonly/noduplicates and
euclidean DRC. Refining array screen with matching settings, both maskhint
values as isolated diagnostic controls, and complementary mirrored ground
boundary fixtures. Turning hints off will not qualify production DRC. Added
explicit box-count calculation from returned reasons; shell syntax/order,
Python/Tcl checks pass locally. No frozen hardware or upstream edits.

**Reproduced ground-boundary failure:**37657638270 completes1m49s; exact
stock import flags enabled. Both fill1 and fill2 ground-sharing mirrored
pairs give17 boxes, all pSD.e/f; opposite mirrored boundary and horizontal
fixtures give0. Results identical with maskhints true/false. This reproduces
the dominant complete-chip thin-box geometry without signals or fabric and
rules out the tested maskhint toggle as a remedy. It does not certify the
entire6350-error cause or justify waiving the rule. Next screen fill4/fill8
at both mirrored boundaries before selecting a physical filler policy;
all nominal pitches checked against exact pinned LEF. Native37657068016
continues independently. Frozen hardware unchanged.

**Larger fillers/independent validation:**37658318703 completes2m01s. Fill4
and fill8 also give17 pSD.e/f boxes at mirrored ground boundaries,0 on the
opposite boundary/horizontal fixtures; isolated cells0. Both import controls
agree. Simple filler-width replacement is not supported. Next investigate
actual tap polygons and upstream interpretation using the now-small reproducer.
Prepared independent D-047 native UART coverage extension:28 TX and28 RX bytes
(zero/ones, alternating, walking-one/walking-zero, seeded random), real SPI
load, original timing and STOP checks. Also require RX FIFO empty after each
read. Same RTL/native/reset triplet, matched original-LUT control remains
available; netlists still function-only with unqualified physical views.
Python/YAML and whitespace checks pass locally. Hosted simulation only.

**User steering/independent fronts:** expanded native UART candidate
37659112021 runs; explicitly dispatched matched original-control37659171115,
queued behind candidate. Shared test edit also triggered known-failing original
hardened diagnostic37659111975; canceled this redundant run rather than spend
time reproducing unchanged BUG33. No gate/check weakened; its manual/automatic
workflow remains and original native acceptance is still unresolved.

Prepared separate frozen-G1 divide-by-eight capture image (six timestamp bits,
shift3, counter period512 clocks, conservative decoder max gap504, quantization8).
Existing verified prescaled image uses85/88 LC in37512249763; new fit unmeasured.
New bounded cloud workflow compiles/audits, runs source queue boundary check,
SPI-loads actual image and verifies FIFO/overflow/wrap/quantization/UART/reset/
STOP through existing top-port test. No new chip hardware or architecture.
Documents mark candidate pending; artifacts exclude raw bitstreams. Static
syntax checks only locally; cloud acceptance required before claiming usability.

**Native stress verified:**37659112021 mux_tree and37659171115 original_control
both pass RTL/native/native USER_RESET triplets. Downloaded manifests/XMLs and
actual simulator logs verify28 TX/28 RX bytes in all three cases per run,
no failure/error/skipped cases. This strengthens functional coverage without
establishing mux necessity, broader protocol coverage or new physical timing.
Extended capture37659595436 now green; artifact verification next. Bounded
route37657068016 still native-active at latest check. Prepared read-only
ground-boundary polygon export and5/30/300nm synthetic row-gap controls;
no real chip row spacing changed, and new spacing/abutment failures remain
acceptance failures to diagnose. Syntax checks pass locally.

**Capture verified:** downloaded37659595436: strict source queue and loaded
XMLs each one passing case/no failure/error/skip. Compiled/audited shift3
image uses86/88LCs versus85/88 for shift2 in37512249763; same frozen hardware.
Counter period512 clocks/eight-clock quantization; decoder known max gap504.
Updated README/report/claims with scope and evidence. Latest lint37659595251/
docs37659595258/test37659595277/unit37659595335/capture queue37659595221 green;
fabric37659595241 and frozen-design gds37659595229 active. No phase boxes
ticked. Next inspect native repair and synthetic gap/polygon reports, then
choose a physically validated remedy for the reproduced filler boundary.

## 2026-10-07 (session61: short electrical screen while physical checks run)
**Done:** proactively inspected corrected geometry37648945387, still active.
Explained that this replay skips detailed routing; previous physical-only job
27m34s, not another3h route. Latest capture queue37650210884/lint37650210869/
docs37650210907/test37650210872 pass; fabric37650210874 and unit37650210862
still active at initial check. No new hardware acceptance claimed.

Prepared D-049 short cloud same-wire slow-corner driver screen: original
a21oi_1 versus a21oi_2 at measured frame_idx[0] hotspot, no saved modified DB,
placement/routing, forced configuration or frozen edits. Require exact baseline
nine-pin reproduction; preserve driver connections and record old wire/input
hashes plus before/after electrical/path/annotation reports. Macro black-boxed;
results cannot sign off new layout or configured fabric. Official PDK gate
networks match and LEF area delta5.4432um2 before any physical repairs. Python,
YAML, Tcl completeness, PDK gate-network and whitespace checks pass locally;
no EDA executed. Initial local syntax-check snippet was corrected; system
Tcl executable absent, so used venv tkinter's Tcl parser without tool execution.
**Boxes ticked:** none.
**Next:** inspect physical outcome and short electrical-screen setup/result;
measure one useful correction before spending hours on a fresh route. Retain
frozen G1 and proactive full-workflow checks.

**Verified cloud follow-up:** caught corrected geometry37648945387 failure
before user reminder and downloaded exact views. Actual0decaps/20714plain
fillers; KLayout248→0, LVS75→12, Magic6350 (all pSD.e). Job18m02s. Remaining
LVS has equal3530device counts, two fewer extracted nets and four extra signal
pin incidences on ground. Saved source still3markers; residual shorts remain
hypothesis. No full physical or timing pass.

Short screen37651173629 succeeds and downloaded reports reproduce9baseline
slew pins; a21oi_2 same-old-wire substitution gives0slew violations,33fanout
violations remain. Conditional slow shell estimate only, no physical DB saved
or resize promoted. Ordinary lint37651173562/docs37651173593/test37651173588/
unit37651173601 green; fabric37650210874 active at check. User requests periodic
monitoring again; checked all workflows repeatedly and explained exact failure
versus concrete improvements.

Prepared D-050 bounded route finish: original driver, authenticated iter52,
16iterations/15minute native-stage cap, stock native acceptance before no-decap
geometry/LVS, corrected final-view retention. Record Magic separately; cannot
claim all geometry zero when it fails. Syntax/YAML/whitespace checks pass; cloud
verification pending. Next is retained native0/LVS result and Magic pSD.e
analysis, then matching new native physical views and configured timing.

**Further proactive checks:** D-050 cloud37652533986 is active in bounded
native cleanup. Latest lint37652533997/test37652534156/docs37652533791/
unit37652533933 and fabric37650210874 all pass. No failing routine workflow
left in this checked group. Continue monitoring the physical experiment.

Read-only6350 Magic polygon-box association:6346 fill2-only,2 fill1/fill2,
2 fill1-only; none inside macro bounds. Exact pinned KLayout pSD symlink target
implements only pSD.c1, confirmed by execution log. KLayout0 does not clear
Magic pSD.e/f; no false-positive assertion or rule waiver. Prepared D-051
bounded isolated full-style Magic filler/library screen, no local EDA or
hardware change. YAML/Tcl completeness and whitespace checks pass. Next:
inspect bounded route outcome and isolated-cell reports, then reproduce row
boundaries if isolated library cells pass. All phase boxes remain open.

**Launched:** isolated filler screen37653631748 on pushed d3cb8bb; pinned
inputs complete and Magic step active. Bounded route37652533986 remains in
native step at last check. New lint37653631265/docs37653631444 pass;
test37653631384/unit37653631641 active. Prior complete set is green. Scoped
diagnostic/CI/docs commits c849dd8/be34ac9/d3cb8bb pushed under standing user
authorization; frozen hardware push-path audit empty. Upstream issue search
found no exact pSD.e match; no root-cause claim beyond measured localization
and confirmed checker coverage. Next inspect both cloud artifacts, including
native timeout/failure evidence if cleanup cannot reach zero in its budget.

## 2026-10-07 (session60: verified reset control, corrected filler experiment, host improvements)
**Done:** proactively inspected all latest workflows. Original-LUT matched
control37553979644 passes RTL/native UART/native USER_RESET; downloaded and
strictly parsed all3 XMLs, one case each/no failure/error/skip. Both regenerated
mappings pass, so mux-tree-only attribution remains unsupported. Latest
ordinary docs37554066409/lint37554066460/test37554066619/unit37554066461 green.

Physical replay37552604692 fails after27m34s: KLayout248/LVS75, but actual
post-fill DEF still has5667 decaps plus1095 plain fillers. DECAP_CELLS remained
active when FILL_CELLS was edited (BUG41); no-decap hypothesis was not tested.
Corrected one copied config field to DECAP_CELLS=[], added actual filler
inventory gate before long checks, and corrected metric extraction from
completed tool states when deferred checkers omit their state_out. Syntax,
exact failed-run DEF count and248/75 parser checks pass; corrected hosted run
pending. Frozen G1/src/arch/macro/info/PDK unchanged; no heavy local EDA.
**Boxes ticked:** none. Compact physical/configured timing remain open.
**Next:** inspect corrected inventory/DRC/LVS; improve fallback-compatible host
trace tools and loading validation while cloud checks run.

**Independent progress:** added host capture decoder with explicit maximum-gap
assumptions, wrap/quantization interval bounds, overflow/mixed-byte rejection,
and documented CLI for both capture variants. Added checked CH_READ parsing
(valid zero versus empty, malformed/out-of-state rejection). Fixed negative
chunk and word/architecture truncation validation (BUG42). All31 lightweight
host tests pass in0.49s; CLI examples/overflow exit and whitespace checks pass.
No EDA or hardware/bitstream format change. Cloud regression follows push.

**Electrical diagnosis:** exact replay netlist/report audit binds all9 slow
slew pins to frame_idx[0], driven by a21oi_1 u_cfg._54_; worst2.562529ns versus
2.507400ns limit. The report also has33 fanout violations. Retained ignored
hash-bound summary; documented one-driver/local-buffer screen and costs, no
hardware change or timing fix claimed. Updated phase5 summary/roadmap. Corrected
geometry37648945387 remains active; at b8922e9 lint37648945437/docs37648945446/
test37648945505/unit37648945403 green. Explicitly answered user: complete timing
has not passed; router0 is distinct from failed DRC/LVS and macro-black-boxed
shell timing. Next is corrected physical outcome and hosted host-tool tests.

## 2026-10-06 (session59: matched synthesis control and final evidence retention)
**Done:** proactively checked cloud workflows. Native mux-tree37552796495 and
tracked-patch37553037381 pass RTL control and actual SPI-loaded native UART.
Matched original-LUT resynthesis37553190074 also passes: the mux change alone
cannot explain the correction. Downloaded control manifest and simulation log
verify original_control,842 loaded words,UART TX/RX/STOP and one passing case.
The original hardened native netlists still fail. Both regenerated variants
have unqualified copied physical views; no compact physical/timing promotion.
Official LibreLane synthesis documentation confirms different ABC strategies;
AREA2 versus this helper's default ABC is a candidate difference, not a cause.

Extended the candidate cloud check with real USER_RESET acceptance, explicit XML
retention and all regenerated tile netlists. Fixed BUG40 collector to preserve
views referenced by each flow's final completed state, metrics/hashes and full
KLayout marker databases, independently of intermediate snapshots. Synthetic
regression retains final0 ODB alongside an old3-marker snapshot. Python/YAML and
whitespace checks pass. Collector/workflow-only edits no longer automatically
start another hours-long compact route; manual dispatch remains available.
No frozen src/arch/macro/info edits or heavy local EDA. Existing filler-only
geometry/LVS37552604692 continues with unchanged inputs.

**Boxes ticked:** none. At5da3b4b ordinary docs37553190167/lint37553190070/
test37553190069/unit37553190205 all green. Cancelled pending push37553190274
is not a failed candidate; manual control37553190074 succeeds.
**Next:** inspect plain-filler DRC/LVS and extended native reset results;
isolate mapping differences and obtain matching hardened views before any
promotion. Keep checking all workflow results without user reminders.

**Verified follow-up:**37553717299 passes all three expanded tests. Downloaded
and strictly parsed rtl_control/native_candidate/native_user_reset XMLs, each
one case and no failure/error/skip. Five retained native netlists match manifest
hashes; static inventory preserves529 configuration latches/eight user flops
per LUT tile type, original source hashes unchanged. This is not equivalence,
full loaded-bit audit, matching geometry or SDF timing. Original-LUT reset
control37553979644 active; physical replay37552604692 still active. Ordinary
lint37553717429/docs37553717453/test37553717308 pass, unit37553717264 pending.
Pushed scoped fixes through4b55b28; final evidence note follows as docs only.

## 2026-10-06 (session58: routing closes; physical checks become the blocker)
**Done:** proactively inspected outstanding cloud jobs.37516794406 completes: native route exit0, iteration53 reaches0markers after2h47m15s router elapsed; antenna nets/pins0, critical disconnected pins0 (7 noncritical). Whole route/geometry job19:09:17–22:25:22UTC takes3h16m05s and fails later geometry: KLayout248 (M1.a1/M1.b247), Magic1828, LVS67 (63 net differences,1 unmatched net,3 unmatched pins). LVS shows power-net mismatches; cause unproven. Extracted shell setup+12.251343397653367ns/hold+0.12463458395889776ns at20ns, but9 slow-corner slew violations and macro black-boxed: no complete timing pass. Frozen G1 unchanged; compact not promoted.

Native37536118708 still fails UART; optional SAT stops importing an unused Liberty cell lacking an output function. Skip incomplete cells at import and require hierarchy-check for all instantiated cells.37545251399 passes import but setup stops because cleanup removes captured aliases; preserve those wires.37545630704 then reaches SAT with feasible counterexamples, but static audit finds missing constraints:529 actual configuration latches versus505 named ConfigMem.Q aliases (24 latch outputs renamed; one of530 logical bits merged). Name-subset constraints leave LUT selectors arbitrary, so these counterexamples do not prove a hardware fault. Capture every actual dlhq latch output and preserve its Q wire; hosted37546145073 pending. Earlier8707 matching-bit audit covers the named FrameMem subset, not every surviving configuration-latch output. Syntax/cell/schema audits pass; no native-function pass.

Read-only physical inventory37545539269 succeeds with exact hosted Docker digest and iteration52 ODB SHA33dceb8d52df9d5ea8cc3741b71b9b3e1e79ae4fb95b1eb559b3ca3eb40390bc. It has3markers, not the final zero-route database. Width-error location x31.005–31.055/y704.655–704.815 contains no pre-fill cell. Later flow inserts6762 fillers; investigating filler/rail interactions is a hypothesis. Added separate bounded geometry replay37545941476 from that saved database, with no routing or hardware change. Retain marker databases and physical views this time; original collector omitted final zero-route ODB and KLayout coordinates. Replay cannot certify final routing/timing. No heavy local EDA. Initial automatic approval review times out; permitted retry succeeds, no remaining blocker.
**Boxes ticked:** none. Ordinary lint/unit/test/docs at3a9b81c green (37536223863/37536223833/37536224076/37536223838).
**Next:** inspect replay Metal1 marker coordinates and all-latch SAT result, then select one measured correction. Preserve frozen G1 and continue proactive full-workflow checks.

**Verified proof:**37546145073 captures529 actual latch Q values for each target and proves all three constant outputs with feasibility checks passed. Actual native UART remains failed. This establishes local false-X behavior under captured configuration, not complete sequential/function/timing closure. D-047 standalone five-PDK-mux4 LUT experiment added: all-input/configuration binary equivalence against pinned FABulous LUTK and2916 partial-input cases against independent truth-table completion. Static Python/YAML/whitespace checks pass; hosted candidate verification pending. Candidate stays in spikes; frozen/generated/upstream/chip RTL and active geometry inputs unchanged. No area or equal-area benefit claim.

**Concrete correction candidates:**37546784325 passes candidate binary equivalence for all configurations/inputs and2916 partial-input simulations using actual pinned PDK models (logs downloaded/verified).37546984612 verifies all9164 actual configuration latches known/image-matching both before RUN and at4423490ns; native UART still fails. Complete audit follows actual latch D/GATE through frame buffers, rather than relying on ConfigMem names. Static frame bindings cover all22 tile types.

37545941476 completes geometry replay and reproduces248 KLayout errors. Exact marker/DEF/LEF join associates all248 with inserted decap fillers:241 decap8-only,3 decap4-only,2 decap4/8 boundaries and2 decap/fill2 boundaries. D-048 tests only FILL_CELLS=plain fill1/fill2 on the same saved3-marker ODB, with LVS added;37552604692 pending. New filled ODB b0736851fd5324f1aa619e70eeb9706476ed9bd70a84883861e114c6b40bda21 retained with GDS and marker coordinates, but it is not the missing final0-route ODB.

D-047 integration candidate37552796495 regenerates scratch LUT tile netlists and tests actual UART loaded through SPI against original RTL control. Copied physical views are deliberately unqualified for regenerated netlists. Upstream substitution is recorded in patches/fabulous_lut_mux_tree.patch, applied to separate output; exact patch/static checks preserve originals. No local EDA, new route, frozen chip edit, configuration tie-off or output mask. Next is the native candidate result and plain-filler DRC/LVS outcome, then one measured correction/promotion review only after remaining gates.

## 2026-10-06 (session57: matched-input LUT diagnosis)
**Done:** inspected hosted37534251857. Setup, RTL control and companion loading execute; actual native UART/reset probes still fail. At4423490ns,49 tile output ports differ on RTL-known bits even with actual native tile input ports shared. Independent internal state can differ, so this is not local equivalence or proof of harmless simulation pessimism. Added read-only snapshots of the same-input TB timer controls/state/config and24 LUT cells in the timer/UART upstream tiles. Enumerate every binary completion of each partially unknown LUT index to report possible combinational outputs, alongside RTL/native state and retained native output aliases. No mapped model, hardware, configuration or user state changed. Lightweight truth-table/index/unknown checks, Python syntax and whitespace pass; hosted37534707478 active at7f5442a. Route37516794406 remains active with unchanged inputs and no final violation/timing result.

Reviewed Piper/Vimjam's DVCon X-propagation paper: RTL conditional optimism and netlist reconvergence pessimism both matter. Passing RTL alone cannot choose between them. Recorded the distinction and next acceptance evidence in the diagnostic report. No heavy local EDA or new routing run.
**Boxes ticked:** none. Native acceptance, final compact geometry, configured-fabric timing and phase5 remain open.
**Next:** inspect the focused cloud snapshots; identify a combinational discrepancy under known configuration or a control/reset uncertainty requiring correction. Keep frozen G1 and active routing unchanged.

**Focused probe correction:**37534707478 passes RTL control but stops before RUN in the new optional-alias probe, not at the later UART failure. Native LUT_out aliases are removed; indexed cocotb lookup raises KeyError while the handler expects AttributeError (BUG37). Switched to existing attribute-lookup convention and checked retained/removed behavior with a fake handle. The snapshot attempt supplies no new native UART result. Corrected hosted rerun pending.

**Focused result:**37535155011 verifies the alias correction and reaches actual native UART X. At4423490ns, same-input timer count15/rst0/loadX/halfX/en0: RTL conditional semantics retain count, which alone is not evidence of deterministic hardware behavior. Several unregistered LUTs have singleton binary outputs yet native O=X: X1Y2 LD INIT all0; X2Y1 LB INIT all0 and LD INIT all1; X2Y3 LD index x001/INIT0000101000001010 yields1. Configuration and internal mapped input binding still require direct cone analysis before assigning a cause. Added read-only selected constant-output cones at this instant; hosted next run pending at28e71b3. No simulation output replacement or model/hardware fix. Static audit of the exact cached PDK mux UDPs checks27 mux2 and729 mux4 partial-input patterns against binary completion; all match, excluding a simple missing mux-table rule as the explanation. This is a local static audit, not native-chip verification.

**Next proof / CI audit:** proactively inspected37535581139 as soon as it completed: actual UART still fails, constant-output traces execute without probe exceptions. Added cloud-only bounded combinational SAT checks for the three all0/all1 LUTs, using actual mapped netlists and functional Liberty, captured native configuration-Q constraints, arbitrary tile inputs and cut user state. Require a feasible model before accepting any constant proof. Each target has60-second process cap; native simulation failure still governs workflow result. Snapshot writes only to ignored simulation output. Static script/constraint/result-parser tests and syntax checks pass; hosted proof verification pending at17cc085. User requests workflow monitoring without reminders; audited all recent workflows and failed-run list: completed ordinary lint/unit/test/docs green, recent reds are native diagnostics and already corrected experimental setup issues. Continue checking all workflow names after pushes and before deciding each iteration, classify setup failures separately, and inspect artifacts promptly. Active route remains untouched; no native, physical or timing promotion.

**Current hosted job:**37536118708 runs the captured-configuration proof at17cc085. Latest completed standard suite at1c0c3ee is green: lint37535643048/test37535642981/docs37535643063/unit37535642959. Next step is its proof artifacts and current route37516794406, which remains active without a final count.

## 2026-10-06 (session56: loaded RTL companion for native diagnosis)
**Done:**37532673220 still fails actual native UART; unknown-select filtering removes a false selector branch but timer input trace still reaches160-node cap in neighboring routing loops. Configuration audit remains8707known/matching bits immediately before timer corruption. Regular lint37532673267/docs37532673461/test37532673177/unit37532673160 pass. Route37516794406 remains active with unchanged inputs.

Added diagnostic RTL companion beside actual mapped fabric. All73 generated/primitive source files are copied into ignored simulation output;80 module names are renamed to avoid collisions, originals unchanged. Companion inputs share actual shell/configuration ports, output ports are unconnected, and its own configuration loads through those real inputs. It receives the ordinary RTL-control D-023 routing pulse; configuration/user storage are never forced. Native output still decides the test result. Compare timer reset/load/half/enable/state and selected tile route vectors at identical observation times. This changes the diagnosis from long post-corruption cones to direct RTL/native boundary comparisons; no timing/SDF proof or hardware correction claimed. Python/YAML/whitespace and complete22-tile source/unique-module/input-connection static audits pass; hosted compile/load verification pending.
**Boxes ticked:** none. Native/physical/configured-fabric timing and phase5 gates remain open.
**Next:** inspect same-load companion/native differences and identify the first relevant input/mapping discrepancy; keep existing route and frozen G1 unchanged.

**Companion result:**37533766076 successfully compiles/loads companion and native fabric. At4423490ns companion timer count15/rst0/load1/half0/en0, while actual native timer D isX; next edge companion counter stays15 while native counter goesX. Selected route vectors diverge (native unknown where whole-RTL copy is known), including idle after-RUN samples. This does not isolate a local gate because whole-copy incoming routes differ. Added per-tile RTL companions connected to each actual mapped tile's input ports, with outputs unconnected; report RTL-known versus mapped-unknown/opposite bits on data outputs. Independent configuration/storage remains driven by real frame inputs. Static full-source/connection checks pass; hosted matched-input result pending. No native pass, four-state root-cause proof or hardware correction yet.

## 2026-10-06 (session55: first timer corruption investigation)
**Done:** Inspected37522773342: actual native failure persists; TB timer is unknown before RUN, resets to configured15/armed1 after RUN, then all sixteen counter bits become unknown while armed stays1 by UART failure. Counter-D cone mostly reaches counter feedback, so sampling only at UART failure cannot identify the original corruption. Added bounded read-only first-known-to-X watcher: captures stable falling-edge counter/D/reset inputs and rising-edge settled state, then traces runtime at the first corrupt edge. Verified all sixteen mapped flop D/RESET_B/CLK bindings, Python syntax and whitespace; hosted verification pending. Standard lint37522773332/test37522773372/docs37522773357/unit37522773331 all pass. Routing37516794406 remains active and its inputs are unchanged; no fresh final route count. No local heavy computation or hardware/model/config/state force changes.
**First-corrupt-edge result:**37523544565 identifies4423500ns: stable pre-edge counter15, all sixteen D inputs alreadyX, all RESET_B pins1; rising-edge counter becomesX. This identifies prior unknown data rather than a known-data sample failure at this edge, without proving the ultimate cause. Next read-only snapshot traces at the preceding falling edge while counter is known; configuration is re-audited against the loaded image at that instant. Added controlling-input sensitivity for actual a221oi gate used in timer D cone. Static gate-schema/control tests pass; next hosted verification pending.
**Pre-corruption result:**37523983755 captures4423490ns (ten ns before corrupt clock), counter15/D allX/reset pins1. Re-audit confirms8707known image-matching configuration bits at that instant, narrowing this observed fault away from changed configuration. Control cone spans neighboring logic and reaches160-node cap; truth-table muxes with repeated data unnecessarily trace irrelevant unknown select pins. Extended conservative Boolean sensitivity to unknown mux selects, without assigning unknown inputs or changing simulation. Synthetic partial-select/repeated-data tests pass; next hosted trace pending. Artifact transfer initially times out, then automatic approval review times out; allowed single retry succeeds, no unresolved approval blocker.
**Boxes ticked:** none. Native/physical/configured-fabric timing and phase5 gates remain open.
**Next:** inspect first corrupt timer edge and upstream data/control cone; select a correction from observed evidence, keep G1 and active route unchanged.

## 2026-10-06 (session54: persistent native unknown and cross-tile diagnosis)
**Done:** Inspected new failed workflow37519661148 at7a7148b. RTL control passes; native UART X persists at4423540ns both at sampled clock edge and after delta-cycle settling. Exact selected UART path reaches Tile_X6Y2 E2END[7]; this is a neighboring route, not an established unconnected net. Added read-only traversal across exact macro/tile connectivity, excluding known unselected mux branches and stopping at clocked state. Whole-fabric JSON comes from actual mapped netlists and pinned Liberty with no remapping; compressed connectivity retained as cloud evidence. Synthetic mux/vector boundary/state-stop checks and Python/YAML/whitespace checks pass. Hosted verification pending. No local heavy EDA, model/config/state forcing, frozen hardware or active route changes.

G1 physical37511778153 completes success, including gds/precheck/viewer/gl_test. This remains the template's mapped-shell/RTL-fabric scope (D-023), not compact native/SDF proof. At7a7148b, lint37519661090/docs37519661032/test37519661002/unit37519661006 all pass. Compact route37516794406 remains active; no final count or timing result available.
**Independent improvement:** added user-design top-port queue boundary test for full simultaneous pop/event (old head delivered, new event accepted, order retained, no overflow) and empty ready/event (new event retained). Separate bounded hosted workflow runs six-bit timestamps with shifts0/2; no hardware or active routing input changes. Python/YAML/whitespace static checks pass; source simulation pending, no new loaded/native/timing claim.
**Hosted results:** cross-tile37520760969 successfully parses exact mapped fabric and reaches failing native tests. UART path spans columns6→5→4→3→2. Known controlling inputs mask some unknown AOI/OAI branches, but generic traversal followed those branches first and hit160-node cap; added conservative Boolean-sensitivity filtering for supported basic/AOI/OAI gates. Synthetic controlling-input assertions pass; next hosted trace pending. Independent queue37520971978 passes shifts0/2; downloaded XMLs each have one test and no failure/error/skip. This closes the previously unisolated source-RTL full pop/push coverage gap without claiming new native/physical success. Route37516794406 remains active.
**Diagnostic correction:**37521273371 passes RTL control but sensitivity probe stops before RUN with wrong nor2b input name (BUG36), not a fresh UART result. Corrected against pinned PDK A/B_N interface; static audit checks every distinct gate interface in actual fabric plus NOR controlling-input masks. Hosted rerun pending. Queue37521273411 also passes; latest lint/docs/test pass, unit/fabric still running.
**Active source isolated:** corrected37521660597 passes setup/RTL control and reaches actual native UART failure22.45s. Same settled X at4423540ns. Boolean-filtered cone now ends after41unknown nodes at Tile_X2Y3_LUT4x8_ha_C2.Inst_LH_FABULOUS_LC.LUT_flop, D=X/RESET_B=1 at sampled failure. No cap hit or setup exception. Added targeted read-only data/reset traces and configuration selectors for this exact UART source register at pre/post RUN and failure. No hardware correction is yet justified; next hosted source probe pending.
**Register input result:**37522095175 completes failing native tests. UART source Q is unknown before RUN but D is known, becomes1 at after-RUN, then becomesX at4423540ns. Configuration selects its registered output/reset value1. D cone reaches unknown TB timer counter bits and own state feedback; reset pin is known. Added read-only TB timer reset/load/half/enable/config/state snapshots to distinguish reset/loading/control corruption at the same samples. Hosted validation pending. Routing37516794406 still active46minutes after job start at19:55:17UTC; documented prior compact132–175minute failed attempts and300-minute step cap as durations, not an ETA to zero. No active inputs or frozen hardware changed.
**Timer probe refinement:** static actual-netlist audit finds primitive port/reload aliases were removed and count was scalarized. Initial optional probe would skip missing aliases; switched to preserved sixteen counter bits/armed state and actual count0/armed D-input cones. These exact state aliases/driver ports are verified against archived mapped connectivity before push. No inferred port bindings or new hardware result.
**Boxes ticked:** none. Compact native/routing/timing acceptance and phase5 remain open.
**Next:** inspect cross-tile first-failure cone, identify the earliest active unknown source before selecting a hardware/model correction; continue independent fallback-compatible improvements and preserve current routing inputs.

## 2026-10-06 (session53: approved checkpoint publication and cloud diagnosis)
**Done:** User explicitly approves public experimental checkpoint upload after contents/purpose explained. Initial network error, then short target SHA rejected; full a284f4c SHA publishes exact5676972-byte asset under compact-checkpoint-20261006-iter8, same pinned SHA256. Earlier automatic approval blocker is resolved, no further publication permission needed. Restarted only failed jobs of37512885358 (attempt2); both verify/materialize checkpoint and fetch exact PDK, four G1 demos remain passed. Existing G1 fabric37511778167 passes; G1 gds37511778153 still running.

Actual tighter RTL-control UART passes. Mapped-fabric test fails15.39s with UART X:8707bits known/matching and26944 stable CRC cycles, selected user flops unknown before RUN. BUG33 records unresolved native/reset/zero-delay distinction. Route fails before OpenROAD with non-TTY Docker input: eager flag ordering error in our driver (BUG32), verified against pinned LibreLane CLI source. Fixed order and added bounded live route progress. Added read-only actual-tile cone parsing with Yosys and a separately labeled real-host USER_RESET probe; ordinary native failure remains required and cannot be overridden. No PDK/upstream/hardware/config/user-state changes or local heavy computation. Python/YAML/whitespace static checks pass; hosted verification pending.
**Next cloud iteration:** pushed4a10f7f/c26f520, run37516278474. Docker no-TTY ordering is verified fixed; route now rejects nonexistent force-run-dir before OpenROAD (BUG34). Create fresh empty run directories before CLI. New native cone parser rejects unsupported PDK Verilog specify syntax in distribution Yosys (BUG35); switch only port extraction to pinned Liberty, leaving simulation cell models unchanged. RTL control again passes; actual native test is not reached in this attempt. Both failures diagnosed from small cloud artifacts, no local EDA. Next hosted fix verification pending.
**Verified follow-up:**37516794406 at1784a49 passes the corrected Liberty cone extraction and RTL control. Actual native UART fails18.81s; separate real USER_RESET probe also fails19.12s. Configuration remains8707 known/matching bits. Read-only cone reaches neighboring tile inputs; a tile-local input boundary is not proof of an undriven whole-chip net. Current route passes directory validation and remains in its routing step; no fresh final count or timing result yet. Four G1 demos pass again. G1 gds/precheck/viewer37511778153 pass; gl_test still running. Latest lint37516794249/docs37516794365/test37516794224/unit37516794383 pass.

Narrowed diagnostics to known mux-selected branches; added actual UART_TX output cone at Tile_X6Y2_E_IO4_wide.B_IN_top. Independent native-only workflow reuses strict baseline/reset checks and pinned inputs, without enqueueing another routing run or touching active routing inputs. Python/YAML parsing and lightweight synthetic mux2/mux4 traversal assertions pass; actual cloud verification pending. No upstream, hardware, PDK model or signal-force changes.
**Output-path result:** independent37519060510 at21a2466 completes actual RTL/native/reset tests. RTL passes; native24.76s fails, reset probe also fails. UART output cone is unknown before RUN (selected E2END[7]), known at after-RUN and after-USER_RESET samples, then recording encounters X at4423540ns (4060ns after after-RUN sample). This narrows when to observe, without proving a hardware or simulator root cause. Added read-only runtime/cone snapshots at first failing UART sample and after same-edge delta-cycle settling, retaining original failure. Next native-only verification pending; routing37516794406 remains active and untouched. Lint37519060376/docs37519060419/test37519060377 pass; unit still active.
**Boxes ticked:** none. Native function, final routing/physical checks, configured-fabric timing and phase5 acceptance remain open.
**Next:** inspect independent UART output cone and current routing artifacts; use measured active-path/reset evidence for one isolated correction. Retain frozen G1.

## 2026-10-06 (session52: routing root causes, hosted migration and authorized commits)
**Done:** Read current plans, evidence and failed runs before changing experiments. Ground-up exact ODB/marker audit identifies west-channel pin escape/local density conflicts;144 final markers cluster near tiny NOR/CRC/clock pins. Local row-bin occupancy reaches97.86%;0global overflow is insufficient. D-044 warm restart saves15markers at completed iteration8, without final repair/checkers; local process no longer visible after steering. Packaged that exact checkpoint and122 hashed inputs into5.41MiB experimental asset (SHA256 `6e2bac339e810a09dc9084393cadc3da5cdfb596077c05410c3b30b5e15ecb4d`). D-045 larger-NOR backup preserves connectivity/legal placement,0GRT overflow, and actual mapped-shell/RTL-fabric SPI UART passes58.69s; not full routed or selected. Fixed bare-DB sizing setup by loading Liberty (BUG30).

Assessed acceptance gaps: baseline extracted shell slow setup+12.418807667ns/fast hold+0.144112337ns at20ns, macro black-boxed; configured-fabric timing remains open. Earlier original-compact native UART fails despite8707 matching configuration bits; tighter native experiment is separate. Documented ordered closure plan, fallback-compatible improvements and primary-source research on Loom, STT, Tempo, Sophos and mcranny. No competitor code copied, no performance comparison claimed.

Added separate hosted `compact experiments` workflow: bounded stock route then physical checks if native zero, real SPI RTL-control/native mapped-fabric probe, and four freshly compiled/audited G1 software demos. Standard public runners, no local heavy EDA, no paid/larger resources. Template jobs/frozen hardware/upstream/main unchanged. Experimental checkpoint is a release asset; ignored build logs/databases are not committed. Python/shell/YAML/runner-limit checks and complete122-file integrity/materialization pass. Cloud results pending at this entry; no phase boxes ticked.

User explicitly authorizes grouped commits/push this session. First five commits: baacee3 compiler validation/provenance,0434a2a soft monitoring/capture,1698103 loaded tests/diagnostics,90177d4 timing audit/compiler experiments,650163a compact routing helpers. Remaining CI/docs groups and push are performed after final review; actual remote run IDs will be recorded below.
**Remote follow-up:** seven scoped commits pushed through a284f4c. Hosted compact experiments37511778394; lint37511778680, docs37511778312 and idle-chip test37511778469 pass. Unit pytest job passes; other jobs still pending/running. Fresh hosted monitor compile/audit/loaded RTL passes22.72s; fault compile fails because the new cloud driver omitted uart_monitor_top.v (BUG31), corrected in a follow-up CI commit. No four-demo pass yet. Automatic approval review rejects publishing the generated checkpoint asset because public egress/licensing scope was not established. Inventory audit finds122 explicit design files, no credential/key/token patterns in text inputs; explicit upload approval requested asynchronously. Routing/native jobs cannot start EDA until their asset exists. No local heavy run launched.
Additional primary-paper review: Kahng et al. pin-access-driven placement refinement motivates legal local mirroring/site shifts against exact access geometry, not density-only padding; linked in acceptance plan. First compact workflow completes failed: native/route fail before EDA because checkpoint asset is unpublished, not a new routing result. Corrected hosted run37512249763 is active; public asset approval still pending.
**Verified iteration:** corrected run37512249763 passes the g1_demos job: fresh compile/audit plus real SPI-loaded RTL monitor21.8674s, fault19.9550s, capture24.7824s and prescaled24.9997s. Downloaded17KB artifact; four independent XMLs have exactly one case and no failure/error/skip. BUG31 closed by this evidence. Unit37511778471 also passes. Both native/route attempts fail before EDA at absent asset, not at hardware checks. Added explicit blocked-before-EDA metadata/error to the harness; static Python/shell/whitespace checks pass. Full evidence in `docs/reports/hosted_experiments_20261006.md`. User asks to inspect failures and keep iterating; checked all recent efpga runs, no additional completed hardware failure found. Public checkpoint approval still pending; no indirect upload or local heavy EDA attempted.
**Additional workflow review:** checked latest35runs plus failure-filtered history across both branches. Older main/TRIPWIRE critical-branch37380322860 fails missing awk in its custom wrapper; L3 hotspot37375683211 fails missing PL_OPTIMIZE_MIRRORING config key; main unit37375675116 RTL job is canceled. Downloaded only254KB of plain logs/read annotations, no main edits. At pushed WARP4146abd, test37512885377, lint37512885326, docs37512885423 and unit37512885345 all pass. Compact37512885358 is in progress with asset precondition still blocked; corrected four-demo pass remains37512249763. No routing/native EDA started, no local heavy compute, no approval bypass.
**Boxes ticked:** none. Compact routing, native functionality, configured-fabric timing, clean reproduction and phase5 gates remain open.
**Next:** inspect hosted setup/results, fix failures without heavy local EDA, preserve exact completed routing evidence; select one geometry-driven fix only if the unchanged-hardware route does not close. Retain G1 until every successor acceptance gate passes.

## 2026-10-06 (session51: completed route results and native-fabric cone diagnosis)
**Done:** Read completed D-041 stock restart:101→198→258markers across three DRT passes,0final antenna nets/pins, routing checker failure. Wall times66m00s+43m58s+64m53s=174m51s. Stopped later incompatible Magic via owning exec session35059; all reports retained. Native258-marker summary and exact control-net endpoint audit saved under tighter root (`diodes_final258_summary_20261006.json`, `diodes_final_control_audit_20261006.log`). All258west; final hotspot y250–350µm. RX-byte branch and RX-empty distribution are implicated; no claim of a proven buffering fix. Reported shell STA setup/hold counts0with black-boxed macro, not whole-fabric timing signoff. The144-marker baseline remains best completed compact result; D-041 not selected.

D-043 bounded CRC padding completes3477versus3482baseline after2iterations, first iteration4105versus3441worse;13m22s elapsed. Five fewer early markers do not justify full hardening. Summary `padding_iter2_summary_20261006.json`; no full route launched. D-042 higher-clock-layer screen also remains rejected. Completed results, durations and limits recorded in route report/decision/physical-flow docs. No compact full route remains active.

Corrected copied scratch probe config's wrapper path (initial setup compiled duplicate top module) and reran actual native mapped fabric with read-only config/cone diagnostics. `native_cone_probe_session51.log` / `simulation_chip_native_cone_probe_20261005_mapped_fabric/test.log`:8707bits known and matching image, UART still fails. LB flop D trace reaches unknown neighbor-route inputs and feedback; reset-select mux chooses data at sampled pre-RUN point. This is diagnosis, not native gate-level success or a demonstrated synthesis/model bug. No state/configuration force was added. Frozen RTL/upstream/spec/held-out set and Git history/remote untouched.
**Boxes ticked:** none. Phase5 and compact physical/native verification gates remain open.
**Next:** Investigate local control/IO/reset routing at fixed complete area/clock using exact endpoint evidence; distinguish real reset/initial-state behavior from gate simulation X behavior before changing the model. Retain G1 and its tested software demonstrations; continue clean reproduction and missing original-tile artifact recovery.

## 2026-10-05 (session50: local CRC placement and tested capture range option)
**Done:** D-042 two-iteration clock-Metal3 diagnostic finishes3784versus3482baseline in13m08s; set aside. Implemented D-043 isolated instance-padding helper from exact pre-GRT baseline, checking connectivity and fixed positions, refusing existing outputs. Four sites cannot legalize; unrestricted two sites moves1539cells and is not routed. Retained two-site probe temporarily anchors3055remote cells, moves256local cells, restores statuses;0GRT overflow/277632µm,3497cells and805813.14µm² unchanged. Bounded DRT launched separately; actual12CRC endpoint locations survive into its input. Active diode inputs untouched. Evidence in `chip_crc_padding_local_screen`, route report and D-043.

Added soft capture `STAMP_SHIFT` parameter and `prescaled.yaml`:6stored bits/four-clock ticks give256-clock wrap versus64unscaled,85/88LCs versus83, same722words/two timers/two shifts/17IO,69.69MHz model only. Real compilation/audit and loaded RTL29.28s+synthesized-shell/RTL-fabric46.93s pass (`uart_capture_prescaled_20261005`). Expanded loaded test covers272-clock wrap interval and13-clock quantization without losing events, plus existing concurrency/overflow/order/backpressure/RX/reset/STOP. Fresh default report/image audits PASS and is byte-identical to original; expanded default RTL test31.00s. Verilog-2005 elaboration passes after including user primitive simulation wrappers. Capture report/README/C13/evidence/roadmap/in-progress phase5 summary updated. No native fabric/SDF/silicon claim; old source hashes correctly require refreshed report after parameterization.
**Validation:** Strict XML one-case/no failure/error/skip checks, both compiler audits, default byte comparison, elaboration and whitespace checks pass. No frozen hardware/spec, held-out tuning, upstream edit, history/remote change.
**Boxes ticked:** none.
**Next at session end:** inspect full diode and bounded padding results; continue native mapped-fabric cone diagnosis. The copied native probe initially has a duplicate-top setup failure; corrected and rerun in session51 above.

## 2026-10-05 (session 49: soft capture/buffering on G1 and bounded physical comparison)
**Done:** Started D-042 clock-minimum Metal3 bounded2-optimization DRT comparison in `chip_clock_m3_screen/runs/clock_m3_drt_screen`, from exact screened GRT state, releasing placement groups with existing helper. Post-DRT antenna repair disabled only for this diagnostic; it cannot qualify/promote. Initial5466markers versus same tighter baseline6038, but first optimization still active; no improvement claim from initial count. Stock preplaced-diode full route continues independently, latest656markers at70% in optimization6. Source/config inputs untouched; work may share compute resources.

Implemented design-set user-bitstream `protocols/uart_capture/`: UART plus two soft event timestamp entries, sampled event input, sticky drop-newest overflow and externally selected stream feeding the shell RX FIFO. Eight-bit timestamp screen fails91/88LCs. Six-bit version fits83/88LCs,2timers/2shifts,17IOBELs,722words;69.69MHz model only. Demo YAML now selects fitting six-bit version. Final hash-bound build/audit PASS, byte-identical to initial tested six-bit image (`build/uart_capture6_final_20261005` and `.log`). Source elaborates as Verilog-2005 with primitive implementations.

Top-level real SPI-loaded test passes both RTL26.75s and freshly synthesized gate-shell/RTL-fabric43.55s (`build/uart_capture6_20261005/{rtl_results.xml,gate_shell_results.xml}`, strict one-case/no fail/error/skip). Covers TX/capture concurrency, local queue full/overflow, ordered timestamp delta32, pointer reuse and known68-clock interval with modular delta4, shell backpressure (two shell+two soft entries retain first four of five events with unequal intervals), drop-newest, sticky overflow/reset, normalRX0xA5 after stream changes and STOP parking. No autonomous scheduling, native fabric/SDF/silicon evidence. Same-cycle full push/pop specified but not separately isolated as a loaded-test bin. Timestamps wrap64clocks; fiveLCs remain. Stream selection cannot replace queued shell bytes; USER_RESET clears soft state, not existing shell FIFO data. Reports/README/roadmap/C13/evidence updated with compromises and rejected wider result.
**Validation:** Actual compile/place/route/bitstream/audit/byte comparison, both loaded suites, source elaboration and whitespace checks pass. No frozen hardware/spec, upstream edit, held-out tuning, repository history or remote change.
**Latest routing:** Stock diode iteration6 completes478markers and starts7. Clock-layer diagnostic iteration1 completes3837 versus baseline3441, so it is worse at this matched early stage despite fewer initial markers; iteration2 remains active. No candidate promoted.
**Boxes ticked:** none. Phase5 and physical/native mapped-fabric promotion gates remain open.
**Next:** Compare completed clock-layer diagnostic with baseline at same stage and inspect stock diode antenna/DRC. Screen prescaled timestamps as a resolution/range tradeoff using measured remaining G1 capacity, then load/test any fitting candidate before claiming benefit. Continue native mapped-fabric evidence and original-tile artifact recovery independently.

## 2026-10-05 (session 48: source/image provenance and historical evidence recovery)
**Done:** Continued diode-route optimization without changing its inputs; latest optimization4 reports1202markers at70%, versus5601initial. Intermediate progress is not a pass. Clock-layer bounded GRT result remains unpromoted; no second full route launched.

Added compiler provenance: reports capture seed, existing control threshold, strict-port option, SHA256 of explicitly listed source/pin/architecture/generated-model/compiler inputs and emitted image. Before image emission, changed listed inputs reject compilation. New `python -m compile.audit REPORT` checks listed inputs/image hashes and image CRC/architecture/length against report. Scope deliberately excludes recursive includes and vendor binaries/libraries; not authentication, atomic snapshot, behavioral equivalence or chip signoff. Absolute paths refer to original inputs. User guide and `docs/reports/compiler_provenance.md` explain scope/reproduction.

Fresh G1 fault-image compile/audit PASS and byte-identical to already loaded/tested image (`build/uart_fault_provenance_20261005/{report.json,fault.wbit}`, corresponding `.log`). Actual Yosys/nextpnr run modifies only an owned source copy after placement; compiler detects change and emits no image/success report (`build/compiler_input_race_20261005/verification.txt`). Compiler49-test regression PASS27.19s before two added snapshot/error checks; final14provenance/diagnostic tests PASS0.27s, including missing/modified source, swapped valid image, truncated header, report mismatch and missing-input errors. Full final compiler suite also scheduled. No bitstream-format or host-interface change.

Read historical G1 CI run36342012141 artifact metadata and downloaded `GDS_logs`10939348491 into ignored build archive. Inventory909members: only chip-level SPEF stage/final copies, no primitive tile netlist/parasitics. This archive cannot close matching G1 tile timing gap. Evidence: `build/g1_timing_archive_audit_20261005.txt`; report reproduction notes updated. Existing local newer tile netlists differ in configuration storage/logic as well as text; no substitution or timing pass claimed. No remote write/history change.
**Validation:** Actual fresh compile, audit, byte comparison, deliberate changing-input rejection, final51compiler tests PASS27.99s (`build/compiler_provenance_all_final_20261005.log`), archive inventory and whitespace checks pass. No frozen hardware/spec, upstream code or held-out changes.
**Boxes ticked:** none. Phase5 clean-machine/CI/evidence and compact promotion gates remain open.
**Next:** Inspect final diode antenna/DRC; if needed compare clock-layer guidance at the same DRT stage. Continue matching original-tile archive/source recovery or separately verify a rebuilt tile before making new timing claims. Use hash-bound reports for new G1 compiler/showcase evidence; retain verified fallback and native mapped-fabric limits.

## 2026-10-05 (session 47: clock locality screen, stale-image safety and timing reproducibility)
**Done:** Continued active diode DRT without altering inputs; latest optimization2 has3609markers at70%, not a final result. Completed D-042 isolated clock-minimum Metal3 GRT from the tighter branch baseline's exact pre-GRT state. Same macro/clock/placement/cell totals;0overflow remains, wirelength276069→276156µm,3497cells/805813.14µm² including macro. No DRT/timing improvement claimed; no second full route launched. Research: official OpenROAD routing-layer docs plus installed LibreLane variable handling. New scratch directory `build/arch_explore/compact_edges_tighter/chip_clock_m3_screen`, run `clock_m3_grt`. Decision/report updated.

Extended native DRC diagnosis to preserve complete net groups. The completed144-marker baseline has20markers involving net37/CRCbit2,16clock-trunk/net1233,9shell-control pairs and8SPI pairs. Exact pair counts guide local placement/routing hypotheses rather than treating all west defects as antenna failures. Evidence: `final144_netgroups_20261005.json`; parser reproduces144total. Existing final route remains failed.

Found/fixed BUGS#28: failed rebuild could retain the old loadable image even after reports were invalidated. Compiler now invalidates the exact output image before synthesis and preserves differently named images. Five diagnostics tests PASS0.28s, including target-image deletion/other-image preservation. Actual95/88-LC failure proves this with a previously valid image (`build/compiler_stale_image_20261005/verification.txt`); fresh successful rebuild remains byte-identical to the fully tested fault image (`compiler_image_rebuild_20261005.log`). User guide/bugs updated; no protocol hardware change.

Attempted a fresh ten-path primitive-tile STA audit; historic routed PRIM2T2S netlist/SPEF paths are absent, while committed tile netlist remains. No fresh timing pass claimed. Reproduction gap recorded in `docs/reports/reproduction.md`. Improved `tools/timing/tile_check.sh` to select completed netlists without brittle ls sorting and reject missing matching netlist/SPEF before creating audit output, with restoration/rebuild instructions. Explicit missing-artifact check passes (`build/primitive_path_audit_20261005/missing_artifact_check.log`). Do not substitute wire-free timing for extracted routed evidence.
**Follow-up:** Default timing audit found newer experimental tile artifacts; their netlists differ from committed G1 and no completed local run is byte-identical. Fixed BUGS#29: default selects matching netlists only; explicitly supplied variants require labeled opt-in. Default unavailable-matching-evidence and explicit variant rejection checks pass. Missing evidence is the matching G1 archive, not all primitive parasitic files; no equivalence is assumed from filenames. Report corrected with this distinction.
**Validation:** Actual compiler failure/success checks, five diagnostic regressions, native144-marker count, timing-artifact error path and whitespace check pass. No frozen RTL/spec, upstream edit, held-out tuning, repository history or remote changes.
**Boxes ticked:** none. Phase5 clean-machine/CI/evidence gates and successor promotion gates remain open.
**Next:** Inspect completed diode-route antenna/DRC result. Consider a same-stage bounded clock-layer DRT comparison only if needed, keeping guards/checks. Restore matching primitive-tile extracted artifacts or rebuild the identical tile before refreshing timing evidence. Continue G1 software/verification independently; retain default compiler mappings and verified fallback.

## 2026-10-05 (session 46: independent fault showcase and compiler usability)
**Done:** Added `uart_fault_monitor_top.v`/`fault.yaml` as a user-bitstream extension on unchanged G1. A synchronized external input inverts UART TX alongside the independent event monitor; costs one LC/one input IO BEL beyond the sampled monitor, totaling38/88LCs and722words. Real SPI-loaded two-case suites pass normal TX/RX/events/wrap/framing errors, selected0x55→0x57 data corruption, recovery, idle override, reset and STOP parking with fault held high. RTL39.35s and fresh synthesized gate-shell/RTL-fabric68.50s; strict XML confirms two cases/no fail/error/skip in `build/uart_fault_monitor_20261005/{rtl_full_results.xml,gate_shell_full_results.xml}`. No autonomous scheduler, SDF/native fabric/silicon claim. Verilog-2005 source elaboration passes with primitive modules. Report/README/roadmap/C12/evidence updated.

Compiler now supports `--strict-ports`, rejecting accidental unmapped inputs/outputs before synthesis. Actual missing fault-input check passes (`build/uart_fault_monitor_strict_20261005/result.txt`); complete image compiles with strict checking. Place/route failures write `failure.json` with resource/tool/error details and capacity versus control/routing advice. New builds invalidate stale success/failure reports (BUGS#27). Actual95/88-LC binary-I2C failure proves diagnosis and removal of stale success (`build/compiler_fit_diagnostic_20261005/verification.txt`). Final compiler/board315unit tests PASS25.64s, including five meaningful diagnostics cases (`build/compiler_host_unit_final_20261005.log`). Fresh final compiler build is byte-identical to the fully loaded tested image (`uart_fault_monitor_final_20261005`). User guide corrected: failed builds have no success report.

Completed independent design-set mapping screens: thresholds2/4/8 for UART/SPI/I2C (nine builds), plus native/binary/one-hot FSMs for SPI/I2C (six builds). Keep defaults: threshold8 SPI costs48vs47LC and model61.63vs77.97MHz; binary SPI saves one LC but model62.20vs77.97MHz; binary I2C needs95LC and fails. Other alternatives match baseline. No changed mapping selected or loaded; these are model screens, not silicon rates/equivalence. Reusable drivers in `spikes/compiler_controls/`, exact aggregates under `build/compiler_{controls,fsm}_20261005/summary.json`; report `docs/reports/g1_compiler_controls.md`. Consulted official Yosys dfflegalize/FSM documentation and pinned local help; links in report. Updated phase5 in-progress summary; no exit gate ticked.

**Routing:** Older shared-CRC finishes404markers, then enters incompatible Magic processing; stopped failed job, reports retained. Daemon restart interrupted the remaining preplaced-diode route (through early optimization3). Checked host processes and confirmed no router survived, rather than treating an open terminal as progress. Restarted unchanged experiment from preserved pre-DRT state into fresh `compact_diodes_drt_restart_20261005`, with stock route/checks; currently active in initial routing. Original interrupted snapshots/reports retained. New software work uses separate directories and never edits routing inputs; compute contention remains possible.
**Validation:** Final unit XML/log and four loaded cases pass; source elaboration, byte comparison and whitespace checks pass. Initial source elaboration omitted primitive implementation files, corrected invocation passes. No frozen hardware/spec, held-out workload, upstream code, history or remote change.
**Boxes ticked:** none. Phase5 clean-machine/CI/evidence gates and successor physical/native mapped-fabric gates remain open.
**Next:** Inspect full diode-route antenna/DRC outcome; target west clock/CRC/configuration locality from completed144-marker audit if necessary. Continue phase5 reproduction/evidence and compiler/host usability on G1 independently. Avoid another broad seed/control sweep without a measured hypothesis. No hardware promotion until all physical/timing/end-to-end gates pass.

## 2026-10-05 (session 45: completed routing diagnosis and tested fallback concurrency)
**Done:** Tighter shared-CRC/local-branch stock route finishes with144 native DRC markers, zero antenna nets/pins, seven added repair diodes. All144 markers lie west:141 Metal2/3 Metal3,86 shorts/58 spacing. Read-only final ODB audit identifies eight-load clock distribution, local CRC bit2 wiring and a configuration-word hold-delay output among implicated nets. Added selectable exact-net auditing with escaped-bus lookup. Evidence: `build/arch_explore/compact_edges_tighter/pass1_iter16_summary_20261005.json`, `final144_net_audit_20261005.log`; report `docs/reports/compact_route_diagnosis.md`. Stopped this already-failed flow and the original716-marker flow during incompatible Magic processing, preserving snapshots/reports. Neither is a physical pass.

D-041 optional preplaced configuration protection adds14 diodes/76.2048µm² in its isolated scratch directory. GRT0overflow/275796µm wirelength/514 hold buffers; actual transformed post-CTS shell with RTL fabric passes loaded SPI/UART TX/RX/STOP25.28s (`simulation_chip_shared_crc_cfgdiodes_mapped_shell/results.xml`). Full stock route remains active; early DRT is not signoff. Older shared-CRC full route also remains active, latest repair pass around404 markers. No active inputs modified.

Fresh synthesized-G1-shell/RTL-fabric monitor test exposed missed events in initial36-LC user design (BUGS#26); read-only probes narrow timing/scheduling investigation without claiming a silicon cause. Added one fabric input sample register to the user design, costing one LC and one clock latency. Current37/88-LC,722-word image passes full top-level loaded TX/events, RX/events, wrap, framing error, USER_RESET and STOP tests in both RTL23.23s and synthesized shell33.82s. Evidence: `build/uart_monitor_sampled_20261005/rtl_results.xml`, `build/g1_monitor_gate_20261005/sampled_results.xml`, compile report in sampled directory. Gate-shell test has RTL fabric/no SDF, not native whole-chip gate signoff. Updated demo README/report, roadmap, claims/evidence. Consulted primary FABulous timing characterization and Yosys FABulous mapping documentation; no upstream edits or speculative tool changes.

**Validation:** Strict test XML checks pass; whitespace check passes. No frozen hardware, architecture contract, held-out workload, history or remote changes.
**Boxes ticked:** none. Phase5 reproduction/evidence and successor promotion gates remain open.
**Latest:** Older shared-CRC routing writes its final database at404 DRC markers; subsequent checks are not yet complete. It cannot qualify with that routing result. Preplaced-diode routing remains active.
**Next:** Inspect final stock-route checks of preplaced-diode and older shared-CRC experiments. Use west clock/CRC/configuration locality evidence to select one isolated physical change only after these results; retain all DRC/antenna/timing checks. Continue native mapped-fabric verification separately. G1 remains the verified fallback.

## 2026-10-05 (session 44: targeted branch buffering and tighter macro completion)
**Done:** Implemented optional D-040 local buffering of frame_idx bits0/1 to each column decoder, based on exact antenna diagnosis.14 non-inverting buffers cost127.008µm² before repair; rail connections and decoder placement groups preserved. Scratch pre-placement probe passes. Matched sharedCRC/lead-macro screen improves GRT overflow93→27 and estimated wirelength285645→281448µm, hold buffers512→522; zero-overflow guard correctly stops. Bounded2-iteration DRT screen starts at5626markers (sharedCRC baseline5010) and is active as `chip_shared_crc_cfgbranches/runs/cfgbranches_drt_screen`. Actual transformed post-CTS mapped shell with RTL fabric passes real SPI/UART TX/RX/STOP (23.92s), all14 added buffers retained. Report `docs/reports/compact_cfg_branches.md`. Frozen RTL/spec/config unchanged.

All four unfinished tighter north tiles completed successfully. Stitched/exported real1120.32×669.06µm macro passes explicit KLayoutDRC0 (`compact_edges_tighter/runs/tighter_stitch_20261005`). Actual842-word SPI/UART/STOP RTL test PASS15.74s (`simulation/results.xml`). Fresh hash-bound trace confirms160data/92strobes consumed. Matched tighter-geometry sharedCRC+local-branch GRT completes with0overflow/276069µm/522hold buffers; guard passes and full stock `compact_local_route` begins. Geometry is the sole new variable versus D-040's lead-macro screen. Actual tighter mapped-shell loading is also active. No geometry promoted.

Pinned router help supports jumper-only. Copied initial-DRT probe runs but detailed antenna result remains1net/2pins, so no standalone fix is established. Original lead DRT finishes at716markers/checker failure; four DRT passes take131m58s total, documented in PHYSICAL_DESIGN_AND_CI. Additional Magic DEF via-reading errors do not change routing failure. SharedCRC full stock route remains active. Active-run inputs untouched; new experiments use separate directories.
**Validation:** Strict XML on mapped branch-shell and tighter RTL tests:one case,no fail/error/skip. Syntax/whitespace check passes. No upstream edits, held-out work, history or remote changes.
**Boxes ticked:** none. Phase5 and successor promotion gates remain open.
**Next:** Compare branch-buffer boundedDRT with the same-stage sharedCRC baseline, inspect final antenna results and short/spacing hotspots. Continue full stock routing only for supported improvements; no disabled-check diagnostic can qualify. Compare tighter geometry GRT first, then real mapped loading and full physical/timing gates if promising. G1 remains fallback.

## 2026-10-05 (session 43: RX concurrency and live routing diagnosis)
**Done:** Extended G1 monitor test to receive 0xA5 while ten independent input events occur, check a deliberately bad UART stop bit retains framing-error status beside the count, and reset both through the host. PASS with pinned simulator/project venv (`build/uart_monitor_rx_20261005_results.xml`, 29.10s; strict XML no fail/error/skip). Updated scope/report, C11 local claim and evidence's misleading one-design-at-a-time wording: one bitstream can contain concurrent functions.

At user request, diagnosed ongoing compact runs from read-only saved DRC/OpenDB snapshots rather than waiting. Added `spikes/compact_edges/inspect_route.tcl`; no routed DB writes. Lead repair2:576 markers, all west,379 in x0–50/y500–550; drivers include CRC/SPI fanout and hold-delayed command bits. Diodes21→51 but west count unchanged21, so added local diodes alone do not explain residual west DRC. SharedCRC iteration6:673 markers, all west, shifted command/data hotspot. Exact antenna checker reproduces initial frame_address[28] ratios251–255/200 and repair2 net22/frame_idx[1] distribution to column6 ratios201.56–203.25/200. Report, evidence paths, limits and targeted next experiments: `docs/reports/compact_route_diagnosis.md`. Inspected pinned flow:16 iterations plus up to3 repair/reroute passes; upstream left untouched. Latest routing jobs remain active; no pass claimed. Estimated1–3h remaining is rough wall-clock completion guidance, not a pass promise.
**Boxes ticked:** none. No hardware promotion, history or remote changes. Whitespace check passes.
**Next:** Inspect final runs, target configuration index buffering/branch placement and west hotspot locality; validate supported jumper-only repair before a matched isolated experiment. Retain all antenna/DRC checks. Continue phase5 reproduction/evidence and native mapped-fabric diagnosis.

## 2026-10-05 (session 42: G1 concurrent loaded UART/monitor demonstration)
**Done:** Added `protocols/uart_monitor/uart_monitor_top.v`, isolated `demo.yaml` and scope/reproduction README. This user bitstream combines existing UART with an independent four-bit edge counter on FAB_IN1 and reports count in USER_STATUS. It deliberately stays outside the frozen comparison workload auto-discovery. Compiles onto explicit frozen G1: 36/88 LCs, all two timers/two shifts, 722 words; model Fmax 89.49 MHz, not chip signoff. Added top-level `test/test_uart_monitor.py`: real SPI load, overlapping UART TX and 20 input events, three decoded bytes, modulo wrap, USER_RESET and STOP. Pinned Icarus12/project-venv cocotb2.0.1 test PASS; final bounded-observer version PASS (`build/uart_monitor_final_20261005_results.xml`). Report `docs/reports/g1_uart_monitor.md`, roadmap updated. Initial test PATH selected suite simulator/Python; discarded as validation and reran with D-007 PATH and project venv.
**Run status:** Shared CRC full route reaches completed iteration4 at726 markers and continues iteration5; lead compact antenna rerouting remains about576 markers late in its optimization; tighter north C5 remains at3 stubborn markers. No pass or promotion claimed. Jobs use separate inputs/directories; lightweight G1 work can share compute resources but does not alter active runs. Initial memory check ~9.5GiB available, no swap.
**Validation:** Strict final XML check: exactly one test, no fail/error/skip. Whitespace check passes. No frozen hardware, history or remote changes.
**Boxes ticked:** none. Phase5 and successor physical/gate gates remain open.
**Next:** Inspect final compact route results and remaining north tile checks, diagnose residual native markers. Extend monitor evidence to UART RX and fault/overflow behavior before enlarging the showcase; resolve mapped-fabric simulation independently. Required whole-chip physical/timing/verification and reproduction gates still apply.

## 2026-10-05 (session 41: improvement roadmap and completed G1 compiler screen)
**Done:** Wrote `docs/design/COMPETITION_IMPROVEMENT_ROADMAP.md`, covering all recommendations, fallback applicability, priorities, benefits/costs and evidence requirements. Distinguished software/bitstream improvements possible on unchanged frozen G1 from hardware revisions. Added reusable `spikes/compiler_seeds/run.py` and completed nine frozen-G1 builds (UART/SPI/I2C controller, seeds 1/2/3). All fit and generate bitstreams. Alternate seeds are slightly worse in the existing timing model; retain seed 1 and do not claim a speedup. Report: `docs/reports/g1_compiler_seeds.md`; local run `build/compiler_seeds_20261005/summary.json`. No loaded simulation of new images or silicon rate claim.
**Validation:** Driver completed exit 0; reports preserve per-build tool versions and resources. Whitespace check passes. No frozen RTL, architecture, held-out design, repository history or remote changes.
**Boxes ticked:** none. Phase 5 and successor promotion gates remain open.
**Next:** Measure a small design-set emulator plus independent monitor on G1; target compiler logic/resource efficiency rather than additional unmotivated seed sweeps. Continue active compact physical runs and gate/reset diagnosis independently.

## 2026-10-05 (session 40: competition improvement priorities)
**Done:** Reviewed the current competition brief, successor exploration, G1 workload limits and equal-area comparison to answer improvement priorities. Recommended concurrent emulator/monitor demonstrations, compiler efficiency and usability, measured routing/configuration locality, primitive input timing, then conditional generic event lanes or small buffering. Extra primitive tiles/control sets and a large register file remain unsupported by current workload data; prior rejected timer-only changes are not presented as new fixes. New architecture evaluation needs fresh sealed workloads because G1's old held-out results are already public. No hardware change selected or implemented in this advisory session.
**Boxes ticked:** none. Existing compact routing work continues; all promotion gates remain required.
**Next:** Finish current physical/gate diagnosis; run inexpensive design-set concurrent-demo/compiler screens before selecting another hardware experiment. Record equal whole-chip area, same-clock timing, route completion and loaded-bitstream behavior for any selected candidate.

## 2026-10-05 (session 39: shared-word CRC; continued physical and gate diagnosis)
**Done:** Continued D-037/D-038 scratch work and researched upstream gate simulation plus congestion-focused FABulous literature. Added proposed D-039 shared-word CRC helper, isolated staging and verification driver. The shell reuses its stable `cfg_word` instead of duplicating word storage in the CRC. An initial integration used the changing assembly wire; real SPI loading caught it, and the corrected registered-word connection passes (BUGS #25). No frozen source or architecture contract changed.

**Evidence:** Forty-stream CRC unit test PASS, including cycle comparison with baseline and independent zlib values. Actual 842-word SPI/UART/STOP RTL test PASS with all 26,944 CRC input-stability cycles checked. F2 BMC PASS at the existing 84-cycle bound; cover reaches valid load/RUN at step 52 (60-cycle bound). Existing SPI abstraction and no-byte-while-busy assumptions remain. Baseline mapped shell plus RTL fabric PASS; native mapped fabric remains failing after RUN despite 8,707 correctly loaded configuration bits. Internal combinational-settle and real USER_RESET probes did not fix it. Details and reproducible paths: `docs/reports/compact_shell_crc.md`, `spikes/compact_edges/README.md`.

**Physical:** Same macro/20 ns target/hold margin: shared CRC pre-PDN mapped shell area 44,443.7 µm² versus 46,753.5, 512 versus 605 hold buffers; GRT overflow worsens to 93 versus 67, while estimated wirelength falls to 285,645 versus 314,294 µm. Two-iteration diagnostic DRT ends at 2,652 markers versus baseline 4,503 (antenna rerouting disabled only in screen). Full stock run `chip_shared_crc_physical/runs/shared_crc_full_drt_20261005` started from preserved pre-DRT state. Lead `compact_narrow_rows_drt_20261005` reached 268 first-pass markers, then remains in antenna rerouting. Tighter north N_IO_C4 recovery completed successfully; N_IO_C5/NW_term/NE_term_wide batch continues. No completed tighter macro or full-chip pass claimed.

**Boxes ticked:** none. Phase 5 gates and all promotion gates remain open. No repository history/remote changes.
**Next:** Await both full-chip stock route/check results and remaining tighter tiles. Record native layer/region summaries and elapsed times. Stitch/export tighter geometry only after all tile checks pass, then test actual SPI-loaded image before matched chip routing. Preserve frozen G1 until complete physical and end-to-end verification gates pass; continue mapped reset/feedback diagnosis without scrubbing user state.

## 2026-10-05 (session 38: resume compact integration; exhaustive configuration audit)
**Done:** Read the project contract, verification/physical flow, current phase 5 gates and latest exploration decisions/handoff. Continued D-037/D-038 scratch work without replacing frozen G1. Restarted lead detailed routing from its original preserved pre-DRT state using `config_recovery.json`, fresh run tag `compact_narrow_rows_drt_20261005`, and stock checks. It reproduces 6,424 initial violations and remains active in optimization; no final route/DRC pass is claimed. Log: `build/arch_explore/compact_edges/chip_mask_narrow_rows/compact_narrow_rows_drt_20261005.log`.

Expanded white-box mapped-fabric diagnostics to every tile, decoding expected frame bits from the actual SPI image. All **8,707 exposed mapped configuration bits** are known and match the loaded image (zero mismatches). After RUN the shell run/reset signals and exposed tile clocks are known; several logic-cell state/output signals remain X and the UART pin test fails. This narrows investigation beyond loading but does not prove a simulation-only root cause. Evidence: `build/arch_explore/compact_edges/gate_image_audit_20261005.log`, `simulation_chip_mask_narrow_rows_mapped_fabric/test.log` in that work directory. No configuration/user-state forces were added.

Added reproducible native DRC report summarization (`spikes/compact_edges/report_drc.py`) to avoid BUGS #21's XML layer loss. It exactly reproduces previous iteration 8's 1,059 markers (787 Metal2, 250 Metal3, 22 Metal4; 776 shorts/283 spacing). Centers locate 1,046 west and 13 south of the macro. Saved summary: `build/arch_explore/compact_edges/lead_iter8_summary_20261005.json`. Counts are markers, not independent faults. This supports targeting shell-channel locality rather than another blind macro blockage change.

**Validation:** `scripts/check_all.sh` PASS, including 377 Python tests and protocol/shell checks (`build/check_all_20261005.log`). Its first sandboxed run failed the I2C sigrok check because libusb initialization was denied; permitted unsandboxed rerun passes. Improved test diagnostics preserve stdout/stderr (BUGS #24). Compact candidate SPI/UART TX/RX/STOP RTL regression PASS (`simulation_chip_mask_narrow_rows/results.xml`, 14.29 s). Python syntax and whitespace checks pass.

**Research:** Consulted FABulous discussion #327 on combinational-loop simulation handling and OpenROAD's GRT documentation on congestion reports/resource controls; links and limits recorded in `spikes/compact_edges/README.md`. User explicitly requested ongoing online/upstream/paper research when stuck. No tool upgrade or upstream modification made.

**Boxes ticked:** none. Phase 5 evidence/reproduction gates remain open. No frozen hardware, architecture contract, submission settings, held-out workload, history or remote changed.
**Next:** Inspect the final native DRC/check results of active `compact_narrow_rows_drt_20261005`; use `report_drc.py` on its latest report. If violations persist, isolate a shell-channel placement/resource change and compare under the same macro/clock/hold margin. Continue mapped-fabric state/reset-path diagnosis or equivalence/timed simulation; matching configuration alone is not gate-level correctness. Four tighter north variants remain unfinished; do not promote either geometry before physical/timing gates pass.

## 2026-09-30 (session 37: narrower row fences; paused at user request)
**Done:** Continued actual 5 × 3 integration in isolated scratch tooling. The reproducible masked-strobe, early-release, Metal1 pipeline reports 155 overflow / 362,577 µm. Narrowing the three middle configuration-row fences to 21.12 µm improves this to **67 overflow / 314,294 µm**, with 605 hold buffers (`build/arch_explore/compact_edges/chip_mask_narrow_rows/runs/compact_local_grt`). All placement regions are released before repair. This retains the proven 1120.32 × 676.62 µm macro, 112 LUT4s, two timers and two shifts. No frozen hardware changed.

Native detailed routing (`compact_narrow_rows_drt`) progressed from **6,424 initial violations to 1,059 at completed iteration 8**; iteration 9 was interrupted by a daemon restart, so there is no final routed database or pass. Iteration 1 had 5,141 of 5,231 markers west of the macro, mostly ordinary Metal2 shell wiring; only 109 involved power nets. Iteration 8 still has 787 Metal2, 250 Metal3 and 22 Metal4 violations. This localizes the remaining problem to the crowded shell channel. Restarted from its saved pre-DRT state with snapshots enabled (`compact_narrow_rows_drt_recovery`); saved `01-openroad-detailedrouting/drt_iter0.odb`. Stopped recovery during iteration 1 at the user's request. Snapshot continuation has not been validated; the original pre-DRT state remains a reliable restart input.

Completed south-only macro `compact_south45/south45_stitch`: **1120.32 × 672.84 µm, KLayout DRC 0**, and actual 842-word SPI/UART/STOP RTL test passes. Its narrower-row screen gives 74 overflow / 331,912 µm; bounded detailed routing reports 14,837 initial and 14,799 iteration-1 violations (`south45_narrow_drt_screen`). This is worse than the 676.62 µm lead. The reference placement gives 5,542 overflow. Keep the lead geometry. Other lead placement screens also fail to improve it: density 75 gives 75 overflow, density 75 plus routability inflation 744, padding two sites 11,613, and extra GRT iterations 173. A Metal2 capacity-reservation screen gives 86 overflow / 313,732 µm; its bounded DRT run was stopped before a complete result, so it is inconclusive.

The tighter north/south batch has completed base north, N_IO_C2, N_IO_C3 and all south views; south variants were reused only after height, zero-DRC and byte-identical RTL checks. N_IO_C4 recovery was stopped mid-route, and N_IO_C5/NW_term/NE_term remain unfinished. No stitched 669.06 µm macro exists yet.

Post-CTS mapped shell plus RTL fabric passes the real SPI load, UART transmit/receive and STOP test (`simulation_chip_mask_narrow_rows_mapped_shell/results.xml`, 35.26 s, no SDF). Fully mapped fabric diagnostics fail with X values after RUN, including with RTL/pre-CTS shells; sampled configuration bits are known after loading. This is consistent with the existing D-023 zero-delay feedback limitation, not proof of a new hardware fault or a native fabric gate-level pass. Added optional white-box diagnostics in `test_internal/compact_gate_probe.py`. Fixed the scratch simulation runner to reject failing cocotb XML instead of returning success (BUGS #23); a failing rerun now exits 1. Python/shell syntax and whitespace checks passed.

**Boxes ticked:** none. No architecture contract, submission settings, held-out workload, history or remote changed. Full-chip zero routing DRC, stitched-chip DRC/precheck and macro timing remain open; retain frozen G1 as fallback.
**Paused:** User requested a reasonable stopping point because of the session limit. Stopped the recovery route, tighter tile batch and Metal2 reservation route with Ctrl-C (exit 130). No experiments are intentionally left running.
**Next:** Restart lead detailed routing from `chip_mask_narrow_rows/runs/compact_narrow_rows_drt/04-openroad-detailedrouting/state_in.json` using `config_recovery.json`, a fresh run tag and stock checks. Resume only the four unfinished tighter north variants before stitching; preserve completed south views. Exact lead restart command and evidence are in `spikes/compact_edges/README.md`. Do not promote either geometry until the physical gates pass.

## 2026-09-30 (session 36: compact edges and real decoder locality)
**Done:** Implemented a reproducible scratch physical experiment in `spikes/compact_edges/` rather than another proxy-only diagnosis. Re-hardened 14 north/south/corner tiles, reducing north height to 37.80 µm and south height to 49.14 µm. All 14 completed with zero routing and KLayout DRC violations; run IDs are in `spikes/compact_edges/README.md`. Stitched `compact_edges_stitch`: real 5 × 3 macro is 1120.32 × 676.62 µm, 758,030.92 µm², recovering 26.46 µm of die height; stitched KLayout DRC is zero. Every generated tile RTL file is byte-identical to its phase-aligned source; resources remain 112 LUT4s, two timers and two shifts.

Actual full-shell RTL simulation loaded the existing 842-word UART image through SPI, entered RUN, transmitted 55/00/C3, received 69 and parked after STOP (`sim_preview/simulation/results.xml`, 4,513,240 ns). Preview fabric/chip RTL matched the subsequently exported versions byte-for-byte. The deferred-flattened mapped shell separately passed the same test with Icarus 13 and template CMOS5L functional models (`simulation_mapped_shell/results.xml`, 28.10 s). Both use the D-023 settling harness for unused combinational routing. The latter still has an RTL fabric and no SDF: neither is full-chip gate-level or silicon evidence.

Full-shell integration uses the real external configuration path, original `src/pdn_cfg.tcl`, complete Metal1–4 macro obstructions and all stock synthesis/placement gates. Supply connectivity passes. Increased density to 95%, disabled placement routability inflation and widened legalizer displacement to 1280/704 µm; this let post-CTS repair place its hold buffers while retaining the 0.1 ns extra margin. Shell legalization is not a routed hold/timing claim; the macro has no timing library.

Found two concrete integration problems: early synthesis flattening shared decoded frame nets across columns, defeating the intended local decoder RTL; and the default 10 µm vertical macro halo removed every placement row below the macro. Supported `deferred_flatten` maps each decoder before flattening (stock unmapped check passes); a 3.78 µm halo retains bottom rows. Optional per-column regions then place the 38 decoder cells per column under their fabric pins. Matched full-shell GRT screens on the same compact macro/y=15.12: ordinary flattening `compact_y15_displacement` **11,405 overflow / 610,524 µm**; deferred flattening `compact_deferred_y15` **9,279 / 548,510**; smaller halo `compact_halo_row` **7,880 / 506,664**; decoder regions `compact_fenced_halo_row` **1,523 / 440,546**. This is an 86.6% overflow reduction on one candidate, not an equal-area comparison against frozen G1 or a route pass.

Released the placement regions after CTS/GRT so antenna diodes can use remaining bottom sites: keeping exclusive regions caused ten new diodes to fail legalization; release retains placed cell locations and enabled detailed routing (`compact_released_drt`, later stopped with thousands of violations to prioritize the improved candidate). A separate routing-layer screen allowing Metal1 outside the blocked fabric reduced GRT overflow to **991 / 434,318 µm** (`compact_fenced_m1_grt`), still not a route pass. The y=22.68 µm screen completed worse (**3,264 / 465,962 µm**, `compact_y22_fenced_v2`), so balanced y=15.12 remains preferred. An initial resume at the power-grid checker skipped earlier IO placement; restarting at `Odb.RemovePDNObstructions` fixed the step order. Tighter north/south base tiles (34.02/45.36 µm) both passed zero routing/KLayout DRC (`N_IO` RUN_2026-09-30_15-14-35; `S_IO2` RUN_2026-09-30_17-04-02). Remaining variants/stitch are running in an isolated directory, with automatic full-shell continuation queued at y=18.90 µm after successful export.

A further row-register region screen reduced hold buffers from 662 to 309 but worsened GRT to **174,271 overflow / 2,023,876 µm** (`compact_rows_fenced`), so it is rejected. A hash-bound Yosys trace through actual generated macro/tile/primitive RTL found all 160 FrameData bits consumed, but 48 of 140 FrameStrobe inputs unconsumed (per-column live counts 4/17/17/17/17/17/3). Added `input_usage.py` and a separate optional wrapper mask for those unconsumed inputs only. Its full SPI/UART/STOP RTL test passed (13.90 s) and its mapped-shell test passed (27.17 s). Under matched early-region-release placement, ordinary strobes give **1,065 overflow / 426,499 µm** (`compact_early_release_grt`); masking only unconsumed strobes gives **574 / 389,030 µm** (`compact_mask_early_grt`), a 46.1% reduction in that matched comparison. A Metal1 routing screen on the same masked placed netlist completed with **161 overflow / 362,577 µm** (`compact_mask_m1_grt_v2`); full detailed routing is running as `compact_mask_m1_drt`. Macro obstructions still cover Metal1–4. Added optional masked/early-release/Metal1 modes to the reproducible route driver, preserving reference defaults; its combined branch is being exercised in `chip_mask_pipeline_check`. Documented the scratch geometry/locality experiment and its costs in D-038; no promotion is accepted.

Corrected session 34's layer attribution using the native router report; pinned LibreLane's XML converter merges layers by violation type (BUGS #21). Recorded the concurrent FABulous primitive-JSON race and serial-driver workaround (BUGS #22). Python syntax checks, shell syntax checks and `git diff --check` pass.

**Boxes ticked:** none. Frozen RTL/fabric, hardware contract and submission settings unchanged; no held-out workload touched. No history/remote changes.
**Next:** Finish `compact_mask_m1_drt`, the combined driver screen and the tighter edge variants/stitch. The y=22.68 screen has already been measured and rejected. Use native final DRC locations to choose the next change. Full-chip zero-violation routing, DRC/precheck, macro timing and real gate-level loading remain open; retain 4 × 3 as the proven fallback.

## 2026-09-30 (session 35: explicit 5 × 3 route blockage test)
**Done:** Ran OpenROAD's `create_obstruction` against the saved x=121.44 5 × 3 shell-proxy database, adding explicit Metal2, Metal3 and Metal4 blockages over the fabric footprint, then reran global routing. The blocker is active (`Blockages: 6`, versus 3 in the prior run), but it does not change the available routing resources or clear the congestion: total overflow remains **2,648**, route demand changes from 16,972 to **17,053**, and wirelength from 163,404 to **163,900 µm**. Evidence is the scratch Tcl/log/guide under ignored `build/arch_explore/chip_5x3_phase_aligned/runs/cfgmacro_x121_routeblock_grt/`. The run reused the same pre-route ODB and isolated its guide; LibreLane's `write_views` wrote its ODB/DEF to the configured prior stage path, so this is only a global-route comparison, not a new detailed-route run.

This falsifies the immediate hypothesis that OpenROAD's GRT was simply missing a whole-macro route blockage: its resource estimate was already accounting for the macro, and duplicating that obstacle does not make the shell fit. The actual remaining issue is physical capacity/locality around a macro that occupies 98.9% of the die height and leaves only 7.56 µm total above/below it, together with severe shell-to-fabric pin routing. No candidate is routable yet; the 5 × 3 proxy must not be called a fit.

**Boxes ticked:** none. No tracked RTL, generated fabric or architecture contract changed.
**Next:** Stop changing the blockage representation. Use the existing detailed-route DRC locations and top-port connectivity to identify which pin groups/escape routes dominate the 5 × 3 failure; then test a concrete floorplan or interface change that creates more usable channel and rerun placement/GRT/DRT. Keep the 4 × 3 implementation as the known fallback until a 5 × 3 candidate passes the complete physical checks.

## 2026-09-30 (session 34: test hard-macro Metal4 obstruction)
**Done:** Investigated the zero-margin detailed-route shorts. The configuration-macro LEF has signal obstructions on Metal1–3 but none on Metal4, while the macro carries vertical VPWR/VGND straps on Metal4. At x=121.44, example DRC markers for `ui_in[3]` and fabric nets fall on the translated VPWR strap coordinates (local x=10.95–13.05 µm). To check the integration model, made an ignored LEF copy with a full-area Metal4 signal obstruction and reran the same x=121.44, zero-hold-margin shell proxy.

The corrected macro obstruction leaves global-route statistics identical to the unblocked zero-margin screen: 2,648 total overflow, 16,972 demand, 163,404 µm wirelength. The global-route guide file still has 19 Metal4 guide rectangles overlapping the macro bounding box, so the LEF obstruction alone did not remove all guides that traverse the block. Detailed routing completed its initial and post-antenna repair cycles (16 optimization passes each); the final pass reported 3,475 violations: 3,384 shorts (471 Metal2, 1,278 Metal3, 1,635 Metal4) and 91 Metal2 spacing violations (`runs/cfgmacro_x121_m4obs/39-openroad-detailedrouting/tt_um_warp.drc` and router log). The generated XML incorrectly groups shorts on all layers under the first layer; see BUGS #21. Of the 3,384 shorts, 3,040 markers fall inside the macro bounding box, commonly involving `inst:u_fabric`; 344 are outside, mostly near the top die edge. The valid-obstruction case still cannot route the shell, and the proxy's GRT/DRT behavior around this abstract hard macro needs further investigation. The route-only PDN also reports 91,278 grid violations; no signoff is established.

Updated `docs/design/ARCHITECTURE_EXPLORATION.md` with the distinction between the optimistic unblocked proxy and the hard-macro obstruction result. The architecture priorities remain: solve physical locality and configuration/pin-boundary cost first, prove full-shell 5 × 3 routing, then compare the hybrid event-lane idea at equal area and clock.

**Boxes ticked:** none. This is a scratch integration-model experiment only; no RTL, generated fabric, architecture contract, or held-out workload changed.
**Next:** Find why the global router still emits 19 Metal4 guides through the blocked macro and add an explicit routing blockage in the scratch flow; then measure route demand in the real side channels. If the 5 × 3 footprint cannot leave enough channel under that model, test a reduced interface/edge geometry or return to 4 × 3 while retaining 5 × 3 only if it can be integrated inside a properly shaped shell. Trace full top-port to macro-boundary route groups before choosing a pin remap.

## 2026-09-30 (session 33: hold-margin sensitivity and 5 × 3 detailed route)
**Done:** Continued the open-east-side 5 × 3 configuration-macro shell proxy screen. At x=100.0 and 0.1 ns extra post-CTS hold margin, the resizer found 275 hold-violating endpoints and inserted 441 buffers; detailed placement failed on 34 instances (`runs/cfgmacro_x100_two_channels/36-openroad-resizertimingpostcts/`). At x=121.44 and 0.1 ns margin, 446 buffers failed detailed placement on 13 instances. Lowering the extra margin to 0 ns at x=121.44 inserted 281 buffers and passed detailed placement (`runs/cfgmacro_x121_holdmargin0/36-openroad-resizertimingpostcts/`). This is a placement sensitivity result only; it does not establish final hold timing, especially with the fabric black-boxed and untimed.

Resumed the zero-margin run through global and detailed routing. Global routing ended with **2,648 total layer overflow**, 16,972 routing demand and 163,404 µm wirelength. Detailed routing completed its 16 configured optimization passes, reducing the initial 4,927 violations to **536**, including 527 Metal4 shorts, 5 Metal2 shorts and 4 spacing violations (`runs/cfgmacro_x121_holdmargin0/38-openroad-detailedrouting/openroad-detailedrouting.log`). Parsed the final DRC XML: representative signal-to-VPWR short markers lie at x=132.39–134.49 µm, exactly the macro's VPWR strap rectangle at local x=10.95–13.05 µm after its x=121.44 placement. That suggests an interaction between the proxy macro's narrow signal-pin access and Metal4 PG geometry; overlay the LEF/GDS/DEF before attributing these shorts to the fabric graph. This is the first 5 × 3 shell proxy run to pass detailed-placement legalization and complete all detailed-route passes, but it is not a route pass: violations remain, global routing is congested, and the route-only PDN produces about 91k power-grid violations. It has a proxy configuration macro and no fabric timing library.

The x-position sweep under matched settings still favors x=121.44: x=100.0 ended at 2,818 overflow / 136,483 µm (`runs/cfgmacro_x100_open/37-openroad-globalrouting/`), and x=90.0 at 2,960 / 147,369 (`runs/cfgmacro_x90_open/37-openroad-globalrouting/`). Earlier notes misread x=121's routing demand (13,770) as overflow; the corrected GRT table reports 2,705 overflow for the no-hold-repair comparison. Updated `docs/design/ARCHITECTURE_EXPLORATION.md` with the corrected placement comparison, the zero-margin legalization result and the ranked spatial/hybrid/configuration priorities.

Added an evidence-ranked successor roadmap to `docs/design/ARCHITECTURE_EXPLORATION.md`: prioritize spatial routing/locality and real 5 × 3 shell fit, then prove a compact event-lane plus LUT-logic hybrid, treat configuration remapping as an integration hypothesis, and defer general datapath blocks until workload benefit is measured. The note captures the current 5 × 3 boundary and repair results and keeps G1 as fallback pending full-chip proof.

**Boxes ticked:** none. No architecture contract, RTL, shell, generated fabric or checklist changed. No held-out protocol was touched. Zero extra hold margin removes the legalization failure in this proxy, but the detailed route remains congested and has hundreds of shorts; this does not prove a 5 × 3 fit.
**Next:** Overlay the remaining Metal4 short coordinates against actual macro signal-pin access and the PG stripe rectangles in LEF, GDS and DEF. Verify whether the pattern comes from the proxy pin abstraction or is present in the hardened macro, then adjust scratch pin access/PDN geometry before another full detailed-route pass. Retain x=121.44 as the best placement screen and 0 ns extra hold margin only as a diagnostic. Keep architecture changes scratch-only until a candidate passes full-shell PDN, real macro timing/hold, detailed route, DRC and end-to-end loading.

## 2026-09-30 (session 32: 5 × 3 pin-group diagnosis and open-side screen)
**Done:** Continued from the best x=121.44 reduced-configuration screen. Parsed the cfgmacro LEF, DEF and global-route guides to associate route guides with macro-side pins. Its 154 signal pins are distributed as 36 configuration pins on the west, 36 fabric pins west, 36 east, 31 south (including the system-reset input), and 15 north; the two supply pins are excluded. Across connected fabric-side nets, the summed guide-rectangle span proxy is about 11.1k µm west (36 nets), 27.8k µm east (18 nets), 12.7k µm north (13 nets), and 9.8k µm south (13 nets); 35 of 36 west configuration nets account for about 4.4k µm. This is a route-guide extent estimate, not extracted wirelength: rectangles overlap and the method does not reconstruct Steiner branches. It points to the east-facing active fabric signals as the longest connections into the west-side shell channel.

Tested x=121.44 with the east floorplan blockage removed, 95% global placement target density, routability-driven placement off, and post-GPL/post-CTS repair disabled. The route-only screen reached GRT with **2,705 total layer overflow, 13,770 routing demand, and 132,588 µm wirelength** (`runs/cfgmacro_x121_open/37-openroad-globalrouting/`), versus the earlier x=121.44 proxy screen at 17,745 / 168,940 total overflow / wirelength. This is not an apples-to-apples physical improvement: the placement/repair settings changed and the proxy LEF/GDS and route-only PDN remain. With post-CTS repair enabled, the same open-side setup inserted 446 hold buffers but failed detailed placement on 13 instances (`runs/cfgmacro_x121_two_channels/36-openroad-resizertimingpostcts/`). The extra east-side cell area helps routing, but the design still lacks buffer placement margin.

Reviewed the frozen G1 data and the D-037 successor candidates against public architecture descriptions. G1 remains the strongest verified fallback: 88 LUT4s plus two timers and two shifters, three of four phase-3 designs fitting, and the six-personality sequential showcase. Its measured limits are control-heavy logic, I2C-controller margin (53 MHz modeled against 50 MHz), no demonstrated concurrent link/monitor, and the I2C target not fitting. Existing generic event-lane screens are still rough area estimates and simulation harnesses, not integrated hardware. Competitor repositories describe deadline-driven PIO/sequencer lanes, independent engines and capture/debug, so WARP's useful differentiation would be those temporal engines working *with* arbitrary spatial fabric logic, not a lane count or CRC block by itself. FABulous documentation also warns that route choices trade area against routability; the 4,940/6,656 G1 switch-configuration-bit share makes graph shaping measurable, not an excuse for blind pruning.

**Boxes ticked:** none. The latest 5 × 3 routes remain diagnostic, use a proxy macro and route-only PDN, and do not pass hold repair, detailed route, DRC or end-to-end macro validation. No tracked RTL, fabric, architecture, or shell files changed.
**Next:** Keep the next physical experiment focused on the active east pin bank and buffer legal sites: test an architecture/pin-map variant that routes active user-cell signals toward the shell-facing boundary while preserving the required protocol workload routes, and compare it with the 4 × 3 frozen baseline. In parallel at the architecture-screen level, rank two successor paths: (1) a routability-led fabric/configuration graph and tile remap, and (2) the smallest shared-image, independently timed event lanes with a ready/valid connection to user LUT logic. Require full-chip area, routable fit, timing, and a concurrent workload before preferring either over G1. Keep G1 frozen and do not use the previously opened held-out set as held-out evidence.

## 2026-09-29 (session 31: 5 × 3 macro-boundary and placement screens)
**Done:** Continued the 5 × 3 fit investigation. Read the TT 6 × 4 pin-template DEF and confirmed all 43 chip pins are on the north edge (x=29.76–191.04 µm). A scratch parent-shell proxy with those 43 ports on the north edge reached global routing with **0 overflow**, 149 tracks of demand over 83,898 routing tracks, and 1,238 µm wirelength (`runs/integrated_topedge_proxy/39-openroad-globalrouting/openroad-globalrouting.log`). This isolates the chip-facing boundary as easy to route when presented correctly; the proxy reuses the fabric GDS with a fictional LEF and skipped macro power checks, so it is not integrated-macro or signoff evidence.

Tested opening the east-side floorplan obstruction and moving the full fabric macro left to x=12.0. With ordinary placement settings, OpenROAD global placement diverges; with 95% target density and placement routability inflation disabled, it reaches global routing only if post-GPL repair is disabled. That route screen reports **56,388 overflow and 811,872 µm wirelength** (`runs/right_channel_no_repair/38-openroad-globalrouting/`), worse than the x=121.44 full-macro screen. The run used route-only PDN and is diagnostic.

Tested the reduced-configuration-boundary proxy at x=12.0 and x=50.0 with shell cell area open on both sides. Results are respectively **19,953 overflow / 413,654 µm** (`runs/cfgmacro_right_channel/38-openroad-globalrouting/`) and **18,871 overflow / 422,604 µm** (`runs/cfgmacro_two_channels/38-openroad-globalrouting/`). Both proxy runs skip post-GPL repair and use route-only PDN. The earlier x=121.44 proxy remains the best screen at **17,745 overflow / 168,940 µm** (`runs/cfgmacro_proxy_nix/39-openroad-globalrouting/`). None routes cleanly. Comparing x=121.44 and x=12.0 shows that hiding most configuration wires helps substantially; moving the macro to expose a larger cell channel does not remove the remaining fabric-interface congestion.

**Boxes ticked:** none. These experiments do not pass placement repair, full PDN, detailed routing, DRC, or end-to-end macro validation. No tracked RTL, fabric, architecture, or shell files changed.
**Next:** Start from the x=121.44 reduced-boundary result and inspect its detailed congestion map by fabric-pin group. Build a physically real composite boundary that keeps the configuration adapter inside the macro and exposes only the Tiny Tapeout pins, with legal PG and all shell logic preserved; if its internal 118 fabric-side signals still cannot route, reduce/remap the fabric boundary or revisit the 5 × 3 footprint before promotion. G1 remains the fallback.

## 2026-09-29 (session 30: 5 × 3 shell routing diagnosis)
**Done:** Continued the scratch 5 × 3 integration rather than treating the PDN result as completion. Tied the three unused north/east macro inputs to zero in the candidate wrapper, removing the three floating-input warnings. At the aligned x=121.44 placement, the updated full flow again passes PSM connectivity for both supplies and reaches global routing (`runs/phase_aligned_5x3_x121_tied/`). Global routing still reports 19,065 total overflow and 489,679 µm wirelength. Detailed routing was run through two of its configured 16 optimization passes before stopping it: it reported 37,328 then 34,822 then 33,483 violations, overwhelmingly shorts on Metal2/3/4 (final sampled counts 6,134 / 14,223 / 11,583). This is not a routable or signoff result.

Tested macro relocation to x=110.0 (`phase_aligned_5x3_x110`): global placement reported 215 initial routing overflow and 74% of tiles overflowed; timing repair later could not place seven hold buffers (`DPL-0036`). Tested a centered y=3.78 placement with the macro horizontal PDN phase adjusted (`phase_aligned_5x3_y378_tied`): power connectivity still passes, but global routing is slightly worse (18,997 total overflow, 481,888 µm wirelength) than bottom-aligned x=121.44. Small placement shifts do not solve the routing problem. All experiment inputs and outputs remain ignored scratch under `build/` and `runs/`; no tracked RTL, architecture or fabric was changed.

**Boxes ticked:** none. PDN connectivity is diagnostic only; both legal-placement candidates fail global routing, and detailed routing has tens of thousands of violations.
**Next:** Treat macro/shell signal access and the near-die-sized fabric footprint as the current blocker. Inspect the actual congestion regions and the macro boundary pin map, then model a smaller 5 × 3 tile/edge geometry or a reduced boundary interface as a scratch candidate. Compare it under the same shell and clock before changing tracked architecture; if the 5 × 3 cannot fit the shell at equal area, record a measured fallback rather than claiming it works.

## 2026-09-29 (session 29: phase-aligned 5 × 3 fabric shell probe)
**Done:** Continued physical work on the scratch 5 × 3 candidate. Built per-column phase-shifted hard tile variants while retaining the 190.08 µm logic tile width, then stitched the 5 × 3 fabric at 1120.32 × 703.08 µm. Every modified tile passed its LibreLane detailed-route/KLayout DRC checks; the stitched fabric completed and KLayout DRC is clear (`build/arch_explore/fabric_5x3_phase_aligned/fabric.log`, run `phase_aligned_stitch`). Its VPWR centers are uniformly 12.00 + 109.92k µm and VGND centers are offset by 4.10 µm, fixing the irregular internal supply-column pattern that blocked the prior full-shell candidate.

Corrected a tool-environment mistake in the previous shell probe: it was launched from the SKY130 FABulous checkout, so LibreLane silently ran SKY130 against an IHP macro. The apparent ODB pin-shape loss was an artifact of inspecting that wrong-PDK run. Re-ran with the project CMOS5L checkout and explicit IHP settings. A geometry LEF with Metal4 pin-access windows plus shell-phase-aligned TopMetal1 cross-straps lets the macro's pin columns join the shell mesh; OpenROAD PSM now reports all VPWR and VGND shapes connected. Evidence: `runs/phase_aligned_5x3_xstrap3/09-openroad-generatepdn/openroad-generatepdn.log`.

Resumed at the correct flow step and completed placement, CTS and global routing (`runs/phase_aligned_5x3_xstrap3/`). This is progress, but not a pass: global placement reports divergence/overflow 0.249; global routing exhausts its extra iterations and reports congestion, with total overflow 18,364 and 479,944 µm estimated wirelength. The final metrics also show 50 `PDN-0200` removed shapes (short disconnected shell stubs at the macro boundary and east-side stubs), three floating pins, and a black-boxed macro with no timing libraries. The three floating pins are unused top-edge macro inputs `u_fabric/Tile_X5Y0_A_OUT_top`, `Tile_X5Y4_A_OUT_top`, and `Tile_X5Y4_B_OUT_top`. A scratch relocation to x=12.0 (run `phase_aligned_5x3_x12`) fails before placement: the template's fixed east-side floorplan obstruction leaves too little legal standard-cell area, so GPL reports 1187.83% utilization. This rules out that simple shift without changing the floorplan constraints. The PDN check is only connectivity evidence, not signoff. Scratch trace/config remains under ignored `build/arch_explore/chip_5x3_phase_aligned/`.

**Boxes ticked:** none. Scratch hardening and DRC results are experiments, not phase-gate evidence.
**Next:** Fix the three unused macro input connections in the scratch wrapper, then inspect the global-route congestion map and test another macro placement that respects the east-side obstruction. Determine whether the remaining congestion is inherent to the 5 × 3 macro footprint and shell area. Check a legal candidate with DRC/precheck and power connectivity before treating the PDN bridge as usable. Keep candidate settings scratch-only until those checks pass.

## 2026-09-29 (session 28: 5 × 3 shell and PDN fit probe)
**Done:**
- Corrected the scratch timing-model path: the earlier structural run did fail on a reversed mux delay lookup. A scratch copy of the pinned FABulous package now infers mux direction from mapped pins; this lets the structural model finish. The resulting timing remains structural only and is not evidence for Fmax.
- The candidate architecture compiled the required UART, SPI controller and I2C controller design set, plus `prims2`, using the structural model. A DIV=16 UART bitstream loaded all 842 words in a configured-fabric simulation and emitted `0x96` with correct UART framing. Evidence is under ignored `build/arch_explore/compile_design_set_structural/` and `build/arch_explore/compiled_structural/sim_uart/sim.log`; this does not yet validate the full shell or hardened macro.
- Extracted the hardened 5 × 3 macro LEF and ran the fixed shell through LibreLane floorplanning. The 1087.68 × 703.08 µm macro fits at the scratch placement (x=121.44, y=3.78) inside the 1289.28 × 710.64 µm die. Floorplan run: `build/arch_explore/chip_5x3_fit/runs/candidate_5x3_floorplan/`.
- The full-chip candidate then failed during PDN generation. Its macro has irregular Metal4 supply-column centers (VPWR: 12.00, 121.92, 231.84, 312.00, 421.92, 502.08, 612.00, 692.16, 802.08, 882.24, 992.16, 1072.32 µm; VGND is offset by 4.10 µm), while the current shell PDN uses a uniform 109.92 µm pitch. The checker found no stripes through some candidate macro pins. Evidence: `candidate_5x3_globalroute` in `build/arch_explore/chip_5x3_fit/globalroute.log` and its `21-openroad-generatepdn` log.
- Tried a scratch explicit-stripe PDN configuration using measured pin centers. The first setup used a pitch wider than the die and generated no stripes; after correcting that, the follow-up still generated no macro-crossing stripes. This is an unresolved scratch-script/configuration issue, not evidence that a custom PDN is impossible. Runs and inputs are under ignored `build/arch_explore/chip_5x3_fit/pdn_variant/`.

**Boxes ticked:** no phase-exit boxes. No tracked hardware, architecture, shell, or generated RTL changed. The candidate has design-set compile and fabric-simulation evidence, plus die-boundary fit evidence; it does not yet pass full-shell PDN or routing.

**Next:** debug the explicit stripe generation against the pinned OpenROAD `add_pdn_stripe` behavior and inspect the candidate macro supply pin geometry in OpenDB. If the candidate’s per-tile rail pitch cannot be served by the fixed shell PDN without excessive/invalid Metal4 stripes, reshape the candidate tile/PDN interface so it preserves the shell’s power-grid pitch, then repeat full-shell global routing. Keep G1 frozen and held-out protocols sealed.

## 2026-09-29 (session 27: site-aligned 5 × 3 fabric stitch)
**Done:**
- Corrected the scratch tile pitch to the IHP CMOS5L site/row grid: LUT and PRIM tiles 190.08 × 196.56 µm, north/south tiles 190.08 × 56.70 µm, east/west tiles 68.64 × 196.56 µm, corners unchanged. These dimensions replace the earlier off-grid experiment values; no tracked architecture or tile source was changed.
- Re-hardened the aligned LUT, PRIM and four edge tile classes in the scratch library. All six tile types reached 0 detailed-routing violations, 0 antenna violations and a clear KLayout DRC. Evidence: LUT `RUN_2026-09-29_14-22-57`; `PRIM2T2S_site_row_aligned.log` (`RUN_2026-09-29_15-19-55`), `N_IO_aligned.log` (`RUN_2026-09-29_15-34-46`), `S_IO2_aligned.log` (`RUN_2026-09-29_15-35-49`), `W_IO4_aligned.log` (`RUN_2026-09-29_15-37-06`), and `E_IO4_aligned.log` (`RUN_2026-09-29_15-39-04`), all under ignored `build/arch_explore/tiles_5x3/` and `build/tile_cmos5l/`.
- Stitched the scratch 5 × 3 fabric using those hardened views. The aligned die is 1087.68 × 703.08 µm. LibreLane global routing reported 0 overflow, 0 global-route wirelength/vias (the tile connections are direct abutments), and the full stitched GDS passed CMOS5L KLayout DRC with 0 errors. Run `RUN_2026-09-29_15-49-13` is in `build/arch_explore/fabric_5x3_clock_primpip_macro_site_row_aligned_no_timing/`; use the run directory name in that path as the authoritative ID.
- The normal FABulous physical timing-model generation separately fails after physical checks with `ValueError: Source node(s) not in graph: ['N2END[1]']`. Setting `FABULOUS_TIMING_MODEL: null` in the scratch config allowed LibreLane to finish and save the GDS, DEF, netlist and bitstream specification, but deliberately produced no timing model. The physical macro result therefore does not establish a usable compile flow or any timing claim.
- A follow-up with `FABULOUS_TIMING_MODEL: STRUCTURAL` also passed physical checks but failed while building the timing model: NetworkX reported no path between pins of `W_IO4`'s `S_GBUF_FEED_BEG0` mux. Structural mode is not a working fallback for this candidate either.
- Earlier software evidence still applies to this unchanged switch graph: the candidate compiled UART/SPI/I2C and prims2 bitstreams, and the UART bitstream passed configured-fabric simulation at DIV=16. It is not a new test of the exported macro.
**Boxes ticked:** no phase-exit boxes. This is a clean tile-hardening and stitched-GDS physical feasibility result for the scratch candidate, not full-chip/shell fit or end-to-end hardware validation.
**Next:** fix the candidate's timing-graph reachability at both the pruned LUT input (`N2END[1]`) and W_IO4 mux, regenerate a timing model and rerun compile/simulation. Then test the macro with the fixed shell in a scratch full-chip run. Its larger 1087.68 × 703.08 µm footprint and seven fabric columns require shell/configuration integration before this can be a successor. Keep G1 frozen and held-out protocols sealed.

## 2026-09-29 (session 25: test 5 × 3 physical stitch prerequisite)
**Done:**
- Attempted the full clock-protected 5 × 3 candidate fabric stitch using the pinned CMOS5L FABulous/LibreLane 3.0 flow. FABulous generated the fabric and bitstream specification, but the stitch stopped before floorplanning because `PRIM2T2S.lef` was missing from the scratch tile library.
- Re-ran CMOS5L hardening for `PRIM2T2S` in that library (`RUN_2026-09-29_12-08-16`). Synthesis completed at 33,961.2 µm²; the configured post-global-placement repair step inserted buffering, then detailed placement failed (`DPL-0036`, 1,259 instances). No LEF/GDS was produced. This independently reproduces the known D-031 limitation: the primitive tile has insufficient placement margin for repair in its current footprint.
- The proposed 5 × 3 architecture therefore has no complete set of physical tile views and cannot yet be stitched. No tracked architecture or RTL was changed; G1 and held-out data remain untouched. Scratch outputs are under ignored `build/`.
**Boxes ticked:** the 5 × 3 flow prerequisite was tested and failed with a concrete physical placement error; no physical-fit claim or checklist box added.
**Next:** either reduce the primitive tile's repair/buffering demand or change its footprint/resource mix, then harden every tile class and rerun the full-fabric stitch. Keep the 5 × 3 candidate unpromoted until then.

## 2026-09-29 (session 26: reject cached terminal-count timer)
**Done:**
- Tested an ignored scratch rewrite of `wp_timer` that registers the zero-count predicate and updates it on reset, load, reload, and decrement. Icarus compared the original and candidate count, armed state, and `tc` across 128,000 randomized cycles and passed.
- Under the D-031 repair-enabled scratch flow, candidate synthesis rose from 33,961.2 to 34,945.1 µm² (+2.9%); fanout violations increased from 106 to 112, and detailed placement still failed (`DPL-0036`).
- Found the scratch tile config still contained the D-031 repair insertion. Restored a scratch copy from tracked `arch/tiles/PRIM2T2S/config.yaml` and reran the cached-zero candidate under the normal tile flow (`RUN_2026-09-29_12-24-40`). Synthesis was 34,945.1 µm²; global placement reported routing overflow 3.7273, global routing finished congested, and detailed routing still had 468 violations after seven optimization passes. Stopped during pass 8 because the candidate was not converging to a clean route.
- Rejected the cached-zero candidate: it preserves cycle behavior but increases area and does not harden cleanly. No tracked RTL/configuration or G1 artifacts changed; all candidate sources and EDA outputs remain in ignored `build/` and `/tmp`.
**Boxes ticked:** functional equivalence for the scratch timer candidate passed; physical evaluation failed and does not qualify as a successor.
**Next:** stop tuning this register-based zero flag. Any further timer redesign must first target the high-fanout control implementation without increasing the tile's area, then pass the baseline tile flow and full tile route before integration into a fabric candidate.

## 2026-09-29 (session 24: remove the orphan lane in a scratch candidate)
**Done:**
- Confirmed `clock_protected.csv` is a PIP removal list, not a retained-PIP list. The two `J2END_GH_BEG3` inputs, `N2END1` and `E1END3`, remain legal candidate arcs; my initial interpretation was backwards and is discarded.
- Traced the missing fanout: the candidate removes both outgoing PIPs from `J2END_GH_END3` to `LG_I3` and `LH_I3`. With no surviving sink in the hardened tile, synthesis removes the `J2END_GH_BEG3` mux and its `N2END[1]`/`E1END[3]` inputs. The two failed rows are retained source arcs on an orphaned path, not a signal that the placement flow dropped a live workload path.
- Confirmed none of the preserved UART, SPI-controller, or I2C-controller routes selects these edges. Removing only the two source arcs fails FABulous's unconnected-output check because the four-lane `J2END_GH` jump is still declared. A separate ignored scratch variant narrows that jump to three lanes in a LUT-only Base definition, regenerates the tile at 529 bits (from 530), and regenerates the 5 × 3 CAD/bitstream model.
- Reran nextpnr on the new model for UART, SPI-controller, and I2C-controller. All three routed normally; each FASM compiled to 842 words. The routes changed, as expected from a changed routing graph. Simulated the UART bitstream through `wp_fabric_cfg` and the generated fabric RTL: TX emitted `0x96` LSB-first with correct start and stop bits.
- The first CMOS5L attempt exposed a split Python environment: Yosys could not import `click`, and OpenROAD could not import the FABulous/LibreLane packages. Temporary wrappers in `/tmp` fixed the embedded Python paths. On a clean source tree, FABulous 2.2's tile optimization flow then auto-expanded both the 529-bit candidate and 530-bit baseline from the requested 190.4 × 199.08 µm to their pin-driven minimum footprints (candidate 256.19 × 274.91 µm; baseline 256.34 × 275.06 µm). Global routing failed both: candidate overflow 217 and wirelength 164,577 µm; baseline overflow 219 and wirelength 161,884 µm. The tiny overflow difference and 1.7% longer wirelength give no evidence of physical improvement. This current flow/configuration does not reproduce the earlier 190.4 × 199.08 µm baseline hardening result, so it is not a valid replacement for that signoff; the candidate has no physical signoff.
- No architecture, RTL, or timing files were changed. Scratch artifacts remain under ignored `build/`; the tracked pruning manifest and shared tile definitions remain unchanged.
- No architecture, RTL, or timing files were changed. The previous measured delay distribution remains partial LUT-tile characterization; no candidate Fmax claim is valid.
**Boxes ticked:** root cause found for the two absent timing arcs; three rerouted workloads and bitstream generation passed; UART configured-fabric RTL check passed. The equal-flow physical probe found no benefit and both configurations failed global routing under the expanded pin-minimum footprint; no new timing coverage or physical signoff claimed.
**Next:** reproduce the earlier successful hardening setup and pin-order inputs for both variants before using physical results to accept or reject the cleanup. Keep the cleanup scratch-only until its physical impact is measured in a comparable run. Then characterize inter-tile wires, remaining tile classes, and BEL arcs before regenerating candidate timing files or enabling Fmax.

## 2026-09-28 (session 23: characterize candidate LUT switch delays)
**Done:**
- The first probe accidentally paired an older 375-bit aggressive tile snapshot with the clock-protected candidate and was discarded. Re-ran against the 378-bit clock-protected `RUN_2026-09-28_20-53-31` final RTL, netlist and SPEF; the switch-matrix RTL SHA256 matches both the current tile source and candidate macro copy. A temporary `/tmp` adapter was needed for this installed FABulous/Yosys combination; no active timing or design files were changed.
- Measured 862 of 864 internal LUT-tile PIPs. Two arcs into `J2END_GH_BEG3` failed because `N2END[1]` is absent from the physical timing graph. Delays ranged 0.001–6.089 ns (median 0.766 ns; p95 2.597 ns). Raw rows are in ignored `build/arch_explore/route_prune/timing/lut4x8_clock_protected_slow_delays.csv`.
- The model returned all 202 external LUT-tile PIPs, but 198 are FABulous's fixed 0.001 ns stitched-wire assumption; only four global-buffer twists use extracted tile delays (0.085–0.091 ns). This does not characterize physical inter-tile wires.
- This only characterizes candidate LUT-tile internal switches. It does not time external routing, the other tile classes, or all BEL arcs; no candidate PIPs file was replaced and no Fmax claim is valid yet.
**Boxes ticked:** partial physical characterization of candidate LUT-tile internal PIPs; timing-model integration remains incomplete.
**Next:** resolve the two missing graph arcs; replace the stitched-wire assumption with measured inter-tile delays; characterize remaining tile classes and validate BEL timing; then regenerate candidate timing files and rerun design-set routes. Keep G1 frozen and candidate Fmax disabled until full coverage is validated.

## 2026-09-28 (session 22: exercise candidate design-set workloads)
**Done:**
- Compiled the design-set `hostecho` example on the consistent clock-protected 5 × 3 candidate (23/112 LCs; 842-word WBIT). Its Fmax field is based on placeholder PIP delays and is not a timing result.
- Through the scratch seven-column shell and host SPI protocol, all candidate workload checks passed: UART 8N1 TX of 0x96; SPI controller mode 0 against the reference target (three bytes); I2C controller against the open-drain reference target (write/read/NACK); and hostecho CH_WRITE/CH_READ, USER_STATUS, attention/IRQ, and USER_RESET.
- I2C first exposed a scratch wrapper bug: its per-pin inout outputs were not reduced into the shell's `io_en` vector. Connecting those vectors cleared the unknown outputs and the complete I2C test passed.
- All testbenches, generated shell, WBITs, and results remain under ignored `build/`. No active architecture/shell RTL or held-out design was touched.
**Boxes ticked:** three required design-set protocol smoke/regression paths plus generic host-channel behavior on candidate RTL shell. Not physical signoff.
**Next:** characterize candidate route delays from physical tile/fabric data; measure full 5 × 3 fabric and shell congestion/area; test additional SPI modes and I2C target capacity if feasible; preserve G1 as fallback until those gates pass.

## 2026-09-28 (session 21: validate candidate shell integration)
**Done:**
- Generated an ignored scratch seven-column shell wrapper from the candidate pin map, using the repository's `wp_shell`, synchronizers and frame loader plus the regenerated 5 × 3 macro RTL. The active `src/tt_um_warp.v` remains untouched.
- The first wrapper left the candidate macro's `FrameData`/`FrameStrobe` ports unconnected; this caused unconfigured X outputs. Connected both buses and loaded the candidate UART WBIT over the actual host SPI interface.
- Host SPI load reached LOADED, RUN succeeded, CH_WRITE accepted 0x96, and FAB_OUT0 emitted one valid 8N1 0x96 frame. Start/data/stop checks passed. The unused `h_attention` output was tied low for this UART-only run.
- Scratch wrapper, test, and simulator outputs stay under ignored `build/`; G1, active shell, and held-out set remain unchanged.
**Boxes ticked:** candidate UART test through scratch shell SPI/configuration/run path. This is RTL simulation only, not physical integration.
**Next:** automate candidate wrapper generation and add candidate passthrough/host-channel coverage; check the I/O map for all shell roles; calibrate PIP delays before timing claims; then evaluate full macro/shell physical feasibility and congestion.

## 2026-09-28 (session 20: confirm candidate UART simulation)
**Done:**
- Traced the earlier 0x96 payload mismatch to the scratch testbench: it subscribed to `negedge tx` after the valid/ready handshake, so it could miss the start edge and sample later bits at the wrong phase. The primitive shift register had loaded 0x96 and was emitting the correct LSB-first sequence.
- Re-armed the edge observer before asserting `h_wvalid` and added explicit assertions for start, all eight data bits, and stop. The candidate UART bitstream passed after configuration through `wp_fabric_cfg` into the regenerated 5 × 3 macro RTL.
- Together with session 19's passthrough test, confirms a dynamic fabric I/O/LUT path and one primitive-based protocol workload on the candidate. This remains direct macro-level RTL simulation, not shell/top-level integration or physical signoff.
- All harnesses and outputs remain ignored scratch artifacts under `build/`; G1 and the held-out set remain untouched.
**Boxes ticked:** UART direct macro RTL load-and-transmit simulation.
**Next:** see session 21 for scratch shell integration evidence; check the full candidate I/O map and physical feasibility before advancing.

## 2026-09-28 (session 19: validate candidate fabric logic path)
**Done:**
- Compiled a scratch combinational passthrough (`FAB_IN0` → `FAB_OUT0`) on the consistent clock-protected 5 × 3 candidate; routing and bitgen succeeded (842 words).
- Loaded that exact WBIT through `wp_fabric_cfg` into the generated candidate macro RTL. The routed output followed input values 0 → 1 → 0 after configuration. This confirms a basic candidate config/LUT/I/O path in simulation; it does not explain or clear the UART payload mismatch.
- Scratch design and testbench remain under ignored `build/`; active G1, shell, and held-out set unchanged.
**Boxes ticked:** first candidate dynamic logic-path proof; UART/primitive behavior and shell integration remain open.
**Next:** inspect the UART compile mapping and candidate primitive/control pins, then isolate the wrong payload bits with targeted probes. After that build a scratch seven-column shell/config integration; no timing claims until candidate PIP delays are calibrated.

## 2026-09-28 (session 18: audit candidate tile/model consistency)
**Done:**
- While preparing RTL bitstream-load simulation, found the reduced candidate artifacts do not share one tile definition: the current clock-protected tile RTL has 530 configuration bits, its separate software-generation tile copy has 527, and the generated scratch macro RTL still has 566.
- Replaced the ignored software-generation tile artifacts from the exact hardened tile, regenerated the FABulous model and feature map, and copied the matching tile RTL into the scratch macro. The candidate RTL declares 530 bits and its config map spans 0–529.
- Recompiled UART, SPI-controller and I2C-controller on the consistent protected 5 × 3 model. All route and bitgen; each 842-word bitstream independently matches FASM-to-word regeneration and the five-row frame check. The 4 × 3 and aggressive 5 × 3 routeability claims remain unverified. Candidate timing PIPs still have placeholder delays; ignore Fmax.
- Started a direct RTL load-and-transmit simulation against the regenerated macro. The first harness released reset too early; after holding user reset through configuration it reached host-ready and emitted the UART start bit, but the transmitted byte failed its data-bit check. Functional operation is not demonstrated. The full shell also needs seven frame columns and a new pin integration; the frozen shell supports six.
- No active architecture, macro, or shell files changed; G1 and held-out set remain untouched.
**Boxes ticked:** consistent protected candidate model and software route/bitgen checks only; no dynamic-functional or physical integration gate advanced.
**Next:** debug the direct configuration simulation, then build a scratch shell with the seven-column decoder and candidate pin map. Generate candidate-specific realistic PIP delays before making timing claims or attempting full-fabric hardening.

## 2026-09-28 (session 17: validate clock-protected switch pruning)
**Done:**
- Corrected the session 15 routing claim: its identical-FASM check used a stale nominal-corner PIPs file, so it did not prove routing through the pruned graph.
- Initially reported regenerated candidate full-fabric models, protocol routes and frame checks. Session 18 found stale tile copies, then rebuilt and revalidated the protected 5 × 3 model from the exact hardened tile; see session 18 for current evidence.
- Re-hardened the clock-protected tile at 190.40 × 199.08 µm. It synthesizes to 29,820.5 µm² / 1,580 cells, places at 88.8% utilization, completes the pinned tile flow, and has a clear KLayout DRC result. The aggressive candidate was 29,824.2 µm² / 1,595 cells at the same utilization.
**Boxes ticked:** tile-only PPA/DRC screen; no architecture-level gate advanced.
**Next:** see session 18 for corrected current status.

## 2026-09-28 (session 16: make pruning screen reproducible)
**Done:**
- Added `spikes/route_prune/removed_pips.csv` as the exact 313-choice manifest for the measured route-pruning candidate, plus a scratch-only script that applies it to every FABULOUS_LC tile and rejects removal of any selected FASM choice at those sites.
- Reproduced the ignored candidate `.FABulous/pips.txt` byte-for-byte (3,443 internal PIPs removed across 11 LUT tiles). The preserved UART, SPI-controller and I2C-controller routes remain unchanged; this is manifest replay, not a general-purpose topology optimizer.
- Updated the architecture research report with the reproducibility path and the current limits. G1 stays frozen; the held-out protocols were not used.
**Boxes ticked:** none; the physical benefit is promising, but a full-fabric feature map, router and shell flow have not been regenerated for this architecture.
**Next:** develop broader non-held-out route coverage and complete the tile-to-fabric configuration/compiler round trip before deciding whether to pursue this as the new 5 × 3 baseline.

## 2026-09-28 (session 15: physically measure route-option pruning)
**Done:**
- Kept G1 frozen and all edits inside ignored `build/` scratch copies while testing a fabric-native switch-matrix reduction.
- Removed 313 of 1,272 local switch options per LUT tile (24.6%) based on routes present in the current UART, SPI-controller and I2C-controller design set. The initial compiler run appeared to produce byte-identical FASM, but it used stale nominal-corner PIPs and was invalid as route-preservation evidence; see session 17 correction.
- Regenerated the LUT tile's scratch configuration-memory map after removing stale generated mapping data. At the 190.40 × 199.08 µm fifth-column target, synthesis area fell 14.4% (34,831.7 → 29,824.2 µm²; 1,825 → 1,595 cells). The pruned tile completed placement at 88.8% utilization and the tile flow through KLayout DRC; the unpruned tile failed placement at 106.507%.
- Tried the remaining I2C-target design-set workload in both candidate and baseline architectures. It exceeds the current 88-LC logic capacity in both, so it cannot establish a routing regression or win.
- Recorded run paths, metrics and limits in `docs/reports/architecture_research.md`. No held-out protocols were inspected, no G1 architecture or macro changed, and the reduced tile's complete bitstream/configuration integration remains unvalidated.
**Boxes ticked:** none; this is a promising scratch experiment, not a complete architecture candidate. Known-workload route preservation does not establish general routability.
**Next:** make the pruning procedure reproducible, expand preservation evidence with generated non-held-out designs and a compiler/configuration-map round trip, then test full-fabric routeability at equal clock/area. Do not merge pruning into G1 or declare the fifth column feasible until the real tile map, compiler, full fabric and shell hardening agree.

## 2026-09-28 (session 13: test fifth-column tile dimensions)
**Done:**
- Checked the current phase 3 gate and retained G1 as the frozen baseline; successor work remains exploration and no active `arch/`, `macro/`, or shell hardware was modified.
- Retried the current LUT4 tile hardening in an ignored build copy at the proposed fifth-column dimensions, 190.40 × 199.08 µm. The pinned CMOS5L flow generated the tile and reached OpenROAD global placement, then stopped with `GPL-0301`: reported utilization was 106.507%, above 100%. This rejects the unchanged tile at that geometry before detailed routing; no DRC, timing, or GDS result exists.
- Recorded the negative feasibility result and reproduction details in `docs/reports/architecture_research.md`. The result makes physical configuration-cell/pin remapping the next high-value experiment; it does not establish that remapping will recover enough area.
- Attempted to query recent `efpga` CI with `gh run list`; the environment could not connect to `api.github.com`, so current remote CI status could not be refreshed. The last recorded pushed-baseline CI remains the all-green set in session 12.
**Boxes ticked:** none; this scratch tile did not pass placement, and no phase gate was advanced.
**Next:** inspect the generated tile/configuration and placement reports, then test bounded config-cell/pin mapping changes in the ignored build copy. Require the tile to complete place-and-route with meaningful margin before attempting 5 × 3 fabric generation. Keep G1 unchanged.

## 2026-09-28 (session 14: inspect tile fit and event-tile integration limits)
**Done:**
- Read the current run's placement report rather than inferring from the headline utilization: 35,943.264 µm² movable cell area + 1,160.105 µm² pin-density adjustment over 34,836.480 µm² core. Eliminating pin-density overhead alone would still leave cell area 3.18% over capacity; with current overhead the footprint needs at least 6.11% recovery to pass 100% utilization, before routing margin.
- Checked FABulous 2.2's documented custom-tile generator limit: 32 internal inputs and 8 internal outputs. The proposed event tile's 29 inputs fit, but its 32 outputs do not fit that stock generation path. A bespoke matrix and matching compiler/bitstream support would be needed; no such integration was built.
- Updated `docs/reports/architecture_research.md` with the exact physical evidence and event-tile tool constraint. No active hardware changed.
**Boxes ticked:** none; the tile still fails global placement, and the event-tile path is not compiler-ready.
**Next:** prioritize reducing LUT-tile cell footprint (especially switch/configuration logic) while keeping routing checks and bitstream semantics; do not expect pin-order changes alone to make the fifth-column target fit. Reassess the event-lane option only after a generated tile can be compiled and configured by the real flow.

---

## 2026-09-28 (session 12: test a fabric-coupled event-lane direction)
**Done:**
- Deepened the closest prior-art check. PRISM's published IHP design already describes two independent 16-state shards, loaded from Verilog state tables, with shifters, counters, FIFOs, CRC, edge capture/sampling, debug and optional trace. Updated `docs/notes/prior_art.md` and the research ranking: lane count, shared code, CRC and capture are not WARP differentiators by themselves.
- Extended `spikes/event_lanes/` with per-lane ready/valid byte channels and `TX_SHIFT`. Added `warp_byte_bridge.v`, a one-byte elastic buffer with a configurable XOR transform, and a concurrent receive-transform-transmit test. All three lane/bridge testbenches pass; Verilator lint is clean.
- Compiled the user bridge through WARP's existing G1 flow: 17/88 LUT4s, 18/36 IOBUFs, 722 words, nextpnr estimated Fmax 212.77 MHz at `nom_slow_1p08V_125C`. This validates the user-logic block independently, not an integrated eFPGA/event-macro data path.
- Re-ran the area screens with channel state included: 8-word writable image 33,451 µm²; 8-word static image plus estimated configuration latches 26,157 µm²; 16-word writable image 51,272 µm²; 16-word static image plus latches 37,387 µm². These remain SG13G2 screening estimates, not CMOS5L routed results.
- Updated `docs/reports/architecture_screen.md`, `docs/reports/architecture_research.md`, and the successor exploration to emphasize the required proof: user Verilog must process bytes between independent pin-timing lanes through the actual fabric.
**Boxes ticked:** none; the ready/valid bridge compiles as a separate G1 user design, while the event-lane/fabric composition and physical tile remain unimplemented.
**Next:** make the static instruction image part of a generated FABulous configuration map, route the ready/valid interface through the real fabric, then load both together and run the transform test end-to-end. Keep the physical tile-remapping experiment as the higher-confidence path to more general eFPGA capacity; select neither candidate without equal-area physical evidence.

---

## 2026-09-28 (session 11: prototype shared-image event lanes)
**Done:**
- Kept G1 frozen and prototyped the first successor block under `spikes/event_lanes/`: two independent protocol-neutral event lanes with per-lane timing/state and a shared instruction image.
- Wrote the instruction/cycle contract before implementing RTL. Added masked drive/release, pin waits, 16-bit delays, sample, conditional branch, jump, halt, and generic shift-in/shift-out operations. Both lanes keep separate output requests and observe the sampled pin inputs; no pad arbitration is inferred.
- Implemented two storage policies: writable program RAM with a write lock while either lane runs, and a static-image wrapper intended to use the fabric's configuration latches.
- Added pin-level testbenches for each policy. `spikes/event_lanes/run.sh` passes both concurrency tests and warning-clean Verilator lint; Yosys mapped the RAM and static variants at 8 and 16 words using the SG13G2 typical Liberty.
- Area screen (`docs/reports/architecture_screen.md`): 8-word runtime RAM 33,067 µm²; 8-word static image including 192 estimated config latches 25,849 µm²; 16-word RAM 50,263 µm²; 16-word static image including 384 estimated config latches 36,411 µm². Cross-library comparisons to a CMOS5L tile are explicitly approximate. Static configuration saves ~22% at 8 words but has no bitstream compiler or fabric integration yet.
- Updated `docs/design/ARCHITECTURE_EXPLORATION.md`; no `arch/`, `macro/`, shell RTL or active hardware changed.
**Boxes ticked:** none; this is a tested, synthesized candidate spike, not a routed tile or successor selection.
**Next:** map static instruction bits into a generated FABulous config interface; then add a bounded generic data/event channel between the lanes and LUT fabric and prove a concurrent lane-plus-transform workload. Compare against the same workload on G1 before changing the active architecture. Do not tune against the previously opened held-out protocols.

---

## 2026-09-28 (session 10: reopen architecture exploration)
**Done:**
- Read the new `WARP_Branch_Review_and_Competitor_Recommendations.md` with the current fabric definition, profiling, G0/G1 results, physical constraints and decisions. Confirmed the user's revised objective: improve the programmable fabric for broad communication workloads while keeping hardware primitives protocol-agnostic.
- Reopened phase 3 exploration under D-037. G1 remains the baseline and frozen fallback; no RTL, architecture, macro or pinout hardware changed.
- Wrote `docs/design/ARCHITECTURE_EXPLORATION.md`: candidates include a denser LUT fabric, a hybrid LUT fabric with generic independently paced sequencers, and a small sequencer control architecture; defines equal-area metrics, workload coverage, a fresh sealed holdout, and gates through physical hardening.
- Measured the generated G1 configuration structure: 4,940/6,656 configuration bits (74.2%) are switch-matrix choices, a concrete target for routability-preserving pruning. Added the caveat that bit counts do not predict area savings.
- Synthesized a temporary two-lane generic event sequencer in ignored `build/arch_explore/`, then consolidated host programming onto one shared address/data bus: 16 × 24-bit instructions per lane maps to 73,589 µm²; 8 instructions per lane maps to 42,553 µm² in SG13G2 typical Liberty. That is about 2.04 vs. 1.18 G1 LUT-tile standard-cell area equivalents, before routing and integration. Logged the assumptions and limitations in `docs/reports/architecture_screen.md`.
- Extended the probe with a shared writable instruction image and independent fetch ports. The two-lane model maps to 47,992 µm² for 16 words and 30,054 µm² for 8 words, about 35% and 29% smaller than private memories. This supports sharing code across replicated endpoints, though the toy engine's timing semantics are incomplete and its cost is not a candidate-core estimate.
- Deeper online research found FABulous-specific physical optimization: a peer-reviewed tile study reports 21.7% area reduction from configuration-cell and interface-pin remapping on SkyWater 130 nm/Innovus. WARP uses IHP CMOS5L/OpenROAD, so the result must be remeasured. Geometry analysis found that 190.4 × 199.08 µm tiles could make a 5 × 3 grid fit with the model's 200 µm shell reserve, enabling 112 LUT4s with one primitive tile (vs. 88 today). This is an ambitious physical target with little utilization slack, not a fit result.
- Confirmed the installed FABulous 2.2.0 package has a tile-area optimization flow and configurable pin placer; WARP's current Nix tile runner fixes tile sizes and its generated G1 feature-to-frame map is linear. Searched the pinned Nix plugin source: it has no optimizer or FABulous pin-placement step, and its LibreLane/OpenROAD/Yosys versions differ from the installed FABulous package. A direct switch to the newer flow is therefore unverified. The report now records a single-tile scratch backport or fixed-geometry sweep as the next physical gate.
- Reviewed current competition entries more closely. Tempo documents a tested two-engine build with capture and timing features; Abagel's similar CPU-plus-lane concept is currently a proposal with estimated block costs. This means WARP's differentiator needs to be the spatial eFPGA coordinating user-defined parallel monitor/transform logic with timed I/O, not lane count or timestamping alone. Research and evidence boundaries: `docs/reports/architecture_research.md`.
- Researched FABulous/OpenFPGA architecture flexibility and the case for custom mux/configuration cells; reviewed public sequencer-based competitor descriptions as self-reported claims. Sources and their implications are linked in the architecture screen report.
- Corrected `tools/areamodel/model.py`: it still used the phase 1 1.07× primitive-tile estimate even though D-026 measured 0.97× LUT-tile standard-cell area. The model now uses the hardened values (35,094 vs. 36,047 µm²) and states that both tiles occupy the same footprint; `capacity.md` labels its earlier estimate historical.
- Reviewed current competing architecture descriptions: Tempo documents two independently paced engines plus capture; GP_PAE documents multiple sequencer lanes and concurrency. These are self-reported public project descriptions, not independently rerun results. Competition brief states uniqueness/general reprogrammability are goals and 6x4 is the current maximum while 8x4 remains a possibility.
- CI on `ee259cb`: docs 36491754412, formal 36491754401, unit 36491754404, lint 36491754317, test 36491754349, fabric 36491754296, and GDS 36491754364 all passed. The GDS run includes successful hardening, TinyTapeout precheck, viewer, and gate-level `gl_test` (completed 23:16:39 UTC). The pushed G1 baseline is fully green.
**Boxes ticked:** none for the reopened architecture exploration; the first low-cost synthesis screen is not a routed or physically hardened candidate.
**Next:** test whether the FABulous generation/hardening flow can safely optimize tile config-cell placement and interface pin placement in a scratch copy, then harden a 190.4 × 199.08 µm tile. This determines whether the fifth fabric column is feasible before spending time on a larger event engine. Also formalize shared-code engine timing, then seal a new holdout before tuning any successor. Keep G1 unchanged until a successor clears the gates.

---

## 2026-09-28 (session 9: close phase 4 CI; phase 5 reproduction and shell verification)
**Done:**
- CI from the Phase 4 push completed green: `gds`/precheck/`gl_test` 36451108163; `fabric` 36451328356 (including co-simulation); `unit` 36451328364, `lint` 36451328384, `test` 36451328368, `docs` 36451328775. No committed hardware files changed since `hw-freeze` (`git diff --name-only hw-freeze..14e7063 -- src arch macro info.yaml` empty). Phase 4 checklist and summary finalized; Phase 4 complete.
- F3 FIFO formal proof passes locally at depths 2 and 4 (`scripts/formal.sh f3_fifo.sby`, `abc pdr`). Independent shell transaction model plus pyuvm environment passes seed 1 locally: 2,288 transactions, 2,851 response bytes, 228 configuration words, 137 design-side bytes, no mismatches, 79/79 coverage bins. Pinned pyuvm and added the checks to `unit` CI and `scripts/check_all.sh`. The mutation report now records 11/11 killed locally.
- Filled Phase 4 CI IDs into `docs/CLAIMS.md` and `docs/EVIDENCE.md`; completed the user guide, prior-art comparison, README and Tiny Tapeout datasheet draft. `docs/summaries/PHASE5.md` is in progress.
- Clean source export of 14e7063 plus the proposed README and Phase 5 sources in `/tmp/warp-repro.vVyH1n`, fresh Python 3.12 venv: `scripts/check_all.sh` passed (377 pytest, all default protocol RTL tests, 30 idle-fabric chip tests, 2 primitive tests, pyuvm 2,288 transactions/79 bins); all 11 committed bitstreams rebuilt identically; UART compiled; UART co-simulation passed; fabric RTL chip suite passed 30/30 including the showcase. Found two README gaps (non-executable fetch script; Python 3.12 required) and BUGS #20 (stale idle-fabric simulator reused for the real fabric); fixed instructions and separated simulator build paths. This is a clean source export and venv on the same development machine, not a separate clean machine/container.
**Boxes ticked:** Phase 4 exit checklist (CI IDs above); Phase 5 claims audit and user-guide/datasheet items (`docs/design/phases/PHASE5_EVIDENCE_DOCS.md`).
**Next:** repeat reproduction in a clean container; finish the evidence report's local-measurement run-ID audit; get CI on the uncommitted Phase 5 changes before closing Phase 5.

---

## 2026-09-27 (session 8: G0 chip green in CI; G1 primitives usable; UART, SPI, I2C controller fit G1)
**Done:**
- **G0 chip in CI, all green** (e5b1f98): `gds` + precheck + `gl_test` 17/17 in 36353540402 (45.8 min; setup +10.63 ns, hold +0.121 ns, DRC/LVS/antenna 0, IR drop 0.77 mV); lint, unit, test, docs, formal, fabric green. D-025 evidence and the hardening table updated.
- **G1 hard primitives** (D-026): `wp_timer`, `wp_shift` (`arch/prims/`), proven equal to a spec model (F4, `formal/f4_prims.sby`, k-induction), white-box tested against `tools/refmodels/prims.py`; primitive tile `PRIM2T2S` hardened at 0.97 × a LUT tile; G1 fabric stitched (`macro/warp_g1`, same size and ports as G0, KLayout DRC 0, antenna 0).
- **Compile flow support:** `WP_TIMER`/`WP_SHIFT` wrappers and BEL cell library (`tools/compile/prims/`), mapped, placed and configured (`examples/prims2`: RELOAD and LEN bits in the FASM, accepted by bitgen). `compile.protocols` takes `--arch`, `--only`, `--set`.
- **BUGS #15:** placement failed with free LCs because each LUT tile has one clock enable and one set/reset; the flow now turns enables/resets used by < 4 flip-flops into logic (`dfflegalize -mince/-minsrst`). Every design got smaller.
- **Protocols on the primitives** (`PRIMS=1`; plain form kept): UART, SPI controller, I2C controller rewritten; all RTL tests pass in both forms (UART DIV 16/13/5 + sigrok, SPI 4 modes × 2 speeds, I2C Q 2/4/5). I2C controller also lost its own synchronizers (ARCHITECTURE §6) and three wait states. Unit CI runs the `PRIMS=1` configurations.
- **Results:** G1 places UART 29, SPI 47, I2C controller 70 of 88 LCs (69–124 MHz slow corner); G0 places only SPI (86/96). `docs/reports/g1_results.md`, `g0_results.md` rewritten.
**Boxes ticked:** full 6x4 hardening of shell + G0 (CI 36353540402); protocols compiled onto G0 (`g0_results.md`).
**Later the same session:**
- CI on b438814: `fabric` failed: the committed test bitstreams predate the BUGS #15 flow change, and `prims2` needs G1 (fixed by the G1 switch, which rebuilds them). The `gds` run it started re-hardens the unchanged G0 (arch/prims touched `arch/**`).
- **G1 into the chip (D-027):** `arch/CURRENT` = warp_g1, ARCH_VERSION 0x0003 (shell, host software), `src/warp_g1.v` black box, `config.json` macro files, test stub and settle files regenerated, RTL fabric model includes `arch/prims`. New chip tests `test_prims` (both block types configured by a real bitstream) and `test_uart` (the design-set UART on the primitives through the host interface; test bitstream `uart16`). Local: RTL suite **19/19**, stub 13 + 6 skipped, F1 PASS (k-induction), pytest 63, lint clean.
- **I2C target** rewritten (hard shift register for the bus byte, shared register ports, no own synchronizers): 6/6 tests in both forms at Q 4/6/11; 205 → 184 LCs (G0), 169 (G1); does not fit either, even with 2 registers (123 on G1) — generic Yosys LUT4 mapping agrees, so it is the design's size: phase 3 (register-file tile or larger fabric).
- BUGS #16 (`sda_o` undriven after the rewrite, found by lint): `lint` now checks all protocol designs in both forms.
- G1 pre-flight: overflow 20, stripes OK, 21 detailed-routing violations all on `clk` at the strip above the fabric (G1 LEF identical to G0's; D-027 records it and the fallback). Pushed as d6f5dcd; CI hardening queued behind the G0 re-run.
- **Protocol chip tests:** `test_spi_ctrl` and `test_i2c_ctrl` (reference target models on the pins, open-drain bus for I2C) through the host interface, bitstreams `spi8`, `i2c8`; pass on the fabric RTL. `compile.protocols --require`; the `fabric` workflow compiles every protocol and fails if UART, SPI or I2C controller stops fitting.
- CI on d6f5dcd (G1 in the chip): lint, unit, test, docs, formal, fabric green; gds (G1 hardening) running.
- **BUGS #17 / D-028:** nextpnr left every path through the hard primitives untimed, so the G1 Fmax figures were optimistic. Primitive arcs from OpenSTA (`tools/timing/`, slow corner, ×1.5 margin) into `placement_estimate.txt`; the compile flow now uses nextpnr 0.11.1 (OSS CAD Suite 2026-09-27, `scripts/fetch_nextpnr.sh`), which reads them (identical FASM to 0.10-82 without them). Timed: UART 93–95 MHz, SPI 83.2, I2C controller 58.0, all above 50 MHz. Test bitstreams rebuilt; RTL suite **21/21**; pytest 69.
- **G1 chip green in CI** (36367067731 on d6f5dcd): gds 43.6 min, precheck pass, gl_test **19/19** (incl. `test_prims`, `test_uart`), routing DRC/LVS/antenna 0, setup +10.73 ns, hold +0.143 ns. D-026 and D-027 Accepted; D-029 (G1 is a valid fallback); `docs/reports/formal.md`; `docs/summaries/PHASE2.md` (in progress).
**Boxes ticked:** exit items: shell + G1 hardened, gl_test with real bitstreams, g0_results for every protocol, formal summary, fabric workflow green, decision point.
- **Timing cross-check** (`tools/timing/tile_check.sh`): STA of the hardened `PRIM2T2S` tile against the model. Clock-to-out bounded (6.79 vs 15.17 ns); the timer's in-tile setup (4.0 ns, a NOR with 33 loads) exceeded the standalone arc ×1.5, so setup/combinational margins are now ×3.0 (input side 8.06 vs 12.06 ns). Timed estimates: UART 90.7, SPI 78.0, I2C controller 53.0 MHz. Timing-model box ticked (documented conservative model).
- CI on fe4cac8: `fabric` failed with exit 126: `scripts/fetch_nextpnr.sh` committed without the executable bit (created from Windows); the workflow now runs it with `bash`, and the three new scripts get `git update-index --chmod=+x`. gds (21-test gl_test) running.
- CI gds on fe4cac8 (36372341186): gl_test **21/21** incl. `test_spi_ctrl`, `test_i2c_ctrl` on the hardened chip; pin-level protocol tests box ticked.
**Next (superseded):** push the margin fix + fabric fix + rebuilt bitstreams; all CI green closes phase 2 (then PHASE2.md final).
- **Phase 2 complete (2026-09-28):** all CI green at 2befd16 (gds/precheck/gl_test 21/21 36376994834); exit boxes ticked; `docs/summaries/PHASE2.md` final.
- TT linter warnings reviewed: `PINMISSING` VPWR/VGND on the macro (TT's black box has power pins; power via PDN_MACRO_CONNECTIONS, LVS 0: harmless), `WIDTHTRUNC` on Frame_Data_Reg's Row (32-bit genvar expression into a 5-bit parameter; values fit), `SYNCASYNCNET` on rst_n: BUGS #18.
- BUGS #18 fixed locally: reset synchronizer (+ separate config-path reset flop); full-top lint without waivers clean of SYNCASYNCNET/WIDTHTRUNC; suites 21/21 (RTL) and 13+8 skipped (stub); F1 PASS.
- Pre-flight of the fix: overflow 37, stripes 22/22, 36 detailed-routing violations, all on `clk` where it reaches the fabric's clock pin on the macro's west face (y ≈ 640 µm) and the local router cuts onto the macro's Metal4 blockage. Same net and area as the 21 of the G1 switch, which CI (LibreLane 3.1) routed with 0 violations three times on this floorplan: a local-vs-CI router difference for this net; CI decides. Fallback if CI fails there: room for the clock pin (macro one row lower or a keep-out west of the pin) as its own hardening.
**Phase 3 started (2026-09-28):**
- `tools/profiling/limits.py` + `docs/reports/g1_limits.md`: on G1 the counters/shifting are absorbed; control logic is what is left; control sets (3–7) and primitive count are not limits; every critical path goes through a primitive; the I2C target would not fit even with a register file.
- D-030 candidate 1 (registered terminal count): F4 re-proved, `tc` 2.98 → 0.88 ns at no area cost, but the I2C controller (the worst design) is limited by paths into the timer: 53.0 → 52.1 MHz: not kept alone (parked in build/c1/parked).
- Root of the timer's slow input path: the primitive tile's hardening config (copied from the tile library) disables resizer/repair, so a NOR drives 33 loads unbuffered.
- D-031 candidate 2 (primitive tile with design repair): three local tile runs; repair works only once inserted as a step (the tile driver applied removals only), then detailed placement fails: the 92 %-full tile has no room for buffers. Not feasible; config restored; `tile_check.sh` now picks the newest completed tile run.
- CI on 3047dea (BUGS #18 fix): all green; gds/precheck/gl_test 21/21 (36383587262), setup WS +12.48 ns.
- Organizers' reply (D-032): eFPGA accepted; software side required (flow, loading, UART/SPI/I2C examples); phase 4/5 plans updated.
- `docs/reports/architecture_comparison.md` + chart; D-033 final architecture G1.
- User kept hardware open for the I2C target: D-034 register-file tile measured (169 → 123 LCs, still no fit); user then chose to freeze and drop the I2C target (D-035).
- Phase 3 exit boxes ticked except the tag; `docs/summaries/PHASE3.md` drafted.
- User tagged `hw-freeze` → 3047dea. CI on a578359 all green: **phase 3 complete**; `docs/summaries/PHASE3.md` final.
**Phase 4 started:**
- Demo-board loader `tools/board/warp.py` (MicroPython + CPython): checked load, run control, host channel, FAB_IN pins, ttboard glue; `tools/board/tests` 270 pass (equal to the reference host); `test_board_loader` (the module's own code drives the chip model through cocotb bridge/resume) passes on the fabric RTL. Not tested on hardware.
- **End-to-end examples** (D-032): `compile --set NAME=VALUE`, report records params; `tools/board/examples.py` (UART send/recv, SPI transfer, I2C write/read/probe); `docs/EXAMPLES.md` (pins, commands at 10 MHz, wiring, what is tested); the board code tested against the chip model for all three (`test_board_loader`, `test_board_examples_spi`, `test_board_examples_i2c`). BUGS #19: parked `uo_out` pins assert active-low outputs (SPI CS_N) while stopped; documented, fix at the pin map (bidirectional pin + pull-up). Loader refuses to load while RUNNING with a clear message.
- **Held-out set unsealed and evaluated** (`docs/reports/heldout_results.md`): models first from each spec (`tools/refmodels/{ws2812,onewire,swd,can}.py`, each tested on its own), then designs in both forms:
  - H1 WS2812: fits (32/88 LCs, 54.3 MHz after tying the period timer's enable high; G0 82); chip test `test_ws2812` passes. Needs a host streaming a byte per ~10 µs (no pixel buffer).
  - H2 1-Wire: fits (77/88, 54.5 MHz; G0 126 = no fit) after a restructure with the second timer (116 → 77); chip test `test_onewire` (READ ROM, CRC) passes.
  - H3 SWD: fits (44/88; G0 61) as a bit engine with packets in `tools/board/swd.py`; chip test `test_swd` passes.
  - H4 CAN 2.0A: RTL correct (3/3 vs reference nodes), **does not fit** (207/88; G0 241).
- Showcase replaced (D-036): six protocols switched at run time on one chip (`test_showcase_protocol_switching` passes). Robustness: `test_corrupt_load_over_running_design`, `test_uart_input_phase` pass; mutation campaign `scripts/mutation.py` 8/8 killed (`docs/reports/mutation.md`); co-simulation `test_internal/cosim` (UART source RTL vs its bitstream on the fabric: identical TX waveforms, equal RX) passes. Local: chip suite 27/27, pytest 377, lint 8 protocols × 2 forms clean, bitstreams reproducible. `docs/summaries/PHASE4.md` drafted.
- Pushed (76860b1, 14e7063); CI: unit, lint, docs, test green; gds (76860b1) and fabric running.
**Phase 5 started in parallel** (the user asked; phase 4's only open exit items are its CI runs): `docs/CLAIMS.md` audited (C1–C10), `docs/USER_GUIDE.md`, `docs/EVIDENCE.md` (draft), `docs/reports/prior_art_comparison.md`, README rewritten, `docs/info.md` + `info.yaml` pinout comment for G1; clean-checkout reproduction running.
**Next:** CI results → close phase 4 and fill the pending run IDs; clean reproduction; PHASE5 summary.
**Next (superseded):** after the G1 hardening result, push the protocol chip tests + timing work (touches `test/` and `macro/`, so one more hardening, which also gives gl_test evidence for the 21 tests); then phase 2 exit: timing cross-check, per-tile equivalence plan, PHASE2 summary.

---

## 2026-09-27 (session 7: phase 2 started: shell, compile flow, real bitstreams)
**Done:**
- **Shell** (ARCHITECTURE §2–6): `wp_spi_target`, `wp_shell` (commands, checked loader, run control, 2-entry host channel FIFOs), `wp_crc32` (bit-serial), `wp_fifo`, `wp_sync`; new top-level pinout; FABulous's bit-bang receiver removed. Spec clarifications D-021.
- **Host software** `tools/host/protocol.py` (from the spec): transactions, STATUS decode, CRC, architecture check before loading.
- **Formal:** F1 output isolation proven unbounded (k-induction); F2 bounded (BMC 84) against an independent shadow loader. The F2 cover trace exposed **BUGS #12** (an empty load reached LOADED), now fixed. New `formal` workflow.
- **Compile flow** `tools/compile/` (D-022): pin map → wrapper → Yosys → nextpnr (slow-corner timing) → WARP bitgen → `.wbit` + report. `arch/warp_tiny/` (fabric.csv, pins.csv, arch.yaml). **BUGS #13**: FABulous's bitgen drops the global-clock mux selects; our generator fixes it and matches upstream word for word elsewhere.
- **Real bitstreams on the whole chip:** `test/test_bitstream.py` loads `counter4` and `logic4` over SPI and checks them at the pins, on the fabric RTL (`WARP_FABRIC=rtl`, new job in `fabric`) and on the hardened macro's gate-level netlists (`GATES=yes`, what CI `gl_test` runs). Gate level needed D-023 (settle X routing loops; no reload over a running configuration).
**Boxes ticked:** host interface, loader, run control, IO cells, host software, compile flow, host rejects other architectures, F1, F2, `gl_test` with two real bitstreams. **CI on acc3af3/2faaa36 all green:** `gds` + precheck + `gl_test` 16/16 36342012141 (35.6 min; shell 3,239 cells / 51,066 µm², setup +12.04 ns, hold +0.117 ns, DRC/LVS/antenna 0), `formal` 36342012194, `fabric` 36342012182, `test` 36342480467, `lint` 36342480574, `unit` 36342480768 (after moving it to Python 3.12), `docs` 36342480572.
**Also (uncommitted at session end, local):** design-set synthesis on the real flow (`python -m compile.fit`, `capacity.md`: UART 129, SPI 96, I2C ctrl 154, I2C target 208 LCs vs G0's 96); `N_IO` tile hardened (0 DRC); G0 fabric stitched (`arch/warp_g0`, 1016.64 × 669.06 µm, D-024 proposed); `spikes/fabric_tiny/run.sh` takes `FABRIC=<name>`.
**Not yet:** host data path into the fabric (FIFOs exist, the current fabric has no channel BELs), G0/G1 fabric, 6x4 hardening, timing model documentation, protocols on G0, `gl_test` evidence from CI.
**Later the same session:** the compile flow's wrapper instantiates IO cells explicitly (needed for the host channel; D-022); the new bitstreams exposed zero-delay hangs in the gate-level fabric model, so `gl_test` now simulates the gate-level shell with the fabric RTL, plus hold-X during loads and settle after (D-023 revised); per-tile netlist-vs-RTL equivalence added to the plan. Local: gl_local 16/16, RTL 16/16, pytest 42, bitstreams reproducible.
**G0 into the chip (later the same session, local, uncommitted at the time of writing):** `arch/CURRENT` = warp_g0 (ARCH_VERSION 0x0002); new top level with all 19 pins and the host channel through the fabric (D-024); black box generated from the macro (`scripts/gen_macro_stub.py`); compile flow maps `h_*` by name; examples `idle` and `hostecho`; RTL suite 17/17 incl. `test_host_channel`; F1 re-proved. Placement took six local pre-flight rounds (new `scripts/preflight.sh`): global-routing overflow 9,290 → 23 via east-channel obstruction, per-column frame decode (`wp_frame_select`), placement density 75 %, routing derate 0.15 (D-025); detailed routing 0 violations, power stripes full height. BUGS #14 (compile flow merged carry chains).
**Next:** push G0 and get the CI hardening + precheck + gl_test green; then G1 primitives and the protocols on G0/G1.
**Earlier next:** G0 into the chip: top-level pin and host-channel wiring (D-024), macro placement in `src/config.json` (D-019 rules), local routing pre-flight, then one CI hardening.

---

## 2026-09-27 (session 6: fabric through TT's flow; phase 1 complete)
**Done:**
- Three CI iterations on the chip-level integration, each failure logged: routing stuck because the fabric's pin faces pointed at the die edges (BUGS #9, run cancelled after ~4.8 h); `"//"` keys inside MACROS (BUGS #10); precheck pin check failed on pdngen's short channel stripes beside the fabric (BUGS #11). Adopted the R3 SRAM spike's macro settings (D-019 rev 2: routing-iteration cap, Magic/LVS handling, port-only black box). Added a local pre-flight: TT's merged config through LibreLane (Nix) up to detailed routing + a full-height power-stripe check (~3 min).
- **CI run 36327510268 (dea2150): `gds` 32.5 min, precheck 9/9, `gl_test` pass**; DRC/LVS/antenna 0, timing met at 50 MHz, IR drop 0.38 mV. Recorded in PHYSICAL_DESIGN_AND_CI, `fabric_tiny.md`, CLAIMS (C1–C3), risk register.
- D-020: template `fpga` workflow not applicable with a hard macro.
**Boxes ticked:** tiny fabric hardened with precheck (task + exit), all CI green on `efpga`, `docs/summaries/PHASE1.md` (final). **Phase 1 complete.**
**Next step:** phase 2 (`docs/design/phases/PHASE2_BASELINE_FABRIC.md`), starting with the shell (SPI host interface + checked loader + run control, ARCHITECTURE §2–4) and the formal properties F1/F2 for it.

## 2026-09-26 (session 5: tiny fabric)
**Done:**
- Magic hang root cause found (BUGS #2): the CMOS5L Magic tech file needs Magic >= 8.3.657; the LibreLane 3.0.0 Nix environment has 8.3.623. Workaround everywhere: skip Magic; KLayout writes the GDS and runs the DRC, OpenROAD writes the LEF (`write_abstract_lef`), unused VIA definitions stripped (the FABulous fabric flow misreads them as the tile size).
- All 9 tile types hardened on CMOS5L (0 routing DRC, 0 antenna each); **16-LUT fabric `warp_tiny` stitched: 357 × 484 µm, KLayout DRC 0**, bitstream spec generated (`docs/reports/fabric_tiny.md`).
- Line endings: my Windows-side Python edits had written CRLF into 14 committed files; all converted back to LF (content unchanged, checked with `git diff --ignore-cr-at-eol`). Edits now go through WSL or the Edit tool.
- The first background tile run was stopped by Claude Code for low memory on the Windows side (not a job failure).
**Boxes ticked:** none yet (the tiny-fabric box needs the chip-level integration + precheck).
**Later the same session:**
- D-017: tile power stripes on a global 109.92 µm grid (2.1 µm wide, per-tile-type offsets) so TT's chip stripes can land on the fabric's power columns (lesson from `main`'s R3 SRAM spike). First attempt put the east tiles' ground stripe outside the tile (arithmetic slip); fixed with grid phase 12.00. All 9 tiles and the fabric re-hardened: power pins are full-height columns exactly on the grid; KLayout DRC 0.
- Placement boundary (IHP 189/4) added to the fabric GDS; macro exported to `macro/warp_tiny/` (GDS, LEF, fabric + 9 tile netlists, fabric RTL, bitstream spec).
- Chip-level RTL (D-018): `tt_um_warp` = `warp_tiny` + `wp_fabric_cfg` (FABulous bitbang + ConfigFSM copied unmodified into `src/fabric_gen/`) + run control/parking. `src/lint.vlt` waives lint only for upstream files and the black box. New pin-level tests (parking, config session). `config.json` (D-019): MACROS, PDN_MACRO_CONNECTIONS, `pdn_cfg.tcl` from `main`'s R3 spike, stripe pitch 109.92 / offset 20.64.
- Local: `check_all` PASS, `gl_local` PASS (4/4 on a Yosys netlist), TT `--check-docs` and `--create-user-config` OK.
**Next step:** push; the CI `gds` run (hardening + precheck + gl_test) is the test of the phase 1 tiny-fabric box.
**While CI ran (run 36277723397):** wrote ARCHITECTURE v1 (pins, SPI host commands + status, loading with version/length/CRC, run states + parking, clock/reset, IO cells, G0/G1 resources, primitive sketches, variants, user Verilog rules; OPEN items marked), VERIFICATION v1 (V0–V7, F1–F4 with bounds, coverage goals), PHYSICAL_DESIGN_AND_CI v1 (three-level flow, known limits), risk register in OVERVIEW, in-progress `docs/summaries/PHASE1.md`. `gh` is installed and logged in (user); run logs/artifacts are fetched with it after runs complete. Boxes ticked: the three specs, the risk register, exit item "specs v1 written".

## 2026-09-25 (session 4: phase 1 starts)
**Done:**
- Phase 0 closed (D-012: organizer email waived by the user). CI green on 7405a2e.
- Held-out set sealed at **0171cf7**: WS2812, 1-Wire, SWD, CAN (D-013, `docs/design/HELDOUT.md`).
- Provisional user-design interface (D-014): pins + host byte channels + status; settings as bitstream parameters by default.
- UART: independent model `tools/refmodels/uart.py` (6 pytest incl. hypothesis) written first; then RTL `protocols/uart/` (tx, rx, top); 8 cocotb tests vs the model and sigrok, DIV 16/13/runtime, all pass; Verilator/Icarus lint clean. First profile: 171 LUTs fixed divisor, 262 runtime (budget ~96). BUGS #3 (harness). `unit` workflow added (D-015); `check_all` runs protocol tests.
**Boxes ticked:** phase 1: held-out chosen + sealed (0171cf7), `protocols/uart/`.
**Later:** `protocols/README.md` states that protocol designs are soft user logic, never silicon (user asked; D-002). SPI controller: model `tools/refmodels/spi.py` (7 pytest) then RTL `protocols/spi_ctrl/`; 24/24 cocotb runs (MODE 0–3, HALF 4/5/7) vs model + sigrok; lint clean; 85 LUTs / 42 FFs. BUGS #4 (model skipped a response; spec `HALF >= 4`, not 3). D-014 revised (`h_wlast`). `check_all` PASS.
**Boxes ticked:** `protocols/spi_ctrl/`.
I2C controller: model `tools/refmodels/i2c.py` (bus, target, decoder; 5 pytest incl. stretching) then RTL `protocols/i2c_ctrl/` (command byte stream); 18/18 cocotb runs (Q 4/2/7) vs model + sigrok; lint clean; 164 LUTs / 65 FFs at ~100 kHz. BUGS #5 (hold time, found in review).
**Boxes ticked:** `protocols/i2c_ctrl/`.
I2C target: reference controller model added to `tools/refmodels/i2c.py` (generator; 2 more pytest incl. stretching), then RTL `protocols/i2c_target/` (4-register map, host command access, dirty bits); 18/18 cocotb runs (Q 4/6/11) incl. sigrok; lint clean; 240 LUTs / 79 FFs. BUGS #6 (harness).
**Boxes ticked:** `protocols/i2c_target/`, reference models + RTL tests, sigrok check. All design-set protocol RTL is done.
Profiling: `tools/profiling/workload.py` (renamed from `profile`, BUGS #7) sweeps LUT3/4/6 ± carry and attributes every LUT to the function of the registers it feeds. UART counters resized to the divisor first (fairness; 171 → 144 LUTs). Result (`docs/reports/profiling.md`): of 648 LUT4s, counters 23 %, storage 21 % (mostly the I2C target's register map), shift 17 %, control 17 %, shared 15 %. Ranked: timer/counter, shift register, host channel in the shell, I/O cell sync/registered/open-drain, register file (1 user). Upper bound: UART/SPI/I2C controller fit ~96 LUTs after ranks 1–4; the I2C target does not without a register file.
**Boxes ticked:** profiling script, profiling report, exit item "profiling.md complete".
Area model `tools/areamodel/` (5 pytest) + primitive sketches (`spikes/primitive_area/`: timer ~2,751 µm², shift ~1,538 µm² incl. config bits). Capacity (`docs/reports/capacity.md`): 4 × 3 tiles fit next to a ~273 µm shell column: 96 LUT4, 88 with one primitive tile (2 timers + 2 shifts). UART/SPI/I2C controller fit; I2C target (~220) does not. **D-016: GO specialized eFPGA**; I2C target/showcase open (register file, smaller map, or showcase on the controller).
**Boxes ticked:** area model, capacity estimate, needs vs capacity, go/no-go decision, 2 exit items.
**Next step:** harden a tiny FABulous fabric (stitched tiles) through the flow with live config; then ARCHITECTURE/VERIFICATION/PHYSICAL v1 and the risk register.

## 2026-09-25 (session 3, continued)
**Done:** fetched the CI `GDS_logs` (user download): die 1289.28 × 710.64 µm, 0 DRC/LVS/antenna, timing met, **top level routes only to Metal4** (TopMetal1 is TT power); recorded in `PHYSICAL_DESIGN_AND_CI.md`. `fpga` run 36201219254 green. D-008 accepted (G1 fallback; goal still full specialization). D-011 (`unit` arrives with the first Python tool). `VERSIONS.md` complete. Phase 0 summary written (in progress).
Tile runs 2–3 (`docs/reports/tile_cmos5l.md`): with signals on Metal2–Metal4 the tile routes at the same size (6 iterations, 0 antenna); run 3 skips Magic (BUGS #2 workaround), KLayout GDS written, **KLayout DRC 0 violations (328 rules)**.
**Boxes ticked:** template workflows green (all four), resource usage, `lint`/`unit` workflows (D-011), `VERSIONS.md` complete, phase 0 summary.
**Open in phase 0:** organizer email (parked by the user); all CI green on `efpga` after the push.
**Next step:** push and confirm CI green. Then phase 1 (after the email closes phase 0, or on the user's call): seal the held-out set first.

## 2026-09-25 (session 3)
**Done:**
- Nix 2.35.2 installed by the user; FOSSi cache configured (`/etc/nix/nix.conf`). LibreLane 3.0.0 + FABulous plugin environment builds in 2.5 min (Nix store 6.9 GB). CMOS5L PDK at TT's revision in `~/.cache/warp/pdk-full`. CI LibreLane version recorded (3.1.0.dev3).
- `fabric` CI run 36196784852 green (FABulous demo in CI).
- **First FABulous tile on CMOS5L** (`spikes/tile_cmos5l`, patch D-010): `LUT4x8_ha` routes at the SG13G2 size/density: 40.7K µm² per 8 LUT4s (~5.1K µm² per LUT4), 97 % utilisation, 0 routing and antenna violations. `docs/reports/tile_cmos5l.md`. Capacity at 6x4: ~96 LUT4s with margin (the synthesis estimate was 60–90). D-008 updated; still stands (UART ~215 cells).
- Magic stream-out hung (BUGS #2); stopped by hand, so no GDS/DRC/STA yet.

**Boxes ticked:** none new (tile hardening is phase 1 evidence; `fab_demo` got its CI run ID).

**Next step:** KLayout stream-out + DRC + STA for the tile (BUGS #2). Close phase 0: organizer email (user), `fpga` workflow run (user clicks), `unit` workflow, phase 0 summary. D-008 decision (user).

## 2026-09-25 (session 2, part 3)
**Done:** `fabric` workflow (`.github/workflows/fabric.yaml`) runs `spikes/fab_demo/run.sh` in CI with the pinned tools (Ubuntu Python 3.12, OSS CAD Suite 2026-06-29, cached). PRISM prior-art notes (`docs/notes/prior_art.md`): Verilog → Yosys → bitstream on IHP already exists there, with a fixed datapath close to our hard-block candidates; our claims must rest on the parallel fabric model and the measured method.
**Boxes ticked:** PRISM notes.
**Next step:** push; record the first `fabric` run ID. Waiting on the user: Nix install (tile hardening), D-008, organizer email. The `main` gate is resolved: every "green on `main`" rule (CLAUDE.md, phase checklists) now says `efpga` (user decision, 2026-09-25).

## 2026-09-25 (session 2, continued)
**Done:**
- `gds` 36170807513 on a63877d fully green: hardening 35.1 min, precheck 12.3 min, `gl_test` pass. Recorded in `PHYSICAL_DESIGN_AND_CI.md`. Cell stats and the CI LibreLane version need the `GDS_logs` artifact (login required).
- Tiny FABulous study: `docs/notes/tiny_fabulous.md`. Tiles → fabric → top, three LibreLane runs, submitted via `custom_gds`. Phase 0 decision point answered: D-009 (yes; our plan: fabric macro integrated by the template `gds` job, as TRIPWIRE's R3 did with the SRAM).
- Early capacity estimate: `docs/reports/capacity_early.md`. ~4.5K µm² per LUT4 (stock LUT4AB tile, cmos5l synthesis), so a generic 6x4 fabric holds ~60–90 LUT4s; a scratch UART needs ~215. Proposed D-008 (the fallback becomes G0 + minimal hard primitives).

**Boxes ticked:** template design green on `test`/`gds`/precheck/`gl_test`; hardening time; Tiny FABulous read + written down; phase 0 decision point (D-009).

**Open in phase 0:** PRISM notes; `unit` workflow (waits for the first Python tool); the template `fpga` workflow has never run (manual); `VERSIONS.md` CI LibreLane version; "all CI green on `main`" (`main` is TRIPWIRE: the gate needs retargeting to `efpga` or a separate repo; the user decides); organizer email; phase 0 summary.

**Next step:** the user decides D-008. Then harden one LUT4AB tile on cmos5l with `FABulousTile` (needs OpenROAD/KLayout/Magic: Nix or the LibreLane container) to replace the synthesis estimate with a real one.

## 2026-09-25 (session 2)
**Done:**
- Fixed the `gds` docs check failure (empty title/author/description/pinout, missing `info.md` sections): filled `info.yaml` (WARP, 6x4, 50 MHz, `tt_um_warp`) and `docs/info.md`. Pinout is provisional (D-006).
- Renamed the placeholder top to `tt_um_warp` (`src/tt_um_warp.v`, `test/tb.v`, `test/Makefile`).
- Took the template `gl_test` UDP fix preemptively (BUGS #1).
- Added `scripts/setup_venv.sh`, `check_all.sh`, `gl_local.sh`, `requirements-dev.txt`, the `lint` workflow, and the `gds` paths filter + non-cancelling concurrency.
- Installed OSS CAD Suite 2026-09-25 to `~/oss-cad-suite`; FABulous-FPGA 2.2.0 into `.venv` (pinned). PATH order D-007; versions in `docs/VERSIONS.md`.
- Deleted the duplicate `docs/OVERVIEW.md` (the user did this).

**Boxes ticked (phase 0):** repo/info.yaml (local `--check-docs` pass; CI `docs` 36170807355 green on a63877d), sign-up form (done by Kanishk), docs skeleton, setup_venv, OSS CAD Suite + PATH (D-007), check_all (PASS), gl_local (PASS).

**Later in the session:**
- The user installed `python3-tk` and pushed (a63877d): `test` 36170807382, `lint` 36170807369, `docs` 36170807355 all green; `gds` 36170807513 still running at session end.
- FABulous demo: OSS CAD Suite 2026-09-25 breaks `synth_fabulous`; switched to 2026-06-29, the release FABulous 2.2 pins. `check_all` and `gl_local` re-passed on it.
- `spikes/fab_demo/run.sh`: stock fabric, two bitstreams (stock counter; our `lfsr_down`), each matches its source for 100 cycles, and B mismatches A's source. Report `docs/reports/fab_demo.md`. Ticked: reference fabric, reference design, second design, FABulous pin, and the exit item "two different bitstreams".
- Found: FABulous's wrapper generator only wires its own demo design (see the report); our compile flow needs its own.

**Next step:** check `gds` 36170807513 (precheck, `gl_test`, hardening time, LibreLane version). Then the Tiny FABulous study (how the fabric went through the TT flow), which answers the phase 0 decision point, and the LUT4AB area / config-bit measurement on cmos5l for the early capacity estimate. The organizer email is still open (the user will send it; low priority). `unit` workflow waits for the first Python tool with tests.

## 2026-09-25
**Done:** Project plan, CLAUDE.md and phase docs created (drafted in a Claude chat, not yet checked against a working repo).
**Boxes ticked:** none.
**Next step:** Phase 0, first task: create the repo from the CMOS5L template.
