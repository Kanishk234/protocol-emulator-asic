# Phase 5 summary: evidence and documentation

**Status:** in progress (updated 2026-10-12). Clean README reproduction now
passes on a fresh hosted runner37690896748: rebuilt bitstreams, loaded30/30
and cosim1/1 with strict XML/tool/README/source provenance. The clean-machine
checklist item is complete; numerical evidence audit and all-required-CI gates
remain open. This is a separate reproducibility result from checkpoint experiments.

Latest baseline additions now have actual loaded evidence: primitive-helper
38167521573 and autonomous UART fault/event demo38168609080 pass real SPI-loaded
chip-port tests on unchanged G1. The latter uses57/88LC and both timers/shifters;
Actual UART TX traffic under faults and clean-frame recovery now pass38273574240; narrower counter still uses57LC, so default4 remains. Portable C checked
loading/recovery and authenticated pin-mapping operating summaries are implemented;
cloud pytest38168413502 passes532checks. None establishes board throughput.

Full-duplex UART fault/recovery now passes38279446388 with concurrent RX and
event counting for both counter widths. Portable compiled-C loaded integration
38293580979 passes checked loading/recovery and31-byte duplex through simulated
SPI. All retain the existing D-023 RTL scope; no board or native timing claim.
Read-only hold allocation identifies590 delay cells and150 direct feedback paths
in compact producer38167697696. D089 queries every delay path in the cloud before
any repair changes; the best fanout-clean routing control still has133overflow.

Measured smaller-delay producer38316322592 now passes native placement and
3-corner estimated shell guards, saving455.4144µm² standard-cell footprint
while retaining worsthold0.112282ns and unchanged chip outline/clock policy.
Paired38316844576 worsens133→145overflow; reject smaller-delay candidate for
routing. Preserve133 control and test congestion-driven redistribution with
all original masters/repairs retained; no closure claim.

Earlier-stage placement38319615838 rebuilds CTS/repairs and restores the
retained hold guard after post-CTS redistribution failed it. Known fanout
repair38320631258 now passes native placement/connection/interface checks
and all3 original-corner estimated shell electrical/timing gates, retaining
fast hold0.100232ns. Routing comparison38321208948 rejects reflow:6544versus133;
D094 now evaluates native routing feedback in placement at unchanged policy;
no routing or complete chip-timing pass is claimed. The progress ledger
separates setup failures, rejected changes and actual qualified results.

Combined shell placement38168159774 improves146→133native overflow and111→91
markers, still fails routing. Buffer producer38172225275 passes native legality
and six preliminary electrical/timing guards; identical-policy routing is now
queued. Exact shared-marker connectivity identifies broader congestion than reset
ties alone; it does not causally assign overflow to individual nets.

Official Tiny Tapeout precheck passes all nine checks37960021923 on the
stronger-driver experimental layout. The fanout-free fixed-original placement
passes six estimated STA screens38101405271 but fails native routing146overflow.
Five-cell spacing leaves146 unchanged38113003427; moving one actual reset-net
endpoint lowers146→13638163542037. Both routes still fail, and the left-shell
band remains congested. This is measured progress with a specific next lead:
many constant reset drivers are far from their single loads, but nearby rows
are dense, so repair needs actual legal whitespace rather than blind shifts.

The eight-delay C2 candidate has zero native physical gates38114298036 and
passes genuine SPI-loaded UART/USER_RESET38163199372. Fresh extracted timing
38164099529 clears all examined internal setup/hold paths at two programmed
positions/three corners, worst hold+0.042992ns under unchanged margins.
Stationary configuration, incomplete annotation/I/O/loading/intertile/other
tiles/programs remain limits; no full-chip timing acceptance. RUN configuration
property38102131236 passes only its84-cycle assumptions/bound. See the dated
physical/extracted reports for precise evidence. The complete compact
successor remains unqualified; no phase boxes or hardware-freeze changes.

Older investigation paragraphs below describe intermediate checkpoints and
their limits at the time; the current official-precheck result is the nine-check
pass above. No checklist or hardware-freeze change follows from these trials.

The shell fanout remedy37956470190 now passes all three explicit estimated
corner measurements: five remaining violations become zero with ten identity
buffers. Routing and extracted timing still need confirmation. The actual
hardened C2 reaches zero route/antenna/Magic/KLayout/LVS in37814078650 but
fails its virtual-clock setup and has62 fanout violations. Its first loaded retest37956821834 stops on missing debug aliases; after
correcting logging,37958116481 passes actual SPI-loaded configuration, UART,
STOP and reset in both normal and USER_RESET cases. Other regenerated tiles
and configured timing still require qualification. Official precheck37814339758 passes eight checks and rejects two
internal supply access entries. An invariant-checked abstract correction is
prepared. None of these results qualifies the compact design or changes G1.

