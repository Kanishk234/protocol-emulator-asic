# Global routing cohort obstructions — October 19

The fixed five-net routing problem is infeasible across the full coarse grid,
not merely inside the southern window. This changes the next experiment from
another search budget to coordinated release of additional blocking routes.
It does not prove whole-chip routing impossible.

Authenticated native source: run39367564921, attempt1, source8782e284e94706486f20f25248c7067eecdf0d70;
original resultSHA8ac9ecbb64903a9296cd7cb6fd36633417933d9723e041537ea79091a1f73674.
The read-only campaign rechecked every native control, raw ledger and terminal
join. Exact source checkpoint identities remain in native_terminal_run_20261019.md.

## Actual solver outcomes

| Cohort | Nodes / edges / variables | Bounded outcome |
| --- | --- | --- |
|32,120,123,124,387, local window|400 /1020 /10200|CP-SAT and SCIP INFEASIBLE; independent axis cut5>4|
|Same five, full coarse grid|3210 /5526 /55260|CP-SAT UNKNOWN; SCIP INFEASIBLE; independent partition cut5>3|
|Five plus70|3234 /5557 /66684|SCIP INFEASIBLE; independent partition cut5>2|
|Six plus1162|3242 /5572 /78008|No MIP run: independent partition cut6>2 already rejects|

Every actual solver call used one worker,30s wall bound and1024MB solver memory
bound; CP-SAT additionally10 deterministic time units. These are solver limits,
not an OS memory enclosure. No seed/budget sweep. SCIP9.2.2/SoPlex7.1.3 comes
from pinnedortools9.14.6206; backend sourceea8cc27. SCIP's status alone is not
an independently checkable infeasibility proof; the arithmetic cuts provide that
separate check for the supplied graph. CP-SAT UNKNOWN remains inconclusive.

Five-net canonical graphSHA9fc8041f91eef1fab1b20f83c3ddda43177d246167e97c008b3b0bf48cdf98cc.
Full-layer aggregation assumes unit demand, all native planar layers available,
and unlimited coarse vias. Capacities are exact original residual capacities;
fixed background overflow112 is retained, with no capacity inflation. The model
releases exact selected old STEP multiplicities. All other nets stay fixed.

## Why the cohort needs to grow

One explicit global partition has only aggregateH_17_1 with residual3, while
all five nets must cross it. A second partition has onlyH_18_1 with residual1,
while four of the five must cross. These are arbitrary graph partitions, not
axis planes; trying a wider rectangular window cannot remove their deficit.

Slot70, cell_en[24], has both pins on the same side of the first partition but
its existing detour occupies two boundary resources. Releasing it repairs that
particular inequality to5required/5available. The resulting six-net model exposes
a different partition: residual2 onH_18_1 andV_15_68 against five required nets.

A measured boundary-owner ranking then selects slot1162/net39, whose old route
releases four units against one additional required crossing. The seven-net
model still exposes another partition: residual2 onH_18_1 andV_16_70 against
six required nets. Stop solver calls when this independent necessary condition
already fails. These nested obstructions explain why small targeted repairs
can merely move congestion into frozen neighbors.

The final partition's original full native planar capacity is798, with395
native nets requiring at least395 units across it. That exploratory count does
not prove feasibility, but this partition does not show a whole-chip deficit.
More coordinated rerouting is required before blaming architecture or placement.

## Retained checks and next step

`capacity_cut.certify_partition` validates an explicit proper node subset,
rejects net-private exterior bypasses/unbounded resources/fixed violations, and
refuses via-crossing partitions (BUG104), and recomputes crossing residual capacity versus a conservative demand lower bound.
It invokes no solver. Optional bounded terminal-pair mincut discovery proposes
partitions; each is passed through that independent arithmetic checker. Failure
to discover a cut is inconclusive.21focused tests pass, including orientation,
fixed usage, invalid subsets, bypass rejection and restricted discovery bounds.

Local ignored artifacts are underbuild/corridor112_scip_campaign,
build/corridor112_expanded70 andbuild/corridor112_expanded1162. No raw native
outputs are committed. Independent result review confirms all actual cuts and same-graph CP/SCIP identities. Hosted reproduction39371954205 atbe895de SUCCESS:326executed testsPASS/0skip; local/global SCIP INFEASIBLE and exact graph/LP hashes match local. Dedicated backend qualification39371931884 SUCCESS:301executed testsPASS/0skip. Both downloaded artifacts independently audited. A post-download independent cut on the hosted graph confirms4>1 atH_18_1. The old hosted campaign did not retain that cut automatically; subsequent8d0f585 adds automatic retention,14campaign testsPASS. Full local autonomy703executedPASS/0skip. Next: use certified cut boundaries to select a joint
cohort, checking necessary cuts before expensive feasibility search. Preserve
100k solver-variable cap; use reviewed graph reduction if joint scope exceeds it.
No native route installation, physical via/DRC, timing or accepted routing gain.

## Joint selection follow-up (October20)

A bounded exploratory search ranks at most80 unit/all-layer native candidates,
then checks single/pair/triple additions against the first three known cuts.
Four two-net additions satisfy those particular inequalities:1318+3031,
1429+3031,3031+136,1460+3031. Each resulting seven-net model passes selected
terminal admission but exposes another certified deficit (6>1 for the first
three;6>2 for the fourth). No routing MIP is run on these rejected graphs.
This candidate list is truncated and does not establish a minimum joint cohort.

A separate exploratory cut-cover selection MIP considers all eligible unit/all-layer
nonbaseline native nets and all seven discovered partitions, permits at most
three extra nets, and linearizes exact nonnegative residual capacity after
old-route multiset release. One bounded30s/1024MB/oneworker SCIP call on
4384variables/1109constraints returns NOT_SOLVED (UNKNOWN), with no selection.
No routing feasibility or lower bound on necessary cohort size follows.
The temporary script/model remain local diagnostics, not a qualified retained
planner. Any future returned selection must have all margins independently
recomputed, then pass full model admission and fresh partition checks.

This leaves the next useful step as a qualified joint-cohort planner or exact
graph reduction supporting a broader coordinated release, rather than more
solver calls on the disproven five/six/seven-net problems. Native guide handoff
still needs its own independently reviewed installation/accounting path.
