# Representative R1 PDN, placement and global routing

D107 continues the audited native preflight39996455894. Both fixed widths reuse the exact frozen mapped LUT netlist and I/O layout policy; only footprint/boundary dimensions differ. The experiment adds tap/endcap policy, native PDN, pinned output-only buffering, global/detailed **placement** and native global routing. It does not perform detailed signal routing.

Policy: same height/margins, pinned tiny-tile96%density, no timing-driven placement or logical resynthesis, Metal2–Metal4signals, fixed50global iterations/0.3capacity adjustment. Full native final congestion table and overflow metrics must be zero. Power-grid violation count must be zero; actual Metal4PGpin centers must match the first-column global phase and span tile height. Original nonbuffer cell counts and438configuration latches must survive. Added physical cells/area are retained.

The verified narrower core starts at89.90%bare occupancy (39996455894), so actual buffer/tap/power overhead may exhaust it. This is a discriminating physical test, not a fit promise. Both widths run independently, with fixed45min native budgets; errors keep the job red and retain the latest completed state. No widened footprint or budget search is pre-authorized by the runner.

CLOCK_PORT=null permits geometry/congestion observations but provides no configured clock/timing acceptance. No CTS/timing repair, detailed routing, antenna/signoff, SDF, other tile types, real shell or whole-chip acceptance. Source/buffer adapter hashes and resolved policies are retained. Hosted results pending.

Run40007850249 stopped at source admission for both widths: original upstream buffer script was fetched while the guard expected its explicit-buffer-cell adapter. Frozen netlist unchanged. BUG123 owns and authenticates the exact two-line patch; this run provides no PDN, placement or routing outcome.

Run40009049924, sourced85369625ec047ce5a521a9b1f0516ad24143f62, completes both native flows through global routing. Final native overflow is zero on every layer, and final VPWR/VGND grid checks have zero violations;2486power terminals checked and438configuration latches retained in each. Workflow is red only because BUG124 rejected auxiliary200nm boundary pin patches despite full-height stripes. Corrected checker replay against both retained result files and ODB SHA hashes passes locally; hosted green replay still required.

| Width (µm) | Native instance area (µm², rounded metric) | Core utilization | Global routing resource usage | Final overflow |
|---|---:|---:|---:|---:|
|219.84|24385.5|64.116%|41.40%|0|
|154.08|24385.5|92.5429%|58.58%|0|

Native run40009049924 supplies these measurements. Narrowed tile has limited placement reserve. This is one first-column LUT tile, output-buffered, no configured timing or detailed signal routing; other tile types, column power phases, shell and full-grid integration remain unqualified. It does not establish equal-total-area superiority over G1.

**Hosted replay accepted within representative scope:**40009616432 at6b2908894d2eefe53bbb1e523d5e924761ef6e8f attempt1SUCCESS, both matrix jobs. Root recomputation authenticates API identity, mapped/adapter hashes, all final layer overflow fields, zero final PG violations,2486PGterminals,438latches, grouped stripe geometry and retained ODB SHA. ODB hashes exactly reproduce40009049924: reference3bc82ec3b9402873a890b03896d4c2429e6f430471f87899d4066f7a2640efec; narrow5e1aa36e26cdae9c1ceabae85e4c8e277850519924a1187445d1c25f097bfc5a. No independent specialist review claimed.
