# Selected SRAM screen: residual repair priorities

Source: [screen 38111368461](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38111368461), artifact 11692116594. Preliminary global-route estimates; extracted continuation [38112320460](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38112320460) remains authoritative for the next physical repair.

Exact final screen netlist SHA-256: `2c00046d787af2d045bbb61a9fab4e15b0356c34ffb6d7397a950f6ecf104a80`.

Report rows independently match saved slow-corner slew 34 and fanout 18. Mapping to exact connected pins finds 14 data branches and four clock branches. Capacitance metrics are zero; the preliminary report omits that section, so this is not a complete electrical-report signoff audit.

| Target | Evidence | Small next repair | Cost and limitation |
|---|---|---|---|
| `_28807_/Y`, net `_03831_` | 17 slew rows; 16 loads, including 8 diodes; NAND3_1 | Partition nearby sinks into four BUF4 branches | Four cells; no stronger NAND3 variant available; fresh antenna insertion can consume load reserve |
| `_28820_/Y`, net `_03844_` | 14 slew rows; 13 loads, including 6 diodes; NOR2_1 | Partition into four BUF4 branches | Four cells; source drives four buffer inputs; timing must be remeasured |
| SRAM A_REN | 1.014359 ns slew against 0.595200 ns limit | Reposition existing REN driver toward macro before adding a stage | No added cell if existing driver can move; shared hold paths must remain above 50 ps |
| SRAM A_ADDR0/6 | 0.640266/0.628722 ns slew against 0.595200 ns | Inspect extracted wire load and existing driver strength/location | Small deficits; avoid unnecessary blanket upsizing or hold-buffer removal |
| Four clock branches | 16 BUF8 sinks each, no antenna diodes | Retune branch placement/depth with setup and hold budgets | Prior eight-buffer split worsened extracted setup; do not transplant it unchanged |
| Remaining 12 data branches | Mostly 9–16 loads with diode contributions | Repair only after these two dominant nets are measured | Lower immediate slew coverage; indiscriminate buffering adds routing pressure |

31/34 slow slew rows belong to the first two nets. This is concentration of reported violations, not proof that buffering removes every row or preserves timing. Their two fanout violations are included among the 18, so this repair alone cannot close electrical checks.

Read-only spatial partitions on the exact screen DEF conserve every original sink and diode exactly once: 16 loads become four groups of four; 13 loads become groups 4/4/4/1. Each source then drives four buffer inputs. Eight BUF4 cells have nominal master footprint 116.1216 square micrometres (3.84 by 3.78 each); this excludes legalization whitespace, new diodes and routing costs. Candidate groups are not legalized or physically qualified. Raw proposals remain in /tmp.

Next: inspect current extracted continuation; re-pin its exact netlist/DEF and recompute placements. Apply one dominant-net repair first, preserve all diode connectivity, reroute and check setup/hold/electrical/antenna/overflow. No changes to hardware, clock constraints, protocol support or phase checklists are justified by this analysis alone.

## Extracted follow-up and first physical screen

Run 38112320460 succeeds but does not close requirements: slow setup -2.614797 ps, fast hold 48.963834 ps. Complete electrical audits show slow/typ/fast slew 147/43/4, fanout 20 each and capacitance 4 each. The two dominant branches still retain their reviewed 16/13 loads and 8/6 diodes. Repinned planner to actual DRT netlist SHA `1da984a3d76325e06e39de478f8d8cf4c24d812970df97dff72f5ee9f1244cfe` and DEF SHA `7a6172759a31a18f20c1ae2b3fd17cce4bd699c3ae18d06ece0f0b887e8fab87`; both synthetic partition topology audits pass on these exact files.

Worst slow setup is _48179_ to _46883_; worst fast hold is _48776_ to _46037_. The first proposed screen changes only _28807_, four BUF4 branches, nominal added footprint 58.0608 um2 before diodes/whitespace/routing. It uses the existing guarded residual OpenDB binding and wrapper, with full source/recipe/hash checks, exact all-cell topology validation, DPL, old-wire reset, zero overflow, antenna-only cleanup and fresh all-corner 50 ps hold gates. No signoff limits are relaxed; success remains preliminary pending detailed routing/extraction.

Prepared dominant_slew_screen.py and separate gds-dominant-slew-screen workflow, pinned to the successful extracted run and exact main head a6e44b457e11e368ebcdd2f3fdafdfd68147cde0. 123 focused tests pass. New physical split has not yet run. The original SRAM screen evidence above is historical; do not use its old DEF for this new repair.
