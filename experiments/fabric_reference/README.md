# Persistent reference reconfiguration experiment

Current result: each image works from startup, but counter-to-LFSR reload
stalls during configuration. A frame snapshot and read-only live probe
demonstrate intermediate LUT feedback at column 1/frame 12.
The runner intentionally fails this gate;
see `docs/reports/ANISH_REFERENCE.md`. A wall timeout is a failure, never
an expected-pass condition.

Follow-up: the reference-only LUT/carry hold candidate passes quick A/B/A
and B/A/B. See `docs/reports/ANISH_RELOAD_EXPERIMENTS.md` for its validation
and limits. It uses a separately patched fabric copy; the ordinary stock
runner and its failing regression remain unchanged.

This experiment generates the stock FABulous fabric once, compiles a counter
and an LFSR using the same wrapper, then loads counter / LFSR / counter into
one persistent RTL simulation. It checks reset priority, disabled hold,
counter wraparound, long LFSR sequences and output-enable pins. A separate
arithmetic oracle checks the pins; the user circuit RTL is not compiled
into the simulation. A wrong-image run must fail with a functional mismatch.

`wp_smoke_signature.v` is an earlier combinational smoke-design draft. It
is retained for reference and is not used by these runners or their results.

From WSL in the repository root, using FABulous 2.2.0 in the project venv:

```bash
source .venv-fabric/bin/activate
export PATH="/home/awsma/eda/2026-06-29/oss-cad-suite/bin:$PATH"
bash scripts/fabric_reference.sh
```

Adjust the venv and tool installation paths to your machine. The toolchain
must be OSS CAD Suite 2026-06-29, installed at a Linux path without spaces.
Download it from the [official release](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-06-29).
The repository itself may contain spaces; generated Taskfile paths live
under `/tmp`. Every invocation creates a fresh directory and retains its
evidence under ignored `build/fabric-reference-*` on success or failure.
Allow several minutes for the full reference simulation. `+cold_b` checks
the LFSR from startup; `+quick` shortens the first counter exercise for
reload diagnosis. The normal script uses the full counter-wraparound test.

To reuse saved images instead of recompiling and routing them:

```bash
bash scripts/fabric_recheck.sh build/fabric-reference-warp-reference.OBUfXfus
# Optional independent full-counter check:
bash scripts/fabric_recheck.sh build/fabric-reference-warp-reference.OBUfXfus counter
# White-box failing witness, separate from acceptance:
bash scripts/fabric_recheck.sh build/fabric-reference-warp-reference.OBUfXfus probe
# Static SCC analysis after 33 new frame records:
bash scripts/fabric_snapshot.sh build/fabric-reference-warp-reference.OBUfXfus 33
python -m pytest experiments/fabric_reference/test_frame_snapshot.py tools/fabric_audit -q
```

Use the actual saved build directory from your reference run. `probe` mode
intentionally returns failure; a diagnostic marker is never a reload PASS.
The snapshot decoder supports only this pinned 10-column, 14-row,
20-frame reference format. Its static emulation configuration is unsuitable
as an acceptance substitute. Snapshot JSONs are large and remain ignored
under `build/`; routine rechecks use the cached images and live loader.

Evidence includes tool/package versions, input source hashes, both binary
images and hashes, compilation/P&R logs, positive and negative simulation
logs, and the configuration mapping audit. The counter and LFSR have the
same module name intentionally: FABulous's stock wrapper auto-connects only
its demo interface. They are compiled separately, never together.

The public loader reset is asserted before each configuration. No internal
configuration or user registers are forced/deposited. User state is reset
through `io_in[0]` after each load. Thus this is a complete reload test with
explicit reset, not uninterrupted execution or a partial-reconfiguration
test. The current images retain the same output-enable pattern.

The test runs at a slow simulation clock. It does not establish CMOS5L
timing, actual chip capacity, shell safety, load corruption recovery or
physical correctness. The stock reference has 672 logic cells and is much
larger than the proposed tapeout fabric. See the architecture checkpoint
in `docs/reports/ANISH_UPSTREAM_REVIEW.md` for the remaining gates.

Candidate experiments reuse the cached images:

