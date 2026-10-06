# Event-path physical screen audit (2026-10-06)

Successful main screens: event-late37533969613 and load-flat37533972946, revision2b93d42. Each uses frozen3393eea plus exactly its named patch, complete2/4/U0full,20ns,density56,GRT0.16,timing-driven placement and all-corner repair. Candidate artifacts'27tracked source/config/info files match the independently proven source or frozen base. Both paired baseline outputs agree on the reported metrics below.

| Repaired metric | Baseline | Event-late | Load-flat |
|---|---:|---:|---:|
| Setup WS fast/slow/typical(ns) |0/0/0|0/0/0|0/0/0|
| Setup and hold violation counts, each corner |0|0|0|
| Hold WS fast(ns) |0.0360107|0.0313302|0.0236243|
| Hold WS slow(ns) |0.238266|0.229262|0.194447|
| Hold WS typical(ns) |0.103103|0.102516|0.0953171|
| Slew violations fast/slow/typical |0/8/0|0/8/0|0/6/1|
| Capacitance violations fast/slow/typical |0/0/0|0/0/0|1/0/1|
| Fanout violations, each corner |162|166|160|
| Area incl.SRAM(µm²) |508444|510233|509017|
| Instances |33169|33205|33152|
| Final repaired route demand |233872|239415|239238|
| Final repaired route usage |39.08%|40.01%|39.98%|
| Final repaired overflow |0|0|0|
| Final repaired wirelength(µm) |2312373|2351671|2354997|

Event-late adds1789µm²(~0.352%) and2.37%route demand; load-flat adds573µm²(~0.113%) and2.29%demand. Local isolated mapped-area savings did not translate into smaller repaired whole-chip area. Event-late has the better local timing probe and no capacitance violations, but fanout worsens. Load-flat reduces slow slew/fanout counts but adds capacitance violations and lowers estimated hold headroom. Neither has measured extracted WNS yet, and zero estimated setup slack is not positive signoff margin.

Both qualify for the existing bounded diagnostic route gates, independently. Route support is prepared for each variant with trusted checkout+named-patch fingerprints established before artifact download, exact successful main workflow/run provenance, saved identity revalidated during extraction/GL, and unchanged antenna/setup/hold checks.98helper tests and workflow-choice validation pass. No main hardware/config/spec or template job changed. Publication and launches require scoped authorization; neither route is launched in this audit.

Recommend independent routes from37533969613/bs-event-late and37533972946/bs-load-flat, followed by automatic extracted timing and matching GL. Do not combine either with resync before its isolated timing effect is measured. Current reviewed resync extraction37529099235 has slow setup−0.325227853853ns and fast hold−0.008052669870ns; routed GL37529099455 passed at workflow level. This remains a diagnostic near-closure result, not an official pass.

Raw downloads and parsed summaries stay in `/tmp/{event,load,event-baseline,load-baseline}-screen-audit`. Standard gh artifact downloads stalled; direct artifact API downloads completed and were audited. No phase checklist is ticked.
