# Reference bitstreams and persistent reload validation

**Status: compilation and individual-image checks pass; persistent reload
fails to complete. Do not mark the reference reload gate passed.**

This status refers to the unmodified stock fabric. The later
[isolation experiment](ANISH_RELOAD_EXPERIMENTS.md) tests a separate source
copy with a fixed LUT/carry hold input; its passing cases do not change the
stock regression's result or establish a production solution.

Local run: 2026-09-25, `warp-reference.OBUfXfus`, based on `anish_branch`
`4dd023b` plus the uncommitted experiment sources. Reproduce with
`bash scripts/fabric_reference.sh` after activating the venv and supported
toolchain; see `experiments/fabric_reference/README.md`.

Raw compilation evidence is retained in ignored
`build/fabric-reference-warp-reference.OBUfXfus/`. It includes manifests,
both generated images and compile logs. This report is local evidence;
it is not a CI result or a physical-chip test.

September 26 cached-image recheck: `build/warp-recheck.EAQHpix8/` retains
the cold LFSR, negative control and byte-level reload trace. Snapshot and
probe evidence below isolate the failure without rerunning synthesis/P&R.

## Compiled designs

| Design | Reference logic cells | Image size | Final nextpnr Fmax |
|---|---:|---:|---:|
| 16-bit counter, synchronous reset before enable | 26 / 672 | 12,024 bytes | 28.33 MHz |
| 16-bit LFSR, seed ACE1, taps 15/13/12/10 | 19 / 672 | 12,024 bytes | 63.69 MHz |

Fmax is the last post-route number from the generic FABulous demonstration
model. Neither value is a CMOS5L prediction or a 50 MHz chip result.
Both images use the same generated fabric and wrapper. The earlier local
September-toolchain run with replacement maps is superseded.

SHA-256:

```text
counter 3788d987158d0e81683cbf1378c0749d57c4f0c265d797483f50d6f004fc5874
lfsr    774c910855a69986347d34072b557dac900bb2dd5556e9f365776ea5f3cec8fd
```

## Checks

- Both supported-toolchain compilations and bitstream generations pass.
- Configuration mapping audit passes: 616 mapped bits, 24 padding bits,
  20 frames of 32 bits per reference LUT4AB tile. This checks index coverage
  and uniqueness; it does not prove physical bit-to-mux correspondence.
- Seven `tools/fabric_audit` unit tests pass; shell syntax check passes.
- Seven frame-decoder/header-validation tests also pass (14 combined).
  These check mapping/format handling, not reload acceptance.
- Counter: 65,673 independently checked cycles pass, including wraparound
  and reset/enable combinations. Retained run `warp-recheck.bM6h67mg`,
  `cold-counter.log`, exit 0. This supersedes the initial temporary
  `progress.log`, which was not retained.
- LFSR from startup: 1,157 checked cycles pass (`cold-lfsr.log`).
- Wrong image: loading the LFSR where the counter is expected fails at the
  first reset check: actual ACE1 versus expected 0000, with enable low
  (`negative.log`, exit 1). This is the intended functional failure.
- Shortened counter-then-LFSR diagnostic (`+quick`, `reload-quick.log`):
  progress stops during the second load at byte 1996 (exit 124 after 90 s).
  This is the last word of column 1, frame 12 (zero-based). The preceding
  counter checks pass. Thus the stall does not require the long sequence.

The diagnostic testbench adds progress messages to the same behavioral
checks and uses cached images from the original compile. The final runner
performs cold-LFSR and negative checks before the full reload, and imposes
a 300-second limit on the latter. It exits with failure unless the complete
A/B/A marker is present. Progress alone is never treated as a pass.

## Reload finding: an intermediate feedback path

Resetting the public configuration loader does not erase the distributed
configuration latches. The second upload therefore transitions through
mixtures of old and new routing/logic bits. We now have both static and live
evidence of a feedback loop during that transition.

`frame_snapshot.py` decodes the pinned reference format with strict length,
sync, frame-address and desync checks. Binary row/bit ordering matches all
140 macros in the independently tool-generated LFSR emulation header. Static
snapshots use the existing generated `EMULATION` interface and Yosys
`proc; flatten; opt; scc`; these are white-box diagnostics, not loader passes.

| Snapshot | SCCs | Retained directory under `build/` |
|---|---:|---|
| Complete counter (0 new frames) | 8 | `warp-snapshot.ZCDlGHBf` |
| After column 1/frame 11 (32 new frames) | 10 | `warp-snapshot.KSHtvWBj` |
| After column 1/frame 12 (33 new frames) | 12 | `warp-snapshot.P6SxowIg` |
| Complete LFSR (200 new frames) | 8 | `warp-snapshot.15ke3eDO` |

Eight DSP SCCs are common to both working endpoints; they must not be
mistaken for newly introduced failures. Frame 11 introduces two LUT SCCs
at X1Y13. Frame 12 additionally introduces LUT SCCs at X1Y8/LC and X1Y10/LB.

At X1Y8/LC, the reduced first LUT mux has `S == Y`, `B == 0`, and variable
input `A`: `Y = Y ? 0 : A`. With A=1 this is inversion around a feedback
loop. `reload_probe.v` observes that exact mux in the live, publicly loaded
DUT without forcing any state. Run `warp-recheck.GJ42Zo6F/probe.log` records
64 output transitions at the same simulation timestamp, 23,293,500 ns,
with A=1 and B=0. The probe emits a fatal diagnostic; the surrounding run
still reaches the wall timeout (exit 124) while the event queue is active.
This establishes zero-time oscillation in this RTL model. It does not
measure silicon oscillation frequency, current, or physical reliability.

The public-port acceptance test remains unchanged by the diagnostic:
`scripts/fabric_recheck.sh INPUT` fails unless A/B/A actually completes.
Its `probe` mode intentionally fails and its `counter` mode checks the full
counter sequence alone. See [the repair plan](ANISH_RELOAD_PLAN.md) for
isolation, load-order and interrupted-load experiments. No repair is claimed.

This is new evidence beyond two fresh simulations with different images.
Do not bypass this regression to claim the chip is safely reprogrammable.

The acceptance testbench uses only public reference-fabric ports and an arithmetic
oracle. It checks every output bit using case inequality, so unknowns fail.
Reset while disabled, reset while enabled, hold, wraparound and pseudorandom
enable sequences are included. Loader reset precedes each upload; user
reset comes through an input pin. Output-enable configuration stays the same
across these two images. No internal state is forced or deposited.

The experiment does not cover interrupted loads, corrupt images, arbitrary
partial reconfiguration, safe output parking, asynchronous pin behavior,
gate-level timing or complete protocol workloads. Phase 0 as a whole remains
open, including organizer and physical-integration gates.
