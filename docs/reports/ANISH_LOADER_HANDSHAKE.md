# Loader handshake regression — 2026-09-27

Both word-wide and byte-at-a-time CRC modes pass a small regression using
the **actual pinned FABulous loader**, without rebuilding the programmable
fabric. Retained run: `build/warp-handshake.rw1QbkFj/`.

Each mode passes 12,129 test steps, 15 busy-window cancellation cases,
3,006 continuously requested words, and exact payload checks for all
200 frame writes. Earlier byte-only run `warp-handshake.X4N5oQLx` also
passed; the two-mode run is the current reproduction target.

## What is checked

For each of three busy positions after an accepted word, the test asserts
write and commit together with one of five control combinations:

- Begin alone.
- Begin plus abort.
- Begin plus external loader reset.
- Begin plus control reset.
- Begin, abort and control reset together.

Begin discards old progress and starts a fresh transaction; cancellation
and reset win over begin when asserted together. No coincident word can
be forwarded, stale completion/validity is cleared, and outputs stay
parked. In byte mode these cases interrupt pending CRC bytes; in word
mode they interrupt the loader pacing interval.

A following full canonical counter image is sent with valid continuously
asserted, changing data only after acceptance. The test checks:

- No word is lost, duplicated or forwarded while stalled.
- Accepted writes are at least four clocks apart.
- No new write overlaps an active frame-write pulse.
- Every frame address and every one of its fourteen captured row words
  matches the input image, with exactly 200 frame pulses.
- Commit during final CRC/pacing work cannot release the outputs early.
- After valid release, a coincident begin/write/commit discards validity
  and parks outputs again.

The fixture uses unmodified `eFPGA_Config`, `ConfigFSM`, UART/bitbang
configuration modules and `Frame_Data_Reg` from the retained reference.
Its replacement `eFPGA_top` has constant user outputs to exercise the
wrapper's park/release muxes. No programmable logic fabric is present.
The frame checks are read-only internal diagnostics; no state is forced.

Consequently, this is **loader/control RTL evidence**, not another user
circuit execution test, full-fabric GL test, exhaustive control proof or
physical timing result. Frame-row comparisons occur at sampled rising
frame strobes, not continuously throughout the pulse or under wire delay.
The earlier full-fabric counter/LFSR acceptance suite remains separate.

## Reproduction and next step

With the project venv and supported June 29 OSS CAD tools active:

```bash
bash scripts/fabric_handshake.sh build/fabric-reference-warp-reference.OBUfXfus
```

The runner generates word data and a zlib checksum from the cached counter
binary. It retains loader/management/test sources, hashes, simulator
version and both logs. No new P&R or large-fabric compile is needed.

Next measure the full management/pacing/parking wrapper without allowing
constant fixture outputs to optimize away real hardware. Physical
validation and broader routing/DSP/RAM isolation remain open. No phase
gate or production architecture decision changes.
