# SRAM electrical closure: targets and experiment order

This is a preparation report, not a timing or electrical pass. Native hold100 routing run37870374707 is still in progress at this audit. Keep the full 2-lane/4-unit design, 20ns clock, fully timed constraints and unchanged protocol latency.

## Measured failures

Native125 extraction37859526262 has slow setup−1.423654124ns and fast hold+0.094072364ns, with133 slow slew and6 slow capacitance violations. SRAM A_DOUT[0] reaches0.128690pF against0.064000pF. Stock electrical-repair screen37858535440 clears estimated capacitance violations, but SRAM A_REN still has0.984095ns slew against0.595200ns and A_ADDR[6] has0.667443ns against0.595200ns. That screen has no extracted-route result.

The actual native125 netlist drives macro A_REN from net_00076_, produced by NOR2B cell_29426_. A_WEN is driven separately through INV cell_29427_. Although the generic SRAM wrapper expresses REN as !we, synthesis has mapped this control cone differently. Inspect the mapped driver and its load before choosing a repair; changing the wrapper expression alone does not establish a physical improvement.

## Independent targets

Pinned-library follow-up confirms NOR2B_2 exists with the same `nor2b` footprint: area12.7008µm² versus9.072µm² for NOR2B_1, a3.6288µm² cell-area increment. This makes a one-driver strength probe concrete. Native125 net_00076_ also feeds hold11848 before the separate write-enable inverter, while A_REN connects directly. Therefore driver sizing can affect both read-enable arrival and the write-enable hold branch; all-corner hold must be rechecked. No sizing change has been applied or measured yet.

1. **Read-enable/address input slew:** buffer or remap the macro input driver, preserving the exact read/write enable truth table and clock-cycle behavior. First verify available cells in the pinned library; do not assume the weak NOR2B has a stronger equivalent. Measure the input pin slew after routing, not only driver output slew.
2. **SRAM output capacitance:** isolate the macro output from downstream fanout with physical buffering near the macro boundary. The macro cannot be upsized like a standard cell. Any inserted buffer needs new routing/parasitics; fixed-wire STA with invented nets is not evidence.
3. **Repair margins:** the pinned stock post-GRT repair Tcl accepts slew/cap margins and runs global routing before repair. A bounded margin experiment is possible without changing RTL, but repeated repair/rerouting can change setup and area. Use a separate clean build and record the complete recipe.

OpenROAD documents buffering/resizing for electrical repair and margins to compensate for estimated parasitics ([resizer documentation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/rsz/README.md)). Current upstream implementation must not be assumed to match the pinned competition image. The pinned LibreLane repair Tcl was inspected separately.

## Qualification and next decision

### Combined electrical changes and timing-prototype compatibility

Twelve further STA processes compare both strength changes together on (a) the unchanged native125 netlist and (b) the prior six-cell fixed-wire timing prototype. Each baseline matches its established six setup/hold metrics within1e-6ns. Both combinations retain their baseline global timing. On the six-cell prototype, setupWS remains0 all corners and holdfast+0.094072364ns/typ+0.196308970ns/slow+0.370721012ns. Slew counts fall133/34/3→113/13/2 (slow/typ/fast); cap6/fanout188 each remain. Added library area for two strength changes7.2576µm², or25.4016µm² including the six-cell prototype changes. Neither combined netlist is a new physical result.

Raw evidence: /tmp/tripwire-native-combined-electrical-37859526262/comparison.json and /tmp/tripwire-native-sixcell-electrical-37859526262/comparison.json. This confirms compatibility for subsequent physical testing, not official readiness.

### Functional fanout triage and strength probe

Of188 native125 slow fanout violations,164 have clock-buffer names and24 are other drivers. This naming classification is triage, not an exemption for clock nets. Driver28820 has fanout19 against8, slew4.107000ns against2.507400ns and cap0.326298pF against0.300000pF. Driver28807 also has fanout15 and slew3.729888ns against2.507400ns.

Six additional actual extracted STA processes test only driver28820 NOR2_1→NOR2_2, costing3.6288µm² library area. Baseline six timing metrics match CI within1e-6ns; global setup/hold stay unchanged. Slow slew violation count falls133→113 and typical34→14; fast stays3. Driver28820's own slow slew violation disappears, but its capacitance/fanout violations remain; all corners retain188 fanout and6 cap violations. Stronger cells alone cannot remove the attached load. Raw evidence: /tmp/tripwire-native-fanout-probe-37859526262/comparison.json. This is fixed-wire analysis, not a routed or official pass.

### Measured read-enable strength probe

Six local STA processes used the actual native125 extracted NL/SPEF and fully timed constraints. All six baseline setup/hold metrics match CI within1e-6ns. Replacing only NOR2B_1 instance29426 with NOR2B_2 preserves connectivity and adds3.6288µm² library area. Slow A_REN slew improves1.411568→0.722519ns but still violates0.595200ns; typical/fast A_REN violations disappear (baseline0.904454/0.581309ns against0.476000/0.380000ns). Global setup/hold remain unchanged at every corner: slow setup−1.423654079ns, fast hold+0.094072364ns.

Electrical counts baseline→probe: slow133→133 slew, typical34→33, fast3→2; fanout188 and capacitance6 unchanged each corner. A count alone hides the slow pin's substantial improvement. This is fixed-wire evidence, not a rerouted result; input capacitance and actual layout must be rechecked after physical repair. Raw evidence: /tmp/tripwire-native-ren-probe-37859526262/comparison.json and per-corner logs. Do not promote this partial fix as closure.

Follow-up report audit: scripts/ci/electrical_report.py reproduces native125 slow counts133 slew,188 fanout and6 capacitance from the actual checks report, matching its printed totals. Five focused tests pass; incomplete or duplicate sections are rejected. Fanout must also be inspected when assessing electrical closure; the earlier slew/cap summaries did not enumerate it.

The extraction helper now prepares electrical_summary.json from fresh corner checks reports;11 combined audit/extraction tests pass, including corner mismatch, missing evidence and printed-total disagreement. This local change does not alter the already-running hold100 workflow.

First inspect hold100 actual extracted setup/hold, per-corner slew/cap counts and offending nets. Reuse that measured baseline when choosing one electrical change per hardening. Require zero electrical violations, nonnegative setup at all corners, at least50ps fast hold, zero routing overflow, clean DRT, and acceptable area. Then run protocol GL on the exact final powered netlist and prepare official integration. No phase checklist is ticked by this report.

The existing official-preparation directory also needs its PNR constraints corrected: its old latch setup masking must not enter main. Adopt the native fully timed PNR/signoff constraints and review configuration changes outside the AGENTS.md whitelist before official integration. Unchanged main currently does not represent the experimental full design.
