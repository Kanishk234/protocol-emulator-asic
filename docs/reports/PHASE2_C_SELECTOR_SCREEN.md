# C-selector source experiment

The extracted full-design result from run **42069613808** fails slow setup at
**−2.66890162 ns**. Hold, electrical and antenna checks pass. The worst reported
path crosses live unit configuration, output-pad feedback, C-pin selection and
fabric consumption/drop logic. Improving only the final counter is too narrow.

The next source experiment removes the redundant index clamp on C and computes
`sel = !c_on || (c_pad == c_active)` directly. A/B inputs, registers, cycle
semantics, live configuration behavior and the architectural contract are
unchanged. Unattached C indices still produce `c_in=c_active` and `sel=1`.

## Local evidence

`spikes/phase2_stock_flow/pin_input_decode/c_select_candidate.json` binds the
reference, candidate and patch. The comparison scripts prove combinational
equivalence for arbitrary binary inputs, including all 32 C indices. The delay
register block is unchanged. Verilog-2005 compilation passes. Five full-chip RTL smoke tests pass on an
isolated full source preparation (SRAM, lane/fabric forwarding, pin-unit UART,
routines and UART loopback); this is not the full protocol suite. Source binding
and physical-profile regressions pass 58 tests; actionlint and embedded Python
syntax checks pass.

Pinned IHP Liberty mapping, BUF2 input driver, equal loads on C/selection outputs:

| Slow output load | Reference delay | Candidate delay | Reference area | Candidate area |
|---|---:|---:|---:|---:|
| 6 fF | 1577.58 ps | 1107.67 ps | 435.4182 µm² | 422.7174 µm² |
| 26.7 fF | 1768.30 ps | 1254.77 ps | 464.4486 µm² | 437.2326 µm² |
| 50 fF | 1833.40 ps | 1284.40 ps | 464.4486 µm² | 446.3046 µm² |

These are isolated longest-cone ABC estimates, with no extracted wiring. They
are not specific measurements of the failing pad-to-selection arc and cannot
be added to routed WNS. The current −2.669 ns deficit remains unresolved.
The comparison receipt also records alternative decode/banked forms and the
rejected pad-owner rewrite, whose small delay gain costs area.

## Full-design screen preparation

The separate diagnostic workflow `gds-stock-official-baseline-screen` has a new
manual profile, `rtl_shared_minbuf2_cselect`. It prepares the same full
2-lane/4-unit source and physical recipe as reference **41569397169**, then
applies only the bound C-selector patch. Source inventory checks reject any
other source change. The physical configuration hash is unchanged.

The stock Classic sequence, existing screening gates and three-corner checks
remain intact. An additional read-only estimated-routing audit uses the exact
unchanged `src/signoff.sdc`, checking setup/hold, 50 ps fast hold reserve and
zero electrical counts. This distinguishes constraint differences from later
extracted RC effects. Antenna and final-source overflow checks still come from
the existing qualification gate. No detailed routing starts in this workflow.

This profile is prepared locally, not published or physically measured. Main
hardware/config and the official `gds.yaml` jobs are unchanged. The diagnostic
recipe's extra physical settings and the earlier checkpoint ECO are not a
qualified clean official-flow implementation. A passing screen still requires
detailed routing, extraction, final netlist protocol replay and unchanged
official GDS/precheck qualification before Phase 2 can close.
