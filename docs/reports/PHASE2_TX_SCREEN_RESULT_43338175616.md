# TX cursor screen result (2026-11-13)

[Run43338175616](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43338175616) completes native physical generation and both read-only timing audits, then fails the final screen solely on one antenna net/pin. Source is b477486f2d3ba5fbcb1a98bb5a87b5c93375d9b3; artifact14001142224. No detailed routing was launched.

| Native estimated corner | Setup WS (clamped) | Hold WS (ns) | Slew/cap/fanout violations |
|---|---:|---:|---:|
| Fast | 0 | 0.130753 | 0/0/0 |
| Typical | 0 | 0.326490 | 0/0/0 |
| Slow | 0 | 0.662409 | 0/0/0 |

Final global-route overflow is0. The unchanged signoff-SDC estimate also passes. These estimates do not establish positive functional setup reserve or extracted timing closure; ordinary max-path reports still lead with latch borrowing endpoints.

## Exact remaining antenna failure

The original selector-word violation is no longer reported. The new violation is net `_01949_`, flop `_48904_/D`, whose Q is `u_chip.u_fab.u_c2.pending_drop`. Its direct driver is NOR4 `_44864_`; placement Manhattan distance is139.08µm, below the200µm wire-repair bound. Placement distance is not routed length.

The final detailed antenna report shows Metal2 cumulative ratio113.64 and Metal3 cumulative ratio299.34 against required200.00. The summary table displays the partial Metal3 ratio185.70/200, which does not describe the failing cumulative rule. The final checker correctly counts one violation. Metal4 has required ratio19984.00; this later-layer protection does not establish Metal3 compliance.

Immediately after native antenna repair, the full-design antenna summary is clean. Late timing repair inserts23 hold buffers, legalizes/mirrors and reroutes; the final fresh audit then finds the pending-drop violation. This identifies the failing stage transition, not the exact physical mechanism or deletion of a diode. A separate read-only audit compares this target on exact before/after ODBs; no repaired checkpoint is being promoted.

## Next candidates and limits

The narrow selector-word staging bank is not selected for this changed offender. Its combined TX-plus-bank RTL replay has finished22/22 cases (362.01s), and its source/XML hashes are recorded separately. Keep it as a verified fallback for its original configuration-data problem.

A new local trial stores the pending-drop event with complemented internal polarity. It adds no state or architectural cycle, preserves public counter/clear/reset timing, and passes module equivalence at N=1/5/6/7/9/16 plus a wrong-polarity negative control. Local mapping retains the changed encoding; C2's final D driver is OR2 instead of the reference physical NOR4. Mapped area415168.4376→414910.6416µm², slow minimum5.848→5.944ns, SRAM5.848→6.588ns. These are matched no-wire estimates, not physical gains. Its full22-case replay passes22/22, zero failed/skipped (266.25s), with source/XML hashes recorded; no native screen is prepared or launched. Audit geometry first, then choose a source-based/native remedy with every acceptance gate retained.

The official GDS jobs, main hardware/config and signoff constraints remain unchanged. Phase2 remains open.

## Exact audit result and selected next screen

Read-only audit43389395358 succeeds on both hash-bound ODBs. At Metal3 the same pin's cumulative ratio changes247.10→299.34, and the required ratio changes19984.00→200.00. At Metal2 it changes60.89→113.64 with required200 throughout. In the final view, protection credit is present at Metal4 (required19984); do not infer diode deletion from the layer-credit shift.

Prepare the separate `gds-official-dev4-pending-polarity-screen` from the exact TX screen source, applying only the port encoding patch. Four source/gate tests pass, actionlint passes, and fresh source preparation plus8×4 preflight reproduces every tested Verilog/header and the unchanged config9074bd3491a40f63b66ce8f09e33c22f8b3e21601a76ffd749fd6add6b3dc9ac. Local replay remains22/22 passed. The new physical result is pending; no gate is relaxed and no DRT is authorized from the failed TX checkpoint.
