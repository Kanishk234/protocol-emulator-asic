# Isolated timing prototypes (2026-10-06)

The user requested official GDS timing closure on the complete2-lane/4-unit candidate before attempting3/6 (D-070). These changes preserve cycle behavior, live reconfiguration, features and encodings; main RTL/spec/config remain unchanged during measurement. Candidate base is3393eea9a58c5cad9077cc360a8515d0e5ec8284,20ns,56% density,U0full,12slots/lane,512-word SRAM.

## Implemented and checked

| Trial | Change | Module-equivalence evidence | Existing simulations |
|---|---|---|---|
| bs-resync | Cancel the saturated correction before sample-time arithmetic; compare PERIOD and timer directly for zero phase error |893points; equiv_simple plus induction closing at step1, seq2 cap |21/21bit-clock tests,5/5chip tests,2048L2 clocks/zero divergence |
| bs-csa | Carry-save compression for sample-time subtraction/addition |868points; same proof recipe |21/21bit-clock tests,5/5chip tests,2048L2 clocks/zero divergence |
| drop-qual | Per-source drop qualification and OR reduction |97points each atN1/5/6/7/9/16; same proof recipe |7/7fabric tests,5/5chip tests,2048L2 clocks/zero divergence |
| setup-margin | One post-GRT repair targeting2ns headroom at all corners |No RTL mutation; retains20ns signoff constraints |Helper guard tests pass; physical measurement pending |

Arithmetic is modulo2^25, including wrap and arbitrary live configuration values. No registered lookahead or pipeline stage was added. Proof covers the named RTL modules, not whole-chip formal verification. Short L2 is not a new million-clock claim.

## Local mapped-delay prioritization

Yosys0.69+24 mapped each isolated module with the same pinned typical IHP library; cached OpenSTA evaluated the slow corner with an ideal20ns clock, zero input/output delay,0.01pF output loads and no wire parasitics. For bit-clock modules the query is PERIOD inputs→RX-load; for fabric ports it is source-load inputs→timed endpoints (N9). These different queries must not be compared against one another as whole-chip paths.

| Trial | Mapped module area (µm²) | Targeted arrival (ns) |
|---|---:|---:|
| Bit-clock baseline |40667.3190|13.808641|
| bs-resync |41905.9494|10.669182|
| bs-csa |41565.3336|14.636085|
| Fabric-port baseline |3508.1802|1.254606|
| drop-qual |4121.7120|1.324727|

Resync improves this probe by3.139459ns at+1238.6304µm² (~3.05% module area). This is a prioritization result, not an extracted WNS gain. CSA and fabric qualification are lower priority because they worsen their probes; retain them for reference rather than immediately spending full routing runs. Different synthesis/placement and whole-chip loading can change the outcome. Judge physical candidates by overflow and extracted timing, not area alone.

## Reproduce and measure

Run Python in the project venv. The verifier creates a new directory outside the repository, archives exact frozen hardware plus current independent test/model fixtures, applies only the selected patch, and runs module-equivalence checks. Optional simulation runs the affected unit suite, chip tests and2048-clock L2.

```sh
source .venv/bin/activate
python scripts/ci/verify_timing_trial.py bs-resync /tmp/tripwire-bs-resync-check --simulate
```

Raw current evidence: `/tmp/timing-prototypes-20261006/{bs-resync,bs-csa,drop-qual}`, and `probe/` for local mapped timing. Reusable proof also passed in an output directory containing spaces. Bugs68/69 record corrected fixture/include issues; reruns passed.

The existing `.github/workflows/gds-drop-counter-screen.yaml` now displays as `gds-rtl-timing-screen` and accepts one experiment choice. Each dispatch compares unchanged timing-placement against exactly one trial, fresh synthesis through GRT and fresh three-corner STA/repair. Default drop-counter behavior remains available. Named choices include drop-counter/drop-qual/bs-resync/bs-csa/setup-margin. Template GDS jobs are untouched. Scripts reject unknown trials, wrong candidate revisions, pre-existing tracked changes and unexpected changed files; only setup-margin adds a2ns repair target.

Prioritize bs-resync and setup-margin physical screens. Once a candidate is measured, route/extract it with exact modified-source provenance (current route continuation accepts only unchanged-RTL physical variants). Do not feed modified RTL to that continuation or claim it is unchanged. After isolated routed wins, combine deliberately, run fresh full synthesis, make a reproducible official-flow candidate, and require actual positive slack margin and all official GDS/precheck/GL checks. No phase boxes are ticked here.
