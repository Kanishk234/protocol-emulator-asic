# Hosted experiments — October 6, 2026

## Verified software result

[Compact experiments37512249763](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37512249763)
at f671c1b: **g1_demos job passes**. Four freshly compiled and hash-audited
G1 images are loaded through real SPI and tested on shell/fabric RTL:

| Case | Hosted test seconds | XML |
|---|---:|---|
| UART monitor |21.8674|monitor_rtl_results.xml|
| UART fault monitor |19.9550|fault_rtl_results.xml|
| Two-entry capture |24.7824|capture_rtl_results.xml|
| Prescaled capture |24.9997|prescaled_rtl_results.xml|

Downloaded17,476-byte artifact `g1-demos-37512249763` to ignored
`build/cloud_evidence_37512249763_g1/`. Independently parsed all four XMLs:
exactly one case each, no failures/errors/skips. Compile reports/logs retained
in that artifact. This proves fresh hosted compile/audit and loaded RTL behavior;
it is not native gates, SDF, physical timing or silicon evidence.

First attempt37511778394 passed monitor in22.72s, then omitted the intermediate
monitor module from fault synthesis. Fix c76de70 adds the documented dependency;
the four-case hosted pass verifies it (BUG31).

## Missing checkpoint is not a design result

Both attempts' route/native jobs fail at release-asset download, **before EDA**.
No new compact routing marker count, antenna result, native functionality or
timing result is produced. Public checkpoint publication was rejected by
automatic approval review because public egress/licensing scope was not
established; specific user approval was requested and is pending. The archive
and explicit122-file inventory are complete and hash-verified. It includes
generated RTL/netlists, macro GDS, OpenDB design geometry, the UART image,
native marker report and supporting design inputs. Text/filename scanning finds
no credential/key/token patterns; that is not a blanket licensing assertion.

Follow-up harness writes `blocked_before_eda` metadata and an explicit setup
error when the asset is absent. It continues to fail rather than present an
untested design as accepted. After publication, rerun failed jobs on the
corrected experiment; no laptop EDA is needed.

## Other CI

At a284f4c, lint37511778680, docs37511778312, idle-chip test37511778469 and
unit37511778471 pass. Fabric37511778167 and G1 gds37511778153 are still running
when this report is written. These do not validate the compact successor.
No phase checklist is closed. See
[compact acceptance plan](compact_acceptance_and_competitors.md).

## Additional failed-workflow review

Read recent failures across both branches after the user's status report.
On main (TRIPWIRE), critical-branch37380322860 fails in its custom OpenROAD
wrapper because awk is absent from its command path. Routed-GL37375683211
fails setup with KeyError:PL_OPTIMIZE_MIRRORING. Unit37375675116's RTL job has
a cancellation annotation, while its pytest and Verilator jobs pass. Read the
plain job logs and annotations; no main files or runs were modified. These are
not WARP compact closure results and WARP uses no TRIPWIRE custom wrapper.

At WARP4146abd, test37512885377, lint37512885326, docs37512885423 and
unit37512885345 all pass. Compact experiments37512885358 is in progress at
this review; no asset approval or new routing/native result yet. The original
G1 fabric and gds runs remain separately in progress. Historical red badges
remain historical; no checks were waived or hidden.

## Checkpoint publication and actual execution