```bash
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus reverse
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus clear-columns
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus hold
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus hold validate
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus guarded validate
bash scripts/fabric_guard_cost.sh build/fabric-reference-warp-reference.OBUfXfus
bash scripts/fabric_validator.sh build/fabric-reference-warp-reference.OBUfXfus
bash scripts/fabric_validated.sh build/fabric-reference-warp-reference.OBUfXfus
bash scripts/fabric_validator.sh build/fabric-reference-warp-reference.OBUfXfus byte
bash scripts/fabric_validated.sh build/fabric-reference-warp-reference.OBUfXfus byte
bash scripts/fabric_validated.sh build/fabric-reference-warp-reference.OBUfXfus byte word-only
bash scripts/fabric_handshake.sh build/fabric-reference-warp-reference.OBUfXfus
bash scripts/fabric_management_cost.sh build/fabric-reference-warp-reference.OBUfXfus
bash scripts/fabric_loader_cost.sh build/fabric-reference-warp-reference.OBUfXfus
bash scripts/fabric_loader_cost.sh build/fabric-reference-warp-reference.OBUfXfus word-only
```

`hold` adds a fixed external control through a hash-checked copy of the
reference hierarchy; it does not force internal nets or change the installed
FABulous package. `validate` adds full counter wraparound, interrupted-load
recovery after 33 and 199 frames, and a wrong-image control. Source patch,
hashes, runner and logs are retained. A production design still needs output
parking, reset/release sequencing, broader path coverage and physical cost.

`guarded` tests a fixed output-parking and reset sequencer around the copied
fabric. It still trusts `image_valid` and uses the two demos' reset pin ABI.
The cost runner maps the guard and original/held LUT primitives separately
to CMOS5L and runs functional gate-level controller/primitive checks. See
`docs/reports/ANISH_GUARDED_RELOAD.md` for measurements and exclusions.

The validator runner tests a separate synchronous validator/guard boundary
against exact-length canonical images and malformed transactions in RTL
and mapped CMOS5L simulation. It does not yet replace `ImageValid` in the
full-fabric wrapper. See `docs/reports/ANISH_IMAGE_VALIDATOR.md` for the
experimental format, 41-case evidence, area and remaining integration gate.

The separate validated-fabric runner connects this boundary to the real
loader with word pacing and coordinated reset, sends exactly 12,024 bytes,
and checks reload/rejection/recovery. It preserves the trusted wrapper as
a baseline. Its read-only word/frame witness is distinct from the pin-level
oracle. See `docs/reports/ANISH_VALIDATED_FABRIC.md` for scope and results.

Both validator runners accept `word` (default) or `byte` as the second
argument. Byte CRC exposes backpressure and checks the last CRC byte before
allowing commit. The matched isolated cost comparison and integration
evidence are in `docs/reports/ANISH_BYTE_CRC.md`; physical timing is open.

The handshake runner substitutes a small fixture for programmable logic but
uses the actual pinned loader and row registers. Both CRC modes check
continuous-valid backpressure, busy cancellation priorities and all frame
payloads. This is separate loader RTL evidence, not full-fabric acceptance;
see `docs/reports/ANISH_LOADER_HANDSHAKE.md`.

The management cost runner preserves the fabric as a synthesis black box,
maps both CRC modes including pacing/parking muxes, then checks each mapped
wrapper with the RTL loader fixture. See `ANISH_MANAGEMENT_COST.md` in
`docs/reports/` for the explicit area boundary and mixed GL/RTL limitations.

The loader cost runner includes the actual loader and 448 row-register bits
in mapping, with an opaque boundary beyond them. Both CRC modes run mapped
control-path checks using counter and LFSR image payloads. Hierarchical area
is counted once; see `docs/reports/ANISH_LOADER_COST.md` for the retained
serial-interface cost and other exclusions.

Optional `word-only` mode removes serial configuration frontends from that
bounded experiment while retaining the pinned FSM and all row registers.
Default `all-ports` mode is unchanged. Candidate cost and capability limits
are documented in `docs/reports/ANISH_WORD_ONLY_LOADER.md`.
The validated-fabric runner also accepts `word-only` as its third argument
to test this frontend with the actual held reference fabric. The report
records the nine-scenario byte-CRC integration run and its RTL-only scope.
