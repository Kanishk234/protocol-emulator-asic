# Clean extracted 2/4 baseline

[Routing and extraction run 38784492656](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38784492656) **passed** on main `88850b1241a4d83609537602dc7d8c7857a9c3a8`. This is the complete frozen R4 2-lane, 4-pin-unit, U0-full/SRAM event-late experiment at 20 ns, continued from qualification 38777752196.

## Measured result

| Check | Fast | Typical | Slow |
| --- | ---: | ---: | ---: |
| Extracted setup WS | 0 ns | 0 ns | 0 ns |
| Extracted hold WS | +89.7503 ps | +188.2766 ps | +367.8210 ps |
| Slew violations | 0 | 0 | 0 |
| Fanout violations | 0 | 0 | 0 |
| Capacitance violations | 0 | 0 | 0 |

Final detailed-route DRC errors: **0**. Final antenna violating nets/pins: **0/0**. Final extracted qualification is true, including the unchanged 50 ps fast-hold requirement. Setup WS 0 is a nonnegative acceptance result; latch-related reporting means it is not a strictly positive global setup-margin claim.

The saved final state reports 543,854 µm² total instance area in a 902,417 µm² core (60.27% utilization), including 498,545 µm² of standard cells and one 45,309.3 µm² SRAM macro. Final instance count is 35,490. These are checkpoint metrics before downstream fill/signoff, not an official area-budget exit claim.

## Identity and independent review

- Bulk artifact `12000974401`; gate artifact `12000179151`.
- Final DRT netlist SHA256: `ac646d7424b75d53d61c5726dac5a83780753dd397e4b2b45c1a90b11ed8221d`.
- Effective signoff SDC SHA256: `63a9ac8dc9d00741c26ea37cf8ee01345c2ebf178e1c408dd213619e080d0ffa`.
- Actual final state confirms DRC 0. All three detailed checks.rpt files independently reproduce zero electrical counts. Original 35,481 mapped cells and connections are preserved from the qualified checkpoint; DRT adds nine antenna diodes. These additions remain electrically clean.
- The exact extracted-gate, full-recipe and single-step DRT-config identities are bound by the routed GL validator. A DRT-only config omits synthesis/resizer fields; those are checked in the full recipe, while the reviewed step config is checked byte for byte.

Raw reports, netlists and checkpoints remain in CI artifacts and local /tmp, not committed here.

## What this establishes

The conservative screen followed by live, bounded electrical/antenna repair survived actual stock detailed routing and RC extraction for this checkpoint. This is stronger evidence than a green estimated screen. The recipe retains the original protocol architecture; the latest experiment adds 123 planned plus 24 incremental BUF4 cells before DRT.

## Remaining work

1. Completed: [expanded routed L3 run 38796998628](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38796998628) passes all 22 cases with zero failures, errors or skips on this exact netlist, using Icarus 13 and sigrok. Functional simulation does not include SDF.
2. Preserve this checkpoint as the measured baseline while preparing a reproducible clean-build recipe. Current main's Tiny Tapeout top is still the earlier placeholder; dispatching its unchanged official workflow would not test this prototype.
3. Review/adopt a complete real-design source/configuration candidate and an official-compatible way to reproduce the physical policy. The current experiment depends on accumulated, source-bound checkpoint ECOs; a passing checkpoint does not prove that clean synthesis or the untouched official flow reproduces it. Respect AGENTS configuration restrictions and template jobs.
4. Obtain official full GDS/LVS/precheck/gl_test evidence and finish the remaining Phase 2 checklist. No Phase 2 completion or official green GDS claim yet.

GL preparation checks: 48 focused tests pass across existing/new routed-netlist provenance, hash/config checks, incomplete or failing extracted evidence, and fixed-source workflow validation. The validator also passes on the independently downloaded real routed artifact.