The compact stronger-driver trial37708459393 passes same-layout native
routing, antenna, full Magic/KLayout and shell LVS. Fresh shell setup/hold,
slew and capacitance pass at all supplied corners; fanout33 remains.
Native37709917442 passes the control after BUG47's configuration-audit fix,
then fails when original C2 is substituted at either synthesis or final
physical output. The failure already exists before physical routing.
Matched-tile preflight37811985092 now passes exact original die/all306 signal
ports for the passing C2. Fanout37811985079 clears27 clock violations with
cluster8, leaving five configuration nets in estimated typical-corner STA;
extra39 cells/+1056um2 area are measured costs. Native remap37811985147
passes storage audit but fails binary SAT; an identical-original proof control
is queued. Official precheck37811985173 finds orphan-top/LEF-format packaging
issues; a geometry-preserving export correction is queued. Actual matched
routing, configured timing and official checks remain open. Frozen G1 remains the fallback. See
[current physical/native evidence](../reports/compact_driver_native_20261008.md) and
[fanout/native plan](../reports/compact_fanout_native_next_20261007.md).

Compact37516794406 now reaches zero native router/antenna violations, but later
physical checks fail. All248 KLayout markers associate with inserted decaps;
the first exclusion attempt left the separate decap selector active. Corrected
37648945387 verifies zero decaps, then reports KLayout0/LVS12/Magic6350.
Magic boxes all overlap plain fillers, and the pinned KLayout pSD deck lacks
that rule. Bounded routing cleanup37652533986 and isolated library screening
investigate the remaining errors. Same-old-wire driver screen37651173629
reduces nine slew failures to zero; fresh physical/configured timing remains open.
Regenerated native LUT netlists pass real SPI-loaded UART and USER_RESET in
37553717299; matched original-LUT resynthesis37553979644 also passes, so the
new primitive alone is not established as the fix. Copied physical views do
not qualify either regenerated mapping. G1 stays frozen. See the
[closure plan](../reports/compact_acceptance_and_competitors.md).

Host capture decoding now handles wrap, quantization and observed overflow
explicitly; checked channel reads distinguish valid zero from empty. Loader
validation rejects negative chunk sizes and truncating fields. These work on
the fallback, with31 local host tests passing and hosted unit37651173601 green.

An independent divide-by-eight capture image now fits frozen G1 at86/88LCs
and passes real SPI-loaded RTL/source-queue checks in37659595436. It doubles
the counter period at the cost of one LC and coarser timestamps. Regenerated
native mappings pass28 TX/28 RX plus reset coverage in37659112021/37659171115;
their physical views remain unqualified. Tiny mirrored filler-ground fixtures
reproduce Magic's rule across all four filler widths, so a width-only swap
is unsupported. Compact physical/configured timing acceptance remains open.

The scratch filler remedy now clears full-chip Magic in37669173193:0 errors,
with all other layers identical. Full GDS-based KLayout/shell LVS follow-up
is prepared; known native shorts and configured timing remain open. Their
geometry now identifies actual pin escapes crossing ground/neighbor pins,
not just net-name associations. Independent loaded UART phase/read-delay
stress37671919707 verifies48 bytes over3 seeds with replay traces. No freeze
or phase gate changed.

## Goal
Make WARP's design choice, results, limits and use understandable to a judge, and make the simulation results reproducible from a clean source tree.

