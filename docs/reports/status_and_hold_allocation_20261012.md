# Status and hold-repair allocation — 2026-10-12

## Confirmed results

[Portable C loaded integration run 38293580979](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38293580979) passed. Downloaded artifact XML contains exactly one test case, `test_portable_c_host_loaded`, with no failure, error or skip. The compiled C loader exercises the actual simulated SPI interface: stale-error recovery, checked loading without automatic RUN, 31-byte bidirectional ordered exchange, final-byte indication, USER_RESET and stopped-state rejection. The hostecho image uses 23/88 logic cells and no timer/shift primitives; image SHA256 is `14b61127da67dbb37d68e746f5720675a809b03ce315c4a6090bbcf1bcf1d8ed`. This is configured-fabric RTL simulation with the documented D-023 accommodations, not board, native extracted timing or silicon evidence. Compiler frequency estimates are not chip timing closure.

[CUGR diagnostic run 38292828402](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38292828402) completed, but neither underlying route passed the observer gate. Original/combined weighted grid overflow is respectively 1573.7818279117346 / 1893.8656954020262, with six/three negative usage observations retained unchanged. Required-net guide coverage is complete. These weighted values are not directly comparable to FastRoute integer overflow. Best accepted comparison control remains the combined placement with **133 nonzero FastRoute overflow**, not a passing route. Diagnostic workflow success means evidence collection succeeded.

## Structural bottleneck measured without changing hardware

Read-only `test_internal/audit_hold_repair.py` analyzes producer 38167697696 census and geometry. Among 3606 instances, 590 cells use `sg13cmos5l_dlygate4sd3_1`. Their summed bounding-box area is 9634.464 µm² out of 58378.32 µm² of CORE instance bounding-box area, or 16.50%. This excludes the macro and whitespace; it is not total chip utilization. There are 150 direct flip-flop Q → delay → mux → same flip-flop D feedback paths. These are graph memberships, not proof of redundant repair or the cause of overflow.

Census SHA256: `3d8a7d032a84720fa1b4e5a243cccadde5678630f0067d846f25352ba4905aa3`.
Geometry SHA256: `c2317b8ffbb2c2f008b85bb8a0ee910075b4db37a3df84a4776cfa9fb688652f`.

The next physical investigation is path-level timing and constraint coverage for this delay allocation. Do not remove repairs or relax uncertainty to force routing. Any alternative enable implementation must first demonstrate reset/enable equivalence and usable mapped cells, then compare unchanged constraints and total physical area. Frozen chip sources and template workflows remain untouched. Full same-build physical acceptance and complete native timing coverage remain open.

## Actual per-delay follow-up

[38315257114](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38315257114) completes590 constrained min and590 constrained max queries at each of3 original PVT corners, with no missing paths and unchanged shell timing/electrical guards. Result SHA256: `3866682f1cbb486f1bbd1f39e642406b89d765dcede5f3b26563217a22c3a0f8`. All150 direct feedback paths belong to configuration registers; their fast-corner hold slack spans0.176544–0.217264ns. The eight feedback paths present in the original fast endpoint report traverse delay cells contributing0.235120–0.236332ns; removing that contribution without considering other timing changes is unjustified.

D090 now tests a smaller delay master only on251 non-feedback cells whose measured fast hold slack is at least0.3ns. The150 feedback repairs remain untouched. This is an unqualified copied-layout producer until native legality and all electrical/timing guards pass. The candidate must also retain at least0.1ns worst hold slack before any routing comparison.

## Measured smaller-delay producer

[38316322592](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38316322592) passes native placement, exact connection/origin/unselected-box preservation and all3 original-corner shell electrical/setup/hold checks. All251 selected cells shrink inside their original boxes; actual summed standard-cell bounding-box saving is455.4144µm², not a chip-outline reduction. Worst estimated shell hold is0.112282ns (fast), retaining the0.1ns guard; setup slack remains positive at all3 corners. Source comparison clock and constraints stay unchanged.

Producer result SHA256: `dd19fa05fd4c46c71d74daa73f371edf2dac439e3bf11e61f3f029a49eebdb8e`. Candidate ODB: `d213774b48b5a3ef93f529228bbb5e9a7b95e54419bdd3bc6602552adfc2c948`. Candidate netlist: `1a2bc7db166798abb6c83a664e589bcf028110ab4267b922a11890a7da52d858`. This is placement and estimated shell timing evidence; routing, full physical signoff and complete native fabric timing remain open.

Prepared paired native routing against the actual best133 control, not the older146 placement. Both retain50 iterations, original capacities/layers/derates and compiler-independent physical inputs. The adapter validates downloaded hashes, selection/geometry, and measured3-corner producer gates; local read-only validation passes against both actual downloaded artifacts. A successful evidence-collection workflow is distinct from a zero-overflow candidate route.

## Actual routing comparison: reject smaller-delay candidate

[38316844576](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38316844576) completes both native cases: control133 overflow versus smaller-delay candidate145. Both native return codes are1 and neither route passes. Result SHA256: `c8b7a005656b0ada9e16af1580628811cd1ace170e923468c837e4fef1aa9c10`. The footprint saving does not improve congestion; reject this candidate for routing and retain the original133 control. Collector success is not routing success. D091 now tests congestion-driven placement with all original masters/repairs retained, native row/power-phase and unchanged timing guards before any route comparison.
