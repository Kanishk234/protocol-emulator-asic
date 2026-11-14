# Pending-event screen and approved stock routing diagnostic (2026-11-14)

Screen43390348317 completes the native physical flow and timing/electrical audits, but fails one fresh antenna net/pin. The old pending-drop offender is gone. Final global overflow and electrical counts are zero; native estimated fast/typ/slow hold is0.107840/0.302408/0.644102ns, setup WS0/clamped. This is not extracted timing closure.

The remaining offender is `u_chip.g_lane[0].ot[12]` at `hold11230/A`, a dlygate4sd3 input with Metal2 ratio229.04 against200. The hold cell already exists in the pre-antenna DEF and is connected to ANTENNA_2 on that net; it was not newly inserted by the final pass. That later pass inserts148 other hold buffers and reroutes. Presence of a connected diode does not prove that each metal layer remains protected. No additional RTL encoding tweak is selected solely to move this one violation elsewhere.

## Native stage order and approval

The exact installed LibreLane3.1.0.dev4 wheel's `librelane/scripts/openroad/drt.tcl` includes antenna checking/repair and another detailed-route iteration after the first detailed route (lines111–137). The saved source resolves DRT_ANTENNA_REPAIR_ITERS=3 and DRT_ANTENNA_REPAIR_DIODE_ONLY=false. The script is unmodified.

The user explicitly approved one stock detailed-routing diagnostic on this source, with final timing/electrical/antenna/DRC gates unchanged and no Phase2 pass claim. This is a scoped exception to the earlier zero-antenna-before-routing prerequisite, not reclassification of the failed screen.

The separate manual workflow `gds-pending-stock-drt-diagnostic` requires explicit opt-in. A push can register it but cannot execute its jobs. The helper accepts only source43390348317/258186504e4b9f73d2711067e456494def705d2b, verified source/macro/config/engine provenance, and exactly the two existing antenna-count failure messages with zero overflow and all ordinary timing/electrical gates intact. It rechecks the source before routing. Missing approval, another source or any extra failure is rejected.

It executes the unchanged stock OpenROAD.DetailedRouting step, including native antenna repair, then a separate extraction job. Final strict setup/hold/electrical/antenna gates are copied unchanged from the existing route helper and tested for structural identity. Route DRC must be0. Diagnostic receipts always retain qualified=false and official_gds_signoff=false; final_gates_passed is recorded separately. No source change, cell swap, custom physical repair, timing exception or official-job edit is introduced.

## Read-only functional setup audit

A separate audit on the same checkpoint adds reports to flop and output endpoints using the existing functional_setup_frontier hook. Ordinary all-endpoint reports remain active. It compares repeated fresh measurements with the archived baseline and verifies physical-view hashes remain unchanged. The source's one antenna violation is recorded, not waived into qualification. It runs no routing or repair. This will expose actual setup reserve hidden by aggregate zero-slack latch-borrowing paths; it is still estimated routing, not extracted signoff.

Local checks: source provenance and the exact allowed failure set checked against the actual archive;52 focused tests pass, including wrong-source/approval/failure-set rejection and unchanged final gate logic. Both workflow files pass actionlint and every shell block parses. Native audit/route execution is pending publication. Main hardware, official jobs and signoff constraints remain unchanged; Phase2 remains open.
