# Byte-at-a-time CRC comparison — 2026-09-27

The experimental byte CRC reduces the mapped validator-plus-guard area
by **828.009 µm² (5.88%)** against the current word-wide implementation,
using identical sources, image cases, synthesis settings and CMOS5L library.
This is a modest isolated-block saving, not a full-chip area or timing win.

## Implementation and interface

`SERIAL_CRC=0` remains the default word-wide baseline.
`SERIAL_CRC=1` processes the high byte on the word-accept edge, retains the
remaining 24 bits, then processes one byte on each of the next three
clocks. Both implement the same CRC and pinned canonical image contract.

The validator exposes `word_ready` for CRC availability. The isolated
management interface also requires LOAD permission; the full reference
wrapper combines CRC availability with LOAD and its existing pacing/reset
conditions to produce the host-facing `WordReady`. Valid/data must remain
stable until accepted. Neither interface handles an asynchronous host.

In byte mode, `complete` means the final word has been received; its CRC
may still be busy. `image_valid` stays low until the last byte has been
checked. The guard uses that validity signal, never completion alone.
A final-word or busy-window commit therefore cannot release unchecked
data. Begin, abort and reset clear pending CRC bytes and progress.
The same held word cannot be forwarded again while CRC is busy.

The byte engine accepts one word every four clocks. The D5 loader already
enforces that interval to drain frame-write strobes, so this implementation
adds no required inter-word delay to that wrapper. This is a cycle-count
comparison, not a measured physical maximum clock or finalized host-rate
requirement. A future faster loader might favor the word-wide engine.

The 24-bit holding register and byte-control logic consume some of the XOR
logic savings. A bit-serial engine would need a separate throughput/cost
comparison; no claim is made that byte serialization is globally optimal.

## Matched isolated measurements

Pinned IHP PDK `2bbec755dc67ca3db0261c3d6163e15735d66710`,
CMOS5L typical 1.20 V / 25 C Liberty; Yosys 0.66+179.
Both configurations use the updated source and ready/busy-aware testbench.

| Variant | Evidence run | Mapped cells | Liberty area (µm²) | RTL / GL checks |
|---|---|---:|---:|---|
| Word-wide | `warp-validator.YLYLyxNZ` | 905 | 14,078.3832 | 41 cases / 116,831 steps each |
| Byte-at-a-time | `warp-validator.Yc1dlz11` | 828 | 13,250.3742 | 41 cases / 296,422 steps each |

The earlier historical word result (14,123.7054 µm²) used an older source
interface. It remains valid for that snapshot but is not the denominator
for this matched comparison. Netlist structure and mapping can change with
source/interface changes even when the default functional behavior agrees.

Both runs pass Verilog-2005 parsing and strict Yosys pre/post-mapping checks.
Functional GL uses Tiny Tapeout Icarus 13 and pinned standard-cell/UDP
models. Retained model warnings about unsupported edge-sensitive `ifnone`
paths are unchanged; no SDF or timing signoff is implied.

The 41-case suite retains independent zlib CRC expectations and all earlier
metadata, length, structural, corruption and recovery controls. The updated
testbench holds valid/data through CRC stalls, checks no write is forwarded
while busy, attempts commit during final-checksum work, and cancels pending
CRC work with reset/abort. The word-wide mode passes the same harness with
no CRC stalls. Random payloads only test the validator, not live fabric safety.

Area excludes fabric, configuration storage, host circuitry, pacing/output
parking wrapper, physical placement, buffers and wires. Equal total-chip
area comparisons and full management-wrapper cost remain future work.

## Full-fabric check

Retained run: `build/warp-validated.VxA9xvJv/`. All nine scenarios meet
their expected result markers and exit codes:

- Full counter/LFSR/counter: 67,987 independent functional checks,
  45,186 parked samples. Reverse LFSR/counter/LFSR: 2,479 checks,
  36,165 parked samples at the fastest permitted word rate.
- Interrupted uploads at frames 33/199, corrupted payload, duplicate frame
  with recomputed CRC, extra padding and loader reset each recover with
  1,322 functional checks. Rejected images cannot release the hold/parking.
- A correctly checksummed wrong-function image passes validation and fails
  the independent semantic oracle at first release (expected exit 1).
- Each accepted complete image has 3,006 accepted/forwarded words and 200
  frame-write pulses in the separate read-only loader witness.

Comparison with `warp-validated.soYb2Cvu` finds identical logged upload
times, word/frame/parked counts and positive result lines for all nine
scenarios; `timing-comparison.json` retains this post-run comparison.
The runner separately verifies the negative semantic failure. This is
unchanged *simulated cycle timing* at the test clock, not physical Fmax.

The TB requests commit while final CRC/pacing may still be busy, waits for
the public ready indication before checking validity, and leaves release
to the hardware. No 100-cycle post-upload delay is restored. Full-fabric
validation is RTL only; the new byte management block's isolated GL test
does not establish full-fabric GL behavior.

Twenty existing Python regressions and both runner syntax checks pass.
Legacy TB conditional syntax also passes with unresolved DUT modules
ignored; that limited check is not a repeat of the historical baselines.

## Reproduction

With the project venv and supported June 29 tool PATH active:

```bash
bash scripts/fabric_validator.sh build/fabric-reference-warp-reference.OBUfXfus word
bash scripts/fabric_validator.sh build/fabric-reference-warp-reference.OBUfXfus byte
bash scripts/fabric_validated.sh build/fabric-reference-warp-reference.OBUfXfus byte
```

Runners retain variant names, source/hash snapshots, versions, manifests,
netlists and logs under ignored build directories. They reuse cached images,
libraries and simulators.

## Next gates

The later [management-wrapper measurement](ANISH_MANAGEMENT_COST.md)
includes pacing/parking/reset muxes and tests mapped wrappers with the RTL
loader fixture. It still excludes that loader from the measured area.

Follow-up: the [loader handshake regression](ANISH_LOADER_HANDSHAKE.md)
now covers held-valid words, begin/reset/abort during busy work and exact
frame payloads for both CRC modes. It uses the actual loader with a small
nonprogrammable fixture; full management cost is still unmeasured.

Measure the complete management wrapper and add a small loader-focused
test for held-valid requests, begin during CRC work, coincident
commit/reset/abort and frame-write draining. Extend isolation beyond the
current LUT/carry paths, then validate physical timing/control distribution.
Keep the baseline available until the candidate passes those checks; no
production architecture decision or phase gate is closed.