## What we did
- Filled the Phase 4 CI run IDs into the claims and evidence report; closed Phase 4 after its `gds`, precheck, `gl_test`, `fabric`, `unit`, `lint`, `test` and `docs` runs passed.
- Wrote the user guide, evidence report and prior-art comparison, and updated the README and Tiny Tapeout datasheet for the frozen G1 chip.
- Added an independent shell transaction model and a pyuvm environment. Local seed 1 compared 2,288 SPI transactions, 2,851 response bytes, 228 configuration words and 137 design-side bytes with no mismatches; its coverage closure reached 79/79 bins. Added the depth-2 and depth-4 F3 FIFO proof, which passes locally with `abc pdr`.
- Reproduced the README from a clean export of commit 14e7063 with the Phase 5 source files under test copied in. The fresh venv run passed all 30 fabric RTL chip tests, the UART co-simulation, a deterministic rebuild of all 11 bitstreams and the candidate `check_all.sh` including pyuvm. The run exposed a non-executable fetch command, a sandbox-only sigrok initialization failure, and a stale simulator build reused when switching from the idle fabric to the fabric RTL (BUGS #20). The README now invokes the fetch command with `bash`; the Makefile separates those simulator builds.

## What we found
- The pinned FABulous release requires Python 3.12 or newer; the README and agent guidance now say so.
- All Phase 4 tests reached green CI, but the new F3 and pyuvm checks still need CI evidence after the current changes are committed and pushed.
- The evidence report still needs a final pass over local-only measurements and their reproducible source references before its checklist item can be ticked.

## October 5 milestone

The unchanged fallback can now run UART and an independent event monitor
together, and a second bitstream adds externally timed corruption of selected
TX bits. The latter uses38/88 logic cells. Real SPI-loaded RTL and synthesized
shell tests pass normal RX/errors, injected corruption, recovery, monitoring,
reset and STOP parking. These remain local RTL-fabric tests without new CI,
SDF or silicon evidence; exact reports are `docs/reports/g1_uart_monitor.md`
and `docs/reports/g1_uart_fault_monitor.md`.

Compiler seed, control-mapping and FSM screens retain default settings;
no overall improvement is established. Strict port checking and structured
failure diagnostics make mistakes easier to find, including invalidating
stale success reports. Compiler/board unit checks pass315tests in local run
`compiler_host_unit_final_20261005`. Scratch compact hardware remains a separate
unpromoted experiment; its routing failures do not block these G1 improvements.

Compiler reports now bind listed sources/models to the emitted image with
fingerprints, and an audit checks those files plus image CRC/architecture/length.
Actual tools reject an owned source changed during compilation. This improves
evidence traceability without claiming hermetic reproduction or chip timing.
The historical G1 CI archive was searched for missing original tile parasitics;
it contains chip-level extraction only, so that reproduction gap remains open.
Details: `docs/reports/compiler_provenance.md` and `docs/reports/reproduction.md`.

G1 also runs UART alongside a two-entry soft timestamp queue. Its83-cell
version records one-clock ticks with64-clock wrap; an85-cell option gives
four-clock ticks with256-clock wrap. Real loaded RTL and synthesized-shell
tests cover concurrent TX/capture, quantization/wrap, overflow/order,
backpressure, RX, reset and STOP. These local results preserve the same
RTL-fabric/no-SDF limits and do not replace the open clean-machine/CI gates.
Evidence: `docs/reports/g1_uart_capture.md`.

## What's left
October10: official precheck37960021923 passes all nine checks for the
stronger-driver layout. Exact final C2 loaded UART passes37958116481, but other
tiles still need matching physical views. Fixed-original buffers38101405271
clear estimated electrical limits without moving original cells; fresh GRT
38101639866 still fails146 overflow. Conditional configured timing38111705892
finds positive examined setup and small fast hold failures, with loading/I/O/
intertile timing outside its scope. Short RUN-mode proof38102131236 passes with
explicit bounds/assumptions. Broad and localized padding probes remain rejected
before routing; no successor is promoted. Independent seed38101717810 fits all
nine planned G1 builds. New organizer guidance and board reload/AI disclosure
are documented; broad protocol flexibility remains the user priority.

October7: the compact scratch checkpoint now passes native routing and full
Magic/KLayout/shell LVS on one recovered layout (37669731197/37674839060).
Shell setup/hold pass, but electrical limits and configured-fabric function/
timing still prevent promotion. Frozen G1 remains the fallback. New48-case
loaded UART phase/read-delay stress passes37671919707. See
docs/reports/compact_clean_layout_20261007.md for the exact remaining gates.

- Clean README reproduction is complete (37690896748); missing historic routed-tile timing artifacts remain a separate gap.
- Finish the numerical-source audit in `docs/EVIDENCE.md` and run CI for the new verification and documentation changes.
- Tick the remaining Phase 5 exit items only after that evidence exists.

## One-line takeaway
The frozen chip's Phase 4 claims now have green CI evidence; Phase 5 is turning the local verification and documentation into a reproducible, reviewable submission package.

October13 update: native routing-feedback placement38339209412 and fixed-instance fanout repair38452773248 complete. All three estimated shell timing/electrical corners pass after repair; original3670 cells stay fixed. Direct routing comparison to133 control is next. This does not establish routing closure or complete matched extracted timing; phase5 remains open.
