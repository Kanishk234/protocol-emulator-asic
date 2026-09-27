# Validated full-fabric loading — 2026-09-27

This experiment connects the image validator to the pinned reference
fabric using the existing LUT/carry hold patch. It preserves the separate
stock, hold-only and trusted-validity test modes. It changes no production
fabric definition or installed FABulous files.

## Interface and sequencing

`reference_validated_top.v` combines the D4 validator/guard with fixed pad
parking and the two demo designs' reset input (bit 0; enable on bit 1).
The host supplies the experimental architecture ID, version, byte length
and CRC when beginning a transaction. There is no host-controlled
`ImageValid` override in this wrapper.

The host holds data/valid until `WordReady`; a valid/ready edge consumes
exactly one word. The validator sees every accepted word during LOAD.
The fabric sees the same accepted words until completion or an error.
An extra word after completion still reaches the validator, invalidating
the transaction, but cannot reconfigure the fabric. Serial/bitbang inputs
are tied inactive inside the wrapper.

The pinned `ConfigFSM.v` raises `frame_strobe` after the last row word,
then raises `long_frame_strobe` on the following edge for two cycles.
Configuration latches use that stretched pulse. Replacing the frame address
too early could select the wrong frame while the old pulse remains active.
The wrapper therefore enforces three idle edges after each forwarded word:
maximum acceptance rate is one word per four clock cycles. This conservative
rule also applies to headers and ordinary row words; optimizing it would
need another loader-specific validation.

Commit is blocked while a word request is asserted or that cooldown is
active. The existing guard then settles the configuration, releases the
internal LUT hold while user reset remains asserted, and releases parked
pads only after the reset interval. The validated test mode removes the
old testbench's 100-cycle post-upload delay so the wrapper must provide
the required settling itself.

Begin/ARM resets the loader and starts validator accounting together.
Abort or external loader reset cancels the transaction and clears validity;
begin is needed before writing again. Control reset resets both management
and loader. These management inputs and word requests are synchronous to
the experiment clock; host CDC and glitch-free physical reset/parking
remain outside this result.

Each canonical upload is 12,024 bytes (3,006 words). Hex files remain padded
for the testbench memory, but normal validated transactions transmit only
the binary length. A deliberate extra-padding test transmits one extra
word and must remain parked.

## Evidence and limits

Retained run: `build/warp-validated.soYb2Cvu/`, Icarus 14-devel from the
supported June 29 OSS CAD Suite. All nine scenarios meet their expected
exit code and result marker; one fabric executable is reused throughout.

| Scenario | Verified result |
|---|---|
| Counter/LFSR/counter, full wraparound | 67,987 independent functional checks; 45,186 parked samples; exit 0 |
| LFSR/counter/LFSR, fastest permitted words | 2,479 checks; 36,165 parked samples; exit 0 |
| Interrupted after 33 frames, abort, restore | 1,322 checks; exit 0 |
| Interrupted after 199 frames, abort, restore | 1,322 checks; exit 0 |
| Payload corruption, failed commit, restart | Held/parked with CRC error after 3,006 words/200 frames; 1,322 recovery checks |
| Duplicate frame with recomputed CRC | Held/parked; forwarding stops after 21 words/one frame; 1,322 recovery checks |
| Extra padding word | 3,007 accepted, 3,006 forwarded; held/parked with error; 1,322 recovery checks |
| Loader reset after complete valid upload | Validity cleared; commit rejected; 1,322 recovery checks |
| Valid image implementing the wrong circuit | Format/CRC accepted; functional mismatch on first release; expected exit 1 |

Each accepted complete image passes the 3,006-word/200-frame diagnostic.
Rejection recovery uses a new begin without requiring a prior abort, so
sticky errors must be cleared by restart. The interrupted-frame cases
separately exercise explicit abort. Corruption/duplicate/padding cases
attempt commit for twelve clocks and require hold, parking and invalidity.
These are selected cases, not exhaustive frame-boundary fault coverage.

Twenty existing Python regression tests, runner shell syntax and legacy
TB conditional syntax checks pass. The latter ignores unresolved DUT
modules and is not a rerun of the old full-fabric baselines. No P&R or
isolated-cell gate-level rebuild was repeated for this milestone.

The existing independent counter/LFSR pin-level oracle checks functional
behavior and the first visible reset state. Parked output samples check
data zero and all tristates disabled during loading/recovery.

A separate read-only integration witness compares the actual loader mux
strobe/data with the wrapper's forwarded stream. For each accepted full
image it requires 3,006 accepted and forwarded words, plus exactly 200
rising frame-write pulses. This witness is diagnostic instrumentation,
not a replacement for public-pin functional checks; no internal state is
forced or deposited.

Corrupt payload uses the original image CRC. The duplicate-frame image
uses a recomputed CRC, so frame structure must independently reject it.
Padding exercises post-completion invalidation. The wrong-function image
uses its *correct* metadata and CRC: it should pass validation and then
fail the independent functional oracle.

This is full-fabric RTL simulation of two compiled designs, not full-fabric
gate-level validation or a proof that arbitrary payloads cannot oscillate.
Only the isolated validator/guard and held LUT have prior functional
CMOS5L gate-level evidence. The new pacing/parking wrapper has not been
mapped or timed. The previous 14,123.7054 µm² figure covers validator plus
guard, excluding this additional wrapper and all physical overhead.

## Reproduction and next work

Follow-up: [byte CRC comparison](ANISH_BYTE_CRC.md) uses the existing
four-clock word budget to reduce isolated management area. The word-wide
wrapper remains the default; the new report records its separate tests.

Activate the project `.venv-fabric` and prepend the supported June 29 OSS
CAD toolchain, then run:

```bash
bash scripts/fabric_validated.sh build/fabric-reference-warp-reference.OBUfXfus
```

The runner snapshots source files, generates CRC/mutation manifests from
cached binaries, hash-checks the fabric patch, compiles once and reuses the
simulation executable for every case. Sources, hashes, image manifest,
tool version, case logs and exit codes are retained under ignored
`build/warp-validated.*/`.

Next compare a byte/bit-serial CRC at the required host throughput, measure
the complete management wrapper, and exercise stall/commit/reset edge
cases in a small loader-focused regression. Broader routing/DSP/RAM
isolation and physical control distribution remain unresolved. No phase
exit gate, production ABI or architecture freeze follows from this test.
