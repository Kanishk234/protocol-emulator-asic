# Pending-event source: stock routing and extraction result

Run: https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43629225955
Source screen: 43390348317, commit 258186504e4b9f73d2711067e456494def705d2b.

Stock detailed routing succeeds, ending at iteration 21 with zero route DRC errors. Fresh extracted antenna checks report zero nets/pins; slew, capacitance and fanout violations are zero at every corner. Critical disconnected pins are zero (one noncritical disconnected pin remains reported). These checks do not constitute official GDS/precheck signoff.

| Corner | Aggregate setup WS (ns) | Hold WS (ns) |
|---|---:|---:|
| Fast | 0 (clamped) | 0.301340 |
| Typical | 0 (clamped) | 0.510919 |
| Slow | -0.783631 | 0.880261 |

Constraint qualification: these hold values use the legacy explicit signoff SDC with0.10ns hold uncertainty. The unchanged stock project uses native0.25ns; fresh stock-constrained extraction is still required. Setup uncertainty is unchanged.

The strict diagnostic fails. Fast/typical clamped zero does not establish positive functional reserve. Slow has three real setup violations, TNS -1.600791 ns. No gate or constraint was relaxed.

## Measured failure cone

All three violating paths start at `_47648_/Q`, U0 configuration word 0 bit 7. Endpoints:
- `_48951_/D`: fabric C3 last_seq, -0.783631 ns.
- `_48869_/D`: fabric C0 last_seq, -0.515177 ns.
- `_48434_/D`: U2 RX rt[23], -0.301982 ns.

Worst path traverses U0 pad selection, `a_in`, event logic and fabric logic. Data arrival is 22.007679 ns. Three explicit hold-cell arcs (hold10304, hold8242, hold8243) contribute 0.812312 + 0.627948 + 0.599110 = 2.039370 ns. Removing them without fast-path analysis is unsafe. This differs from the pre-route worst path (U1 PIN_A[4] to U2 RX timer); pre-route +2.533495 ns reserve did not survive extraction.

## Next experiment

Prioritize shortening the A/S selector cone on this exact source. Existing parallel-priority idea chooses S and A pad values before applying priority, instead of choosing an index then doing a bounded pad lookup. Rechecked against this source locally: all 46 Yosys equivalence points pass; an inverted selected-pad mutant is rejected. C selection and sequential statements remain unchanged. Raw proof, receipt and review patch: `/tmp/tripwire-selector-refresh-43629225955/`. This is a prototype only: no mapped/full-chip or routed improvement claimed.

Next gates: compare whole-chip mapped path groups and area, run exact-source protocol regressions, then prepare one native screen if the candidate is competitive. Preserve the 20 ns clock, acceptance gates and official jobs. Do not repeat the antenna-exception route without appropriate scope; the prior approval covered one diagnostic only. Final extracted functional reserve, official GDS/precheck and final netlist protocol replay remain required before Phase 2 completion.
