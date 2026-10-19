# Escaping repeated routing experiments: change the question

The next useful question is whether the congested corridor admits a simultaneous repair under a declared routing model. Another negotiation variant that ends with a different positive overflow does not answer that question. The [used-grid experiment39143364213](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39143364213) corrected discovery of all439 initial overflow owners but never beat the protected121 control; see [its measured result](used_grid_result_20261019.md). This report proposes work; no new solver, tool installation, dispatch, hardware change or routing success is claimed.

## First choice: a bounded exact local routing model

Use a pinned CP-SAT or integer-programming solver on a small extracted corridor. This is an engineering proposal, not an upstream-supported OpenROAD feature. It changes joint route selection rather than seeds, iteration count or capacities.

1. Authenticate the exact121 snapshot and source identity. Select one actual connected overloaded-edge component and a deterministic bounded halo. Preserve every intersecting route's name, layer, multiplicity, boundary crossings and fixed exterior connections. Obtain native pin-access terminals where a pin lies inside; a route endpoint is not automatically a real pin. Freeze unaffected routes and account for their demand once.
2. Build a layer-expanded grid with exactly exported edge capacities and separate actual preferred boundary edges. Declare permitted nonpreferred motion, vias and terminal-access rules explicitly. The current preferred-direction reporting grid alone is insufficient to claim a full physical routing model: missing nonpreferred/via constraints must be supplied or identified as a relaxation. Preserve NDR/weighted demand and union occupancy by net; do not count each sink commodity as a separate physical wire on shared tree edges.
3. For each selected net, introduce binary occupied-edge variables and root-to-terminal connectivity flows gated by those variables. Shared undirected capacity counts the net's union of occupied edges, not flow magnitude. Give disconnected exterior components separate boundary terminals so that a local shortcut cannot erase a required connection. Capacity constraints include fixed exterior/background usage. Minimize overflow first; require exactly zero for a constructive capacity-feasible result, then minimize wire/vias as a secondary objective.
4. Independently re-evaluate exported occupied-edge witnesses, all terminal connectivity and unchanged outside routes. A candidate must later survive native guide import/normalization, complete guide coverage, full-grid metrics and native acceptance before detailed routing. Never manufacture a zero by changing reporting conventions.

Start with one component, explicit model-size and wall-clock/memory limits, one worker for reproducibility, and a serialized model/input hash. Report actual variable counts, solver version, status, bound and witness hash. A path-choice model with several enumerated candidate trees is cheaper, but its infeasibility only means the supplied menu was insufficient. An edge-flow model permits more topology freedom but costs more memory and connectivity constraints; no runtime estimate is established for our extracted graph.

Interpretation must remain precise:

| Result | What it establishes | Next decision |
|---|---|---|
| Independently checked feasible witness | A simultaneous repair exists in the declared model with frozen surroundings | Implement a bounded native route/guide handoff and validate it |
| Proven infeasible restricted window | That window, fixed background, terminals and rules cannot work together | Expand a specifically implicated boundary/net set; no claim that the chip is impossible |
| Infeasible optimistic relaxation with a valid separating cut | Even the relaxed declared graph cannot support its compulsory crossing demand | Review model/terminal export, then justify a targeted topology or floorplan change |
| UNKNOWN/time or memory limit | No conclusion about feasibility | Preserve the model and bound; do not relabel a timeout as impossibility |

A cheap first stage is a checkable cut witness: partition the graph, identify distinct nets with mandatory terminals on both sides, sum their minimum crossing demand, and compare with *all* legal crossing capacities. A horizontal/vertical rectangle is not a universal cut if nets may escape around it or change layers. An optimistic cut bound should permit omitted alternatives, not silently forbid them. A violated cut in a frozen-residual model proves only that restricted repair impossible; a genuine whole-design obstruction needs an appropriately relaxed whole graph and actual terminal constraints. Ordinary single-commodity min-cost flow is useful for one-net subproblems, not a substitute for shared-capacity, multi-net connectivity.

