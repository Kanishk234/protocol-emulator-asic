# Representative R1 PDN, placement and global routing

D107 continues the audited native preflight39996455894. Both fixed widths reuse the exact frozen mapped LUT netlist and I/O layout policy; only footprint/boundary dimensions differ. The experiment adds tap/endcap policy, native PDN, pinned output-only buffering, global/detailed **placement** and native global routing. It does not perform detailed signal routing.

Policy: same height/margins, pinned tiny-tile96%density, no timing-driven placement or logical resynthesis, Metal2–Metal4signals, fixed50global iterations/0.3capacity adjustment. Full native final congestion table and overflow metrics must be zero. Power-grid violation count must be zero; actual Metal4PGpin centers must match the first-column global phase and span tile height. Original nonbuffer cell counts and438configuration latches must survive. Added physical cells/area are retained.

The verified narrower core starts at89.90%bare occupancy (39996455894), so actual buffer/tap/power overhead may exhaust it. This is a discriminating physical test, not a fit promise. Both widths run independently, with fixed45min native budgets; errors keep the job red and retain the latest completed state. No widened footprint or budget search is pre-authorized by the runner.

CLOCK_PORT=null permits geometry/congestion observations but provides no configured clock/timing acceptance. No CTS/timing repair, detailed routing, antenna/signoff, SDF, other tile types, real shell or whole-chip acceptance. Source/buffer adapter hashes and resolved policies are retained. Hosted results pending.
