# Production integration review for the qualified 8x4 candidate

This prepares the remaining integration decision; it does not apply a config
change, promote hardware or approve a release. The current template config at
`4b1204a` is byte-identical to main's project baseline, SHA256
`4b192dffa877dcefa4ab969af9dedf105375921aa179c677524fa88ac94bb510`.
The qualified screen's complete config SHA256 is
`4d71243f672fac34f004c43a8c8bfc46cffaae2b2929f7d3c788de1fac72a9f7`.
Exact values and classification of all 25 changed keys are retained in
[`closure_integration_config_review.json`](closure_integration_config_review.json).
Evidence: [screen 42681697462](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42681697462).

## What must be integrated together

The actual Tiny Tapeout top must instantiate the two-lane/four-pin-unit core;
its generated spec, fabric, encodings, model/compiler tables, source list,
test Makefile and pin documentation must match. This is the existing
protocol-floor candidate, with one full pin unit, rather than a new resource
expansion. Hardware and config must reproduce the same qualified source,
including the pinned SRAM views. Keep the current 8x4 allocation and official
`ttihp27a` template jobs. Do not copy the old plugin/runtime override into them.

## Configuration adoption surface

| Group | Changes from template/project baseline | Existing rule |
|---|---|---|
| Density | 60 to 56 | Explicit whitelist; record final decision |
| SRAM macro | Fixed views, instance, location and orientation | Explicit macro whitelist; retain source hashes and attribution |
| SRAM power grid | Pitch 67.44, offset 26.36, spacing 3.52, custom PDN config and macro connections | Review scope before adoption |
| SRAM abstract handling | PDK source and SRAM abstraction pattern | Review scope; actual final official precheck is still required |
| Clock distribution | No clock NDR, clustering size 8 and diameter 75 | Outside standing config whitelist |
| Hold repair targets | Early 0.175 ns, late 0.125 ns | Outside standing config whitelist; final 0.05 ns fast-hold acceptance stays fixed |
| Setup repair targets | Early and late optimizer targets 0 | Outside standing whitelist; these are optimizer settings, not setup-check waivers |
| Mapping/drive | DELAY 0 strategy, excluded buffer-1, buffer-2 synthesis output driver | Outside standing config whitelist |
| Routing/repair | Adjustment 0.16, 100 overflow iterations, post-GRT design/timing repair, max repair wire length 200, diode-only antenna repair | Outside standing config whitelist; final overflow/antenna/electrical checks remain mandatory |

The unchanged template options remain unchanged, including linter enable,
clock period and port, layer cap inherited from TT, and the template's normal
verification/export settings. The candidate adds no project PnR/signoff SDC
override, no disabled acceptance gate, no custom runtime and no checkpoint ECO.
The separate extracted diagnostic explicitly uses the preserved signoff SDC;
that diagnostic is not proof that the official full-flow endpoint is closed.

The repository permits production `src/config.json` edits only for clock,
density and the SRAM macro block. Session permission to commit/push is not
recorded as permission to bypass that engineering rule. This review identifies
the exact adoption surface so a later decision can cover the tested recipe
without an open-ended exception. No configuration outside that rule has been
applied to production source by this closure branch.

## Remaining evidence before promotion

1. Finish the current continuation's detailed route, native checks and
   extracted all-corner setup/hold/electrical qualification. Preserve any
   failure rather than carrying screen metrics forward as extracted results.
2. Inspect exact native-cell functional replay and current lockstep controls.
   Refresh protocol replay against the exact final netlist after routing.
3. Produce GDS/LVS and pass the current unchanged official precheck on that
   exact layout. A previous older-flow precheck cannot qualify the new result.
4. Review the production source/config bundle, record its adoption decision,
   reproduce the full allowed TT submission flow and recheck required CI.
   Split diagnostic stages and thread/diagnostic controls must not be hidden
   when describing reproducibility.

No higher lane count, extra protocol hardware, ISA change or new clock target
is included in this integration proposal. Phase 2 remains open.