[OR-Tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver) requires integer constraints and distinguishes feasible, proven infeasible, invalid and unknown outcomes. [Its flow documentation](https://developers.google.com/optimization/flow/mincostflow) describes supplies, demands and arc capacities; the multi-net construction above is our proposed additional model.

## AI and other search approaches

| Approach | Concrete fit | Integration and compute cost | Evidence needed before spending further |
|---|---|---|---|
| Independent reasoning agents | Separate exporter/model review, routing-algorithm research and adversarial witness verification | Session agents can inspect the same reproducible bundle; independence must include different hypotheses, not repeated prose | A new falsifiable prediction, a minimal counterexample or independently checked constructive witness |
| NVIDIA differentiable global router (DGR) | Optimizes routing-pattern choices through a differentiable objective and feeds results into revised CUGR2 | Separate CUGR2 build, data extraction, PyTorch/torch_scatter environment, output-to-guide adapter and reproducible CPU/GPU execution; our PDK/capacity equivalence is unproven | First reproduce the unchanged grid/capacities, terminals, weighted demand and guide inventory; only then compare full-grid outcomes |
| AlphaChip | Learns macro location/orientation with congestion and density proxies | Netlist conversion, clustering/technology mapping, TensorFlow/TF-Agents/DREAMPlace stack and training/fine-tuning; source supports distributed GPU/actor execution | A demonstrated placement degree of freedom linked to a measured cut, followed by real downstream routing; no benefit inferred from a proxy |
| OpenROAD AutoTuner | Schedules parameter search with Ray and several search algorithms | ORFS-oriented configuration/metrics adapter for our LibreLane flow; many CPU routing trials unless tightly bounded | A new narrow parameter mechanism with protected capacities/clock/margins and a predeclared rejection rule |

The [NVlabs DGR source](https://github.com/NVlabs/Differentiable-Global-Router) specifies PyTorch, torch_scatter and revised CUGR2. Its pipeline extracts tree/layout data, optimizes choices, and gives CUGR2 a `--dgr` input replacing its own pattern-routing decision stage. This is a credible algorithmically different experiment, but not a drop-in AI repair for OpenROAD. Repository scripts include GPU-indexed searches; no WARP hardware requirement or speedup has been measured. Existing CUGR run38292828402 failed our weighted-grid guards, so repeating CUGR or comparing its raw overflow with121 would be misleading. DGR is contingent on fixing that compatibility problem, not a reason to waive it.

[AlphaChip's primary repository](https://github.com/google-research/circuit_training) provides floorplanning, fixed-macro support, a TPU-pretrained checkpoint and technology/netlist conversion machinery. Our present fixed compact macro and narrow corridors offer little obvious macro-placement freedom; this is my applicability assessment, not a measured AlphaChip result. Moving shell cells or changing the macro floorplan would require a new physically controlled experiment. A large learning stack is not justified merely because it carries an AI label.

[OpenROAD AutoTuner documentation](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/docs/user/InstructionsForAutoTuner.md) exposes Ray-driven search, including Bayesian/evolutionary methods, and routing layer-adjustment/seed knobs. Those knobs can change the problem or repeat rejected search. Lock resources and constraints, and use it only if a new measured mechanism needs a bounded combination search. It does not certify routability.

## Recommended autonomous loop

Protect121, original133 and the frozen G1 fallback separately. Admit experiments by hypothesis class, not by available tool: geometric necessity/cut, simultaneous topology choice, native negotiation/history, layer assignment, or exporter/model correctness. Each gets a predicted discriminating result, fixed inputs, finite cost cap, independent validator and explicit rejection memory. After a rejected class, require new evidence before reopening it.

Proceed first with authenticated local graph extraction and a checkable cut/terminal audit; then one bounded exact feasibility model. Keep DGR as a second, separately scoped path contingent on capacity-compatible export. Use reasoning agents to challenge both models and source interpretations. Another model's confident explanation alone cannot promote a route; it must produce a checkable artifact that changes the next engineering decision. No external AI service was called, no account/paid access is assumed, and no third party was contacted.


## Implementation follow-up

The explicit-graph oracle is now implemented in tools/autonomy/corridor_solver.py,
with optionalortools9.14.6206. [Hosted39290648912](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39290648912)
atde26ea4 qualifies117 executed passing tests; downloaded strictXML, package pin
and full source revision were independently checked. Local combined oracle and
repair-auditor qualification has138 clean passes. Native input authentication
and physical acceptance remain false. The native corridor contract report
identifies the remaining export/reconciliation gate. Earlier statements about
no installation describe the research stage, before this implementation.
