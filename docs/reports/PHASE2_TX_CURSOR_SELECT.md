# TX cursor subtract-before-select experiment

This is an isolated 8×4, two-lane/four-unit candidate, not main hardware or an official GDS result.

The configuration-mode control can select a cursor base before a signed subtraction, whose result controls token acceptance and timer updates. The prototype evaluates subtraction for the existing register base, zero and minus-one first, then selects the result. It adds no state, cycle, instruction or protocol-specific behavior. It is a single `trw_pin_tx.v` delta from native-drive run 43178099947.

## Local evidence

TX-module equivalence at FRAC=8 passes FULL=0/1 with 548/634 points; induction sequence cap is six. The arithmetic negative control (subtracting from minus-two instead of minus-one) is rejected. These are module checks, not full-chip formal verification. Reproduce against the prepared reference source:

```sh
source .venv/bin/activate
python scripts/ci/verify_tx_cursor_select.py --reference <prepared-reference-src> --output /tmp/tx-cursor-proof
```

Matched local synthesis maps the complete chip with the same library and NAND2_1/NOR3_1 exclusions in both variants. Ideal clock is 20 ns with 0.25 ns setup uncertainty and no routing parasitics. This does not reproduce native physical repair or official signoff.

| Measurement | Reference | Candidate |
|---|---:|---:|
| Standard-cell area (µm²) | 411236.0280 | 415168.4376 |
| Typical worst flop slack (ns) | 10.629 | 11.098 |
| Typical SRAM slack (ns) | 11.561 | 11.098 |
| Slow worst flop slack (ns) | 5.614 | 5.848 |
| Slow SRAM slack (ns) | 6.557 | 5.848 |
| Slow TX timer group slack, 100 endpoints (ns) | 5.901533 | 7.755704 |
| Slow fabric last-sequence group, 9 endpoints (ns) | 6.677540 | 6.844627 |
| Slow BITSYNC timer group, 25 endpoints (ns) | 6.544236 | 6.532560 |

Mapped area increases about 0.96%. The new global worst path launches from SRAM; the TX path improvement does not establish a routed improvement or eliminate the extracted BITSYNC/fabric setup deficit. Detailed local output stays in `/tmp/tripwire-tx-specsub`. Strict whole-chip Verilator lint fails on the existing C-pad comparison width warning in both reference and candidate; filtering WIDTHEXPAND locally leaves no other warning. This is not a clean strict-lint result. The open issue is recorded in BUGS.md and must be fixed/proved before source promotion; no lint suppression or second RTL change is included in this experiment.

## Physical comparison and gates

The separate `gds-official-dev4-tx-cursor-screen` workflow uses the reference's exact native-drive configuration: 20 ns, hold125, wire200, diode-only antenna repair, and the same three excluded weak cells. It changes only the TX source file. It keeps the native Classic commands, image, SDC audit, all-corner timing, electrical, fresh antenna and overflow checks. Its preparation requires a passing 22-case protocol replay receipt. The official `.github/workflows/gds.yaml` is unchanged.

The reference has one antenna violation and is not qualified for routing. The new RTL may change placement, buffering and antenna outcomes. A failed screen stops before detailed routing. A green screen still requires detailed routing, extraction, all-corner timing/electrical/antenna checks, gate-level replay, integration of the exact source/config, and the unchanged official GDS/precheck flow before Phase 2 can close.

Status: all 22 L3 RTL replay cases pass (zero failed/skipped, 395.48 seconds); source hashes and the XML digest are recorded in candidate.json. Final candidate preparation from a fresh HEAD archive passes, with all Verilog/header files matching the locally tested candidate, the reference configuration hash unchanged, and the 8×4 tile preflight passing. The initial local macro download was blocked by sandbox network access; rehearsal used the same verified cached macro files, whose pinned hashes passed the unchanged preparation checks. Ready for isolated native measurement; no physical result yet.
