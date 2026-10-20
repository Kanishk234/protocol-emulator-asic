# Southern corridor: an exact local capacity obstruction

The first native-derived bounded solve returns INFEASIBLE. An independent
arithmetic cut confirms the result: **five nets must cross a plane with only
four units of remaining capacity**. This concerns a fixed window/cohort and
frozen exterior, not whole-chip impossibility or physical signoff.

## Source and model

Inputs come from authenticated native run 39367564921, source 8782e28, attempt 1;
see [the terminal qualification](native_terminal_run_20261019.md). Exact native,
terminal and initial-segment SHA256 values are respectively `1859f6fdaffad9977ab4025867332a5835e68f50b86405719447b1b3c1aa07e6`,
`90be2ecef64627ed67b1c4df920f86f673cac1bcdae4fef4db9587a3e79a18d3` and
`19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c`.
Committed extractor a3eb447 reconstructs the model without routing or EDA.

The inclusive window is x=8..17, y=0..9, all four layers. It contains one
initial overflowing edge, H(layer0,x16,y1). Select all five owners: native slots
32, 120, 123, 124, 387 (delaynet_3_clk, cell_val[27], cell_val[31], cell_val[32],
frame_strobe[0]). All selected physical/coarse memberships and access pass;
the whole terminal gate remains false. This is a different cohort from the
previous two-net native repair.

The graph has 400 vertices, 1,020 edges and 10,200 solver variables. Exact old
multiset release removes 51 weighted planar step occurrences. Original
capacities and all fixed background demand remain; published native route
connectivity freezes the exterior. Every required native pin is connected in
the original published route; its planar support matches the raw STEP support.
Unlimited coarse vias are an explicit relaxation. Physical via feasibility,
native search/access constraints, detailed routing, timing and antenna are
not proven. All native/physical/timing authentication flags remain false.

## Result and independently checked cut

Pinned OR-Tools 9.14.6206, one worker, 30-second/10-deterministic-unit bounds,
returns INFEASIBLE. This result is not treated as a solver proof certificate.
A separate graph-only arithmetic checker and independent reviewer establish:

- All five nets have required terminals on opposite sides of x16|17.
- Every layer demand is one. There are no private exterior connections crossing
  the plane, and same-XY vias cannot cross it.
- Across all 40 crossing planar resources, total residual capacity is four;
  only H_0_16_1 has positive residual.
- Every individual net is reachable, and no fixed edge is already over capacity.
  Thus the obstruction is collective, rather than a disconnected-terminal or
  already-invalid-background artifact.

The necessary inequality is 5 <= 4, which fails. No rerouting algorithm can
satisfy this declared fixed problem. It does not rule out changing the window,
freeing another lane's owners, changing exterior topology, or a future physical
candidate. The other three southern crossing lanes are occupied by fixed nets;
next work must measure an alternative crossing/topology instead of repeating
negotiation on the same blocked paths.

Canonical graph SHA256 `7f49b0ddb0ea3976cdf4c7f4191f4099f1fd8a60da1a1037de251c4dfb73b8d0`;
serialized graph `8c6a07d806c9535320b416ce89bd2e43e913c5c1e8306c2b482d65aeddd28847`;
solution `509e8cd298450ed28b7251784079cd0ed13fd0bd0505fdb150f63ac4e2b1171a`;
independent cut certificate `c4ae0de72fa3700be4ef94d731d1aac1278fb66e07a5e58f0f92975be6a47746`.
Ignored artifacts are in build/corridor112_south/. Raw native source evidence
remains in CI. Independent review/reconstruction and graph-only certificate
snippet: [corridor_south_exact_review_20261019.md](corridor_south_exact_review_20261019.md).
