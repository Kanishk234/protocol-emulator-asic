# Current-source formal refresh, October 18

[Run39143521760](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39143521760) at a81eac9b3525ff149a683bc959069f25a62da0df succeeds in all four jobs. The coordinator downloaded all four artifacts and inspected all seven task logfile.txt files, each ending DONE(PASS,rc=0). This is hosted native proof evidence, not merely a workflow badge.

| Property | Actual engine/result | Scope |
|---|---|---|
| F1 output isolation | Yices temporal induction + base case PASS | Unbounded named isolation assertions, fabric outputs unconstrained |
| F2 loader | ABC bmc3, no assertion output in84frames; cover reached step52 with Yices | Safety bounded84cycles; reachable-load witness within cover depth60; not unbounded loader proof |
| F3 FIFO | ABC PDR Property proved for d2 and d4 | Unbounded named shadow-queue assertions at FIFO depths2 and4 |
| F4 timer/shift | Yices successful temporal induction + base case for both | Unbounded named primitive equivalence assertions under each harness |

Proof files and checked RTL are unchanged from the prior successful proof source ee259cb48dbbb82b233bc6ac68e558cd8942beab (git diff empty for src, formal, arch/prims, scripts/formal.sh and formal workflow). Current-source execution independently refreshes that evidence without changing any property or bound. Raw logs remain ignored build/formal110 and GitHub artifacts; the local seven-file hash inventory is build/formal110_verified.json.

This does not prove complete compiled-fabric correctness, physical timing, equivalence of every architecture, or properties outside the named harnesses.
