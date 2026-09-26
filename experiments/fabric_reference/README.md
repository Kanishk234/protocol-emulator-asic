# Persistent reference reconfiguration experiment

Current result: each image works from startup, but counter-to-LFSR reload
stalls during configuration. A frame snapshot and read-only live probe
demonstrate intermediate LUT feedback at column 1/frame 12.
The runner intentionally fails this gate;
see `docs/reports/ANISH_REFERENCE.md`. A wall timeout is a failure, never
an expected-pass condition.

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
