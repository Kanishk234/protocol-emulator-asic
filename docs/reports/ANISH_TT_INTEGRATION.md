# TT top integration checkpoint — 2026-09-29

The configured chip source now instantiates the 16-LUT reference-derived
fabric instead of the placeholder adder. Source lists match in info.yaml
and test/Makefile. No src/config.json or template workflow job was changed.
ANISH-D11 and the architecture document specify the experimental synchronous
byte host, FSB1 geometry, checksum, pad parking and counter reset ABI.

The exact TT top passes the shared cocotb test using cached Icarus 13:
`build/small-tt-rtl.log`, `build/small-top-results.xml`, 4,692 simulated clocks.
The test loads the real image over pins, checks 256 counter cycles across
initial load and recovery, rejects incomplete and incorrect-checksum images,
checks output parking and deselection. No internal force/deposit is used.
Run `python scripts/test_small_top.py` in .venv-fabric to reproduce locally.
The Makefile runs the same test on CI RTL and the physical-flow netlist.

Local hierarchy/proc `check -assert` reports zero connectivity problems.
This is not a flattened feedback proof. Strict Verilator lint fails on
generated-source warnings including combinational feedback; the first run
reported 168 warnings including trailing-newline diagnostics subsequently
normalized by the generator. Diagnostics are in `build/small-top-lint.log`.
No blanket warning suppression, STA disabling or physical exceptions added.
GDS may fail at lint/synthesis; a functional simulation pass does not make
these physical blockers disappear. The CI run is a diagnostic integration
attempt, not a signoff claim. Final GDS/precheck/GL outcomes remain pending.

The local machine lacks make and its default venv lacks cocotb. Using the
FABulous venv and cocotb runner avoids installation; cached TT Icarus avoids
the June OSS suite's incompatible runtime-library combination with Python.
The runner explicitly checks the results XML so a missing test cannot pass.

Next: inspect the actual chip-flow failure or completion, repair generated
lint issues through the generator, and resolve configuration-aware feedback
and physical timing before expanding protocol workloads. Cold/recovery tests
cover only this counter, not arbitrary images or a second compiled circuit.
