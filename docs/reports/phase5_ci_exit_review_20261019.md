# Independent phase-five CI exit review, October 19

Current conclusion: the fresh GDS refresh resolves the transitive-helper gap; see the final section. The initial findings below are retained as review history.

Reviewed checkout `0165bef01b34e02420e79757c1cb0871f3a92402`.
**The all-CI exit gate remains open:** historical GDS physical inputs still
match, but its gate-shell tests consume a board helper that has changed.
The coordinator will refresh the existing unmodified GDS workflow instead of
claiming identical transitive test inputs. No phase checkbox is changed here.

## Applicable completed checks

Coordinator-verified GitHub statuses at the reviewed revision are SUCCESS for
lint `39144228213`, docs `39144228227`, test `39144228181`, unit `39144228173`
and autonomous-supervisor checks `39144228163`.

Fabric `39144029882` passes at `faecd01`. Independent Git comparison confirms
no changes from that revision to the reviewed HEAD in its workflow, scripts,
requirements, architecture/macro/RTL, test and protocol inputs, FABulous demo,
compiler/host/board/reference-model code, co-simulation code, or the actual
`tools/autonomy/check_xml.py` dependency used by the workflow. Later autonomy
repair-auditor and documentation changes do not invalidate this fabric result.

Formal `39143521760` passes at `a81eac9`. Independent comparison confirms
unchanged `formal/`, `src/`, `arch/prims/`, `scripts/formal.sh` and formal
workflow inputs. Downloaded `build/formal110` logs contain seven actual
`DONE (PASS, rc=0)` completions across the four matrix jobs: F1, F2 BMC/cover,
F3 depth-2/depth-4 and F4 timer/shift. These retain the named properties and
bounds in the formal report, not a broader chip-equivalence claim.

## Blocking transitive GDS test dependency

GDS/precheck/gate-shell run `37659595229` passed at
`927b225d72c53ba60a606de75c7e99359cc0202b`. The checked physical inputs
`src/`, `arch/`, `macro/`, `info.yaml`, `docs/info.md` and the GDS workflow are
unchanged. The direct `test/` tree is also unchanged. This preserves that
historical frozen-G1 physical result.

However, `test/test_bitstream.py::_board_modules()` inserts `tools/board` into
the Python path and imports `warp`; the board-loader/example cases execute it
under `gl_test`. `tools/board/warp.py` changed after the historical GDS run:
it adds load-argument validation and wraps `Warp.xfer()` in transport-error
cleanup. Therefore the full consumed gate-shell-test input set is **not**
identical. Changes on its successful path may be small, and current fabric
tests cover the updated helper with RTL shell/fabric, but those facts do not
turn the old GDS job into a current gate-shell test run.

Smallest conservative resolution: execute the existing GDS workflow at the
current source and inspect its GDS/precheck/gl_test results. No hardware or
template-job edit is required. A passing result would close this specific
applicability gap; it would not qualify compact routing or native configured
fabric timing. Do not tick the exit gate while that refresh is pending.

## Existing applicability rules, not new exemptions

The manual FPGA run `39143524179` reproduces the known missing `warp_g1`
iCE40 implementation. Accepted **D-020** already excludes that template
workflow from phase gates once WARP uses a hard macro. No new waiver is
introduced, and a placeholder FPGA success cannot support the G1 chip.

**D-095** states that no `efpga`-only nightly cron is active while default
`main` holds TRIPWIRE. Explicit bounded campaigns supply their named evidence;
do not describe those as an active nightly schedule. This review does not
invent a new scheduled-job success.

Experimental routing collection can pass while native routing fails, provided
the failure and rejection are retained accurately. It cannot substitute for
the core physical or gate-shell checks.

## Independent D-102 artifact audit

Actual controlled-repair run `39143364213`, attempt 1, is SUCCESS at
`a81eac9b3525ff149a683bc959069f25a62da0df` according to retained API identity
`build/repair110_identity.json`. Re-executing the portable read-only auditor
against `build/repair110_result/route_force_repair` verifies result SHA-256
`b9c50cf9f47ae7189a04b3982e2bb790d926ddfcb886d0525f1b4ae5b4691a74`.

| Case | Final observed overflow | Actual native failure | Real boundary overflow |
|---|---|---|---|
| Default identity | 121 | `GRT-0116` | 0 |
| Legacy forced pair | 132 | `GRT-0232` | 0 |
| Used-grid rebuild candidate | 139 | `GRT-0232` | 0 |

The audit rechecks geometry/connectivity census identity, all 69,064 interior
and 550 real preferred boundary reporting capacities, complete native route
inventory, hashes and source/run/attempt binding. The legacy observer retains
five whole-reporting-grid states: 125, 123, 139, 140, 132, with actual input
net counts 2, 53, 489, 637, 678. No recorded pass improves the protected 121
control. The candidate is rejected.

Only the default case has a final native congestion table. Both repair calls
throw before that table is printed; their 132/139 outcomes are independently
audited reporting-grid totals, not invented final-table results. All three
retain `native_repair_passed=false` and `physical_acceptance=false`.

This review runs Python/file/Git-object analysis only. It performs no EDA,
dispatch, commit, acceptance-rule change or checklist update.

## Resolved by current GDS refresh

The coordinator subsequently ran the existing unmodified workflow at the
reviewed revision. Independent GitHub API inspection confirms
[`39280550500`](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39280550500)
is completed SUCCESS at exact
`0165bef01b34e02420e79757c1cb0871f3a92402`; all four jobs (`gds`, `precheck`,
`gl_test`, `viewer`) are SUCCESS.

Independent strict parsing of `build/gds111_gate/results.xml` confirms **30
executed passes, zero failures, errors or skips**, including
`test_board_loader`, `test_board_examples_spi` and `test_board_examples_i2c`.
`build/gds111_precheck/results.md` records all nine named prechecks passing.
This directly resolves the changed board-helper dependency identified above.

**The all-applicable-CI phase-five gate can now close for `0165bef`**, together
with the applicable fabric and formal results reviewed above and the other
current core workflow successes. D-020's existing FPGA exclusion and D-095's
explicit scheduling scope remain unchanged. Subsequent changes still need
their own applicable checks; this conclusion is tied to the reviewed revision.
It does not make the rejected compact candidate acceptable, establish native
configured-fabric timing, or itself tick a phase checklist.
