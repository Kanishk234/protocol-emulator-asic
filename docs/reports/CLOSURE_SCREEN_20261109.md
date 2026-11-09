# Qualified current-toolchain 8x4 screen

[Run 42681697462](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42681697462)
at `5407d4c278353ec125018f3a3d49de2fd620d9ce`, attempt 1, is SUCCESS.
This is the unchanged full-core `portable_clock75_hold125` candidate at 20 ns,
8x4, with the reviewed stock LibreLane 3.1.0.dev4/Ciel toolchain. It passes
both original-constraint and unchanged-signoff estimated timing checks, the
50 ps minimum fast-hold gate, all electrical checks, final global overflow and
a fresh final-checkpoint antenna check.

| Original-constraint corner | Setup worst slack (ns) | Hold worst slack (ns) | Slew/cap/fanout counts |
|---|---:|---:|---|
| Fast | 0 | 0.127092 | 0 / 0 / 0 |
| Typical | 0 | 0.333103 | 0 / 0 / 0 |
| Slow | 0 | 0.697614 | 0 / 0 / 0 |

Final global-routing overflow is 0; final antenna violating nets/pins are 0/0.
These are estimated-routing results. Setup worst slack 0 does not establish
positive setup reserve, especially with the latch timing model. Detailed
routing, extracted timing, physical GDS/precheck and routed protocol replay
remain unqualified for this new candidate.

## Independent artifact review

Downloaded the whole artifact (347,368,324 bytes), ID `13708390816`, and checked
the API SHA256:
`5bd617e3a926684728f8dd2a0e9dc1a54bbb6229449c2965b5eedfae6aa8a3fb`.
Run/source/attempt/path identity, all bound state/native-view/constraint hashes,
original before/after raw corner metrics, signoff corner gates, final raw
antenna metrics and the final native overflow log reconcile. All 32 non-JSON
hardware/macro files and the project config/metadata match independent
candidate preparation. The compact measured receipt is
[`closure_screen_42681697462.json`](closure_screen_42681697462.json).

The separately authenticated RTL regression is run 42690695832; see the
[protocol matrix](CLOSURE_PROTOCOL_MATRIX_20261109.md). Neither result is
substituted for the other.

## Continuation observer correction

The first continuation, 42692486237 at `b13b439`, correctly passed its source
dependency and then stopped before physical execution. Its new restoration
observer incorrectly assumed an absolute receipt state path. Actual screen
receipts mix a relative state filename and relative signoff filename with
absolute native-view filenames. The physical source is valid; that lexical
path assumption was a diagnostic bug.

The correction resolves receipt paths for reading and compares exact resolved
coverage/hashes, while retaining the producer's spelling when replaying its
existing screen checker. No saved receipt, state, SDC or view is rewritten.
A regression exercises the actual mixed-path format and checks all restored
bytes remain unchanged. The failed run is preserved; corrected hosted replay
is required before claiming actual restoration or routing.
