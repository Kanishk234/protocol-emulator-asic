# WARP resumption: configured timing before another physical campaign

The user requests making eFPGA work. Preserve selected G1 and distinguish its
shell-only timing/RTL-fabric simulation from full native configured timing.
No hardware, generated fabric, held-out protocol, template job or production
configuration is changed by this work.

## Reproduced starting evidence

Timing run40128859740 at97f655a, attempt1, failed as expected. Whole artifact
12574475845 is authenticated against SHA256
d3ebcd915e82c6b9646648efe0053e2baf2d790312769beff707bb99e9d0f900.
Its result classifies370edge registers and246endpoints; six endpoint slacks
differ by approximately16.122ps between static/dynamic loop policies. Worst
cell-only setup is+1.508933ns; this does not qualify timing. Eight structural
loops remain. The two LE/LG all-feedback cofactor failures are also retained.

An independent direct-frame probe checks438native LUT-tile latch values against
the loaded image with0mismatches. The new configuration_audit.py extends this
to all40tiles/8736bits in cloud CI; it uses actual native latch D/GATE-to-frame
wiring, not merely snapshot equality after reload.

## First controlled experiment

D-122 probes the existing output-register selection on unused X2Y3/G. Original
FASM declares neither that BEL nor a routed LG_O source. Locate its select bit
from the frozen bitstream specification and native frame wiring, not a guessed
configuration index. Change analysis case0→1 and its corresponding sanity guard;
preserve original scripts and all original topology/timing arcs.

The experiment first reproduces the exact six-endpoint failure. It then reports
whether the candidate still depends on the timing loop policy. Even a favorable
result is not functional, delay/hazard, routed or physical acceptance: the changed
configuration has not been loaded. Negative measured outcomes are retained too.

42focused tests, actionlint and embedded Python parsing pass; original-capsule
preparation succeeds. An initial console-pytest invocation overrode import paths;
the project's python -m pytest invocation passes without bypasses. No tool or
hardware failure is inferred from that invocation error.

## Work sequence

1. Complete the full-grid configuration audit and one-bit sensitivity probe.
2. If supported, derive a separately scoped opt-in image and run actual native
   configuration, concurrent UART/SPI, reset, STOP/restart and reload checks.
   Preserve original negative controls and all active-feature bits. Inspect
   delay/hazard obligations before treating feedback changes as timing closure.
3. If unsupported, use the retained native cones/counterexamples to select the
   next structural or configuration experiment; do not waive timing arcs.
4. Qualify remaining detailed leaf contexts, then assemble macro and fixed shell
   with matched extracted views, clocks and functional replay. One leaf's route
   or ideal-wire timing does not qualify the complete fabric.
5. Review adoption of the current official CMOS5L template/8x4 allocation before
   modifying the older frozen6x4contract. More area does not repair timing-model
   ambiguity. Finish actual GDS/precheck and preserve honest claim scopes.

No phase checklist boxes are ticked. Existing G1/compiler/ABI controls and sealed
held-out set remain protected. Heavy EDA runs in GitHub Actions.
