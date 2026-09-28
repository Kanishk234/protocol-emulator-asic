# Word-only loader candidate — 2026-09-28

Removing unused UART/bitbang configuration frontends reduces the measured
byte-CRC management-plus-loader boundary from **68,536.6542 to
47,208.5334 µm² (31.12%)**, with all 448 row-register bits retained.

This is an experimental configuration-port change, not a reduction in
programmable protocol resources or a full-chip area claim.

## Change and cost boundary

The `WORD_ONLY_LOADER` fixture option connects the management word port
directly to the **unchanged pinned ConfigFSM** and existing row registers.
It omits serial receiver modules and their arbitration muxes, ties
`fsm_reset` inactive, and fixes serial status outputs `ComActive` and
`ReceiveLED` low. The management wrapper already disables those serial
inputs; a future design requiring serial bypass/recovery would need to
retain or replace that capability.

Default `all-ports` mode is preserved. Installed upstream files, the
production fabric generator and chip RTL are unchanged. No host/CDC
implementation or permanent tapeout pin contract is selected.

| Mode | CRC | Mapped cells | Direct Liberty area (µm²) |
|---|---|---:|---:|
| All frontends, cached baseline | Word | 3,591 | 69,542.6256 |
| All frontends, cached baseline | Byte | 3,492 | 68,536.6542 |
| Word-only candidate | Word | 2,018 | 48,188.7630 |
| Word-only candidate | Byte | 1,921 | 47,208.5334 |

Baseline: `warp-loader-cost.AXvDP6i0`. Candidate:
`warp-loader-cost.t41jdJxH`. Same reference dimensions, pinned FSM/row
registers, synthesis flow, hierarchy boundary and CMOS5L typical library.
The baseline is reused from retained evidence; the added conditional
candidate does not alter the default fixture behavior.

In byte mode, the direct loader/row-bank area is 33,330.4524 µm² and the
wrapper is 13,878.0810 µm². The bank is still 14 rows × 32 bits, with every
bit observable at the opaque boundary. Hierarchical totals are independently
checked against direct cell-count × library-area sums.

The cost still excludes fabric/configuration latches, column frame-select
decoders, RAM/DSP, future host circuitry and physical buffers/routing.
The reference dimensions are not the final chip dimensions. There is no
placement, frequency, physical-fit or full-chip saving claim.

## Validation

Both word-CRC and byte-CRC candidates pass mapped control-path tests with
counter and LFSR image payloads: **four runs of 12,129 steps each**. Each
checks 15 busy cancellation/priority cases, 3,006 words and the exact address
and row payloads of 200 frame writes. Strict synthesis and the area/boundary
integrity checks pass.

The real control path is mapped, but user outputs come from a behavioral
fabric-side stand-in. The test does not execute either programmable circuit,
establish full-fabric reload safety or provide SDF/timing signoff. The
previous cell-model `ifnone` warnings remain applicable.

Default all-frontend RTL regression `warp-handshake.MtxHcGZ2` also passes
both CRC modes (12,129 steps each). Shell syntax and whitespace checks pass.

## Live reference fabric follow-up

Run `warp-validated.FtTE9K1D` connects the word-only path to the actual
672-cell reference fabric with the existing LUT/carry hold patch and
byte-CRC management. All nine reload/rejection scenarios meet their
expected results. This is separate full-fabric RTL evidence, beyond the
mapped control-path stand-in used for the cost comparison above.

| Scenario | Result |
|---|---|
| Counter/LFSR/counter, full wraparound | 67,987 functional checks; 45,186 parked samples |
| LFSR/counter/LFSR, fastest permitted words | 2,479 functional checks; 36,165 parked samples |
| Interrupt after 33 frames, abort, restore | 1,322 recovery checks |
| Interrupt after 199 frames, abort, restore | 1,322 recovery checks |
| Corrupted payload | CRC error; 1,322 recovery checks |
| Duplicate frame with recomputed CRC | Forwarding stops at 21 words/one frame; 1,322 recovery checks |
| Extra padding | 3,007 accepted / 3,006 forwarded; rejected; 1,322 recovery checks |
| Loader reset after a valid upload | Validity cleared, commit rejected; 1,322 recovery checks |
| Correctly encoded image for the wrong circuit | Expected exit 1 at first visible output; oracle catches the mismatch |

All accepted complete images have 3,006 accepted/forwarded words and 200
frame pulses. `baseline-comparison.json` records that the selected load
timestamps, functional check cycles, word/frame/parking counts and exit
codes match the cached all-frontend byte-CRC run `warp-validated.VxA9xvJv`
in every scenario. This comparison is about simulation behavior, not
physical timing or frequency.

The optional `--word-only-loader` transform in
`patches/reference_reload_hold.py` replaces only the top-level frontend
instance with the pinned ConfigFSM and direct word connections. Real row
registers, column selectors, configuration latches and user fabric remain.
The four existing input hashes and an additional ConfigFSM hash are checked
before copying; unknown FSM contents are rejected before creating output.
`patch-checks.json` records that default transformations still match the
cached baseline and only `eFPGA_top.v` differs between the two candidates.
The runner retains all generated Verilog hashes and the transformer snapshot.

One newly compiled executable was reused for all nine scenarios. The cached
counter/LFSR binaries were reused without synthesis or place-and-route.
The unchanged pin-level oracle and read-only loader witness drive no
internal fabric state. Default all-frontend mode remains available.

This follow-up tests byte CRC only; the earlier mapped fixture tests cover
both CRC modes. It is not full-fabric gate-level validation, arbitrary-image
isolation, a production host contract or physical signoff. In particular,
routing-only/DSP/RAM feedback and physical control distribution remain open.

## Reproduction and next gate

With the project venv and supported tools active:

```bash
bash scripts/fabric_loader_cost.sh build/fabric-reference-warp-reference.OBUfXfus word-only
# Existing default/reference mode:
bash scripts/fabric_loader_cost.sh build/fabric-reference-warp-reference.OBUfXfus all-ports
# Live fabric with byte CRC and the word-only loader:
bash scripts/fabric_validated.sh build/fabric-reference-warp-reference.OBUfXfus byte word-only
```

Next review the transferable CMOS5L physical-flow evidence on fetched main
and choose a bounded tiny-fabric integration experiment, preserving the
sealed held-out set. Physical implementation, broader isolation coverage
and the final host contract must precede production adoption. No phase
exit box is changed by these reference experiments.
