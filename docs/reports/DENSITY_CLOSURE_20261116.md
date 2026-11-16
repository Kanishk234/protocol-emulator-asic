# One density control after selector antenna residual

Selector screen43951998125 completed with passing original/signoff estimated
timing, electrical checks and final global overflow, but fails one final data
antenna. Original fast hold is0.114093ns. The previous configuration-clock
antenna is gone; the remaining net11655 feeds `_31624_/A2` (a21oi_1), with
Metal3CAR252.71/200, and ultimately U2producer token bit5. Native post-repair
antenna0 does not substitute for the failing final check.

Route43956306270 and final replay43957253552 stopped at their source gates;
neither routed nor tested this unqualified layout. Raw failure is preserved;
compact checked evidence is `selector_screen_43951998125.json`. Ten selected
ZIP reports/netlist were CRC-verified; no local whole-archive digest claim.

D-175 tests exactly density56→60 on the same functionally verified RTL, same
8x4geometry and20ns clock. This moderate tighter placement is a hypothesis
for shortening the remaining data branch. It can regress timing, skew,
congestion or other antenna branches; every original final gate stays fixed.
No margin-only repeat, manual diode, checkpoint ECO, new RTL or waiver.

- [Density screen43961635994](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43961635994)
  at9e4c74f is active in the stock physical flow, with exact2b822640… config.
- [Qualified route43962211849](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43962211849)
  at7ba8d40 waits for that exact screen/attempt1 to pass. Full archive/source
  binding, fresh timing/antenna checks, clean route, extracted three-corner
  timing/electrical and50psfast hold remain required.
- `tripwire-density-final-gl.yaml` is bound to that exact route. It independently
  authenticates both original screen and route archives, reconciles six frozen
  views, requires all extraction gates, and replays the exact extracted-state
  NL for22protocol cases using pinned native cells/Icarus13 and real sigrok.
  Replay remains functional without SDF and is not official GDS signoff.

Full density replay-source reconstruction passes: all170 inputs match the
successful selector regression except the reviewed project-config hash.
124combined guard tests and workflow actionlint pass. The older recipe remains
strict by default; only the density-specific callers admit its exact new hash.
Production source/config and architecture contract are unchanged. Phase2 stays
open; no new extracted closure, GDS/precheck or main integration is claimed.