User explicitly approves public checkpoint publication after explanation.
[Experimental asset](https://github.com/Kanishk234/protocol-emulator-asic/releases/tag/compact-checkpoint-20261006-iter8)
is published,5676972bytes, unchanged SHA2566e2bac339e810a09dc9084393cadc3da5cdfb596077c05410c3b30b5e15ecb4d.
Attempt2 of37512885358 restarts only failed jobs, verifies materialization and
fetches pinned PDK. Publication/approval blocker is resolved.

Native RTL control passes; actual tighter mapped fabric fails15.39s with X
at UART output. All8707 configuration bits match and26944 CRC processing
cycles have stable input. This reproduces a real native test failure, not
loader corruption or proof of a hardware fault (BUG33). No SDF/config/user-state
force. Route reaches Docker image launch but fails before OpenROAD because
no-TTY is placed after eager dockerized option (BUG32). Corrected ordering,
visible bounded progress and read-only native cone/reset diagnostics are added;
new cloud verification pending. Existing G1 fabric37511778167 passes; G1
physical37511778153 remains running at this entry. No compact pass claimed.

## Corrected setup and unresolved native behavior

[Run37516794406](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37516794406)
at1784a49 passes directory validation, with routing still active when checked.
No new final routing count is available. Actual Liberty-based cone extraction
passes; tighter RTL control passes; native UART fails18.81s and the separately
labeled real USER_RESET probe fails19.12s. All8707 configuration bits remain
known and image-matching. Artifact `compact-native-37516794406` retains logs,
actual tile connectivity and strict nonzero native result.

The initial tile cone includes inactive mux branches and stops at tile inputs.
Neither is evidence of a whole-chip undriven net. Follow-up diagnostics trace
known selected mux data and actual UART output at Tile_X6Y2_E_IO4_wide.B_IN_top.
The independent `compact native diagnostic` workflow performs this investigation
without starting another route. It retains ordinary native failure even if a
reset probe succeeds; no state/configuration force or PDK model change.

All four G1 demo tests pass again in37516794406. At1784a49, lint37516794249,
docs37516794365, test37516794224 and unit37516794383 pass. Original G1
gds/precheck/viewer37511778153 pass; gl_test remains active at this check.
These results do not close compact/native/configured-fabric timing gates.

[Independent probe37519060510](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37519060510)
at21a2466 reaches actual tests: RTL passes; native24.76s and reset probe fail.
UART output is unknown before RUN via selected E2END[7], known at after-RUN
and after-USER_RESET snapshots, and subsequently unknown at4423540ns in the
baseline recording. The after-RUN snapshot is4419480ns,4060ns earlier.
This establishes an observation window, not the cause. Next probe records
runtime/cones at first UART X and after the same edge's delta cycles, retaining
the original test failure. Heavy computation remains hosted; active routing
inputs and frozen G1 remain unchanged.

## Failure-time evidence and baseline physical completion

[Probe37519661148](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37519661148)
at7a7148b completes RTL control and both failing native paths. UART X at4423540ns
persists after delta cycles; this observed failure is not resolved by sampling
after settling. Selected output cone reaches Tile_X6Y2.E2END[7]. Follow-up
traces exact macro connectivity across tiles, stops at clocked state and keeps
compressed actual connectivity in the artifact. No remapping or model changes.

[G1 physical37511778153](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37511778153)
now completes success including gds, precheck, gl_test and viewer. D-023's
mapped-shell/RTL-fabric limit still applies. At7a7148b, all regular checks pass:
lint37519661090/docs37519661032/test37519661002/unit37519661006.
Compact37516794406 routing remains active at this check. No compact native,
final geometry, configured-fabric timing or promotion pass is claimed.

Research follow-up: [FABulous synthesis guidance](https://github.com/FPGA-Research/FABulous/blob/main/docs/source/user_guide/using_doc/synthesis/yosys.md)
and [Yosys FABulous pass](https://yosyshq.readthedocs.io/projects/yosys/en/v0.69/cmd/index_techlibs_fabulous.html)
describe technology-specific mapping. They do not establish our X failure's
cause or justify changing pinned models. Trace actual active sources first.

## Independent capture boundary improvement

[Queue37520971978](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37520971978)
at86a1af7 passes the new full simultaneous pop/event and empty ready/event
checks at STAMP_SHIFT0/2 with six stored timestamp bits. Independently audited
both XMLs: one case each, no failure/error/skip. This exercises user-design
top ports in source RTL; it supplements, rather than replaces, existing real
SPI-loaded behavior checks. No queue implementation or frozen hardware change.

Cross-tile probe37520760969 reaches actual native failure and traces UART
through columns6→5→4→3→2. Unknown branches masked by controlling gate inputs
consume the trace cap; follow-up uses conservative Boolean sensitivity for
supported basic/AOI/OAI gates. No native pass or root-cause fix yet.
