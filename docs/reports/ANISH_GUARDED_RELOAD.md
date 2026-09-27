# Guarded reload and isolated CMOS5L cost — 2026-09-26

**The experimental wrapper parks outputs, resets user state before pad
release, and passes the full reload/recovery suite. The guard and isolated
LUT also pass functional tests on mapped CMOS5L netlists.**

This is a reference experiment under ANISH-D2/D3, not the production chip
shell. The stock loader regression remains unchanged. The bitstreams are
the same counter/LFSR images identified in `ANISH_REFERENCE.md`.

## Control sequence

`wp_reload_guard.v` accepts synchronous begin, abort and commit requests.
Its active-low reset is synchronous. A begin request parks the outputs,
asserts fabric hold and provides an arm interval before enabling word
writes. Writes are disabled outside the loading state, and the reference
loader is held reset outside that state. Serial configuration is disabled
in this experiment so it cannot bypass the word-loader permission.

Commit is accepted only while loading, with `image_valid` high and the write
strobe low. Two settling states follow. Internal hold then releases while
the pads remain parked and the demo reset input stays asserted. Five user
clock edges are available before pad release. This distinction matters:
reset carried through programmable LUTs cannot propagate while those LUT
outputs are held at zero. Internal hold release and external pin release
are separate events.

`reference_guarded_top.v` implements the actual output muxes: data is zero
and every active-high tristate control is one while parked. During reset,
the two demo input pins are reset=1 and enable=0. That is a demo-specific
reset interface; a production user-reset ABI is still required. Abort has
priority over begin/commit and returns to the parked state.

`image_valid` is a trusted test input, **not an implemented checksum or
completeness validator**. A host that falsely asserts it can still release
an incomplete/bad configuration. The next shell experiment must generate
this condition from accepted length, architecture/version, frame structure
and checksum, and clear it on restart or abort.

## Evidence

Retained full-fabric run: `build/warp-order.v5IBJS6u/`.

| Check | Result |
|---|---|
| Full counter/LFSR/counter, including wraparound | 67,987 checked cycles, exit 0 |
| Counter recovery after 33 interrupted LFSR frames | 1,322 checked cycles, exit 0 |
| Counter recovery after 199 interrupted LFSR frames | 1,322 checked cycles, exit 0 |
| Invalid commit before abort/recovery | Remains held/parked; loader disabled after abort |
| Wrong image | Functional mismatch at first guarded release, expected exit 1 |
| Controller unit sequence | 120 steps; invalid, busy and out-of-transaction commits; abort throughout release; reset priority |
| LUT/carry hold primitive | 256 vectors and unknown-input/configuration hold |

The full run checks 61,848 parked clock samples and tests the expected
reset value immediately on release, before the normal exercise routine
resets the design again. These are settled RTL samples, not a guarantee
against subcycle glitches or propagation skew in silicon. Guarded B/A/B
has not been rerun; both directions passed the earlier hold-only candidate.

## Isolated mapping results

Retained successful run: `build/warp-guard-cost.3TVEQJRI/`.
Yosys 0.66+179 (`e74db6dea`), IHP-Open-PDK
`2bbec755dc67ca3db0261c3d6163e15735d66710`, CMOS5L typical 1.20 V/25 C
Liberty. Sources, library/model hashes, netlists, statistics and logs are
retained. Configuration inputs remain variable; configuration storage is
outside this isolated cell measurement.

| Module | Mapped standard cells | Sum of Liberty cell area (µm²) |
|---|---:|---:|
| Reload guard | 30 | 665.8848 |
| Original LUT/FF/carry primitive | 17 | 344.7360 |
| Same primitive with hold clamps | 19 | 353.8080 |
| Increment per isolated primitive | 2 | 9.0720 |

The controller maps to ten flops plus logic (the synthesis FSM encoding is
not the source register width). Yosys `$scopeinfo` metadata is excluded from
the physical cell count; all remaining cell types must be CMOS5L cells.
These sums exclude placement, wires, clock/control buffers, hold-net fanout,
configuration storage, output parking muxes and a real validator/host.
They cannot establish full-chip fit or frequency.

The 120-step controller test and 256-vector primitive test pass again on
their mapped netlists with Tiny Tapeout Icarus 13 and the pinned standard
cell/UDP models. Icarus reports unsupported edge-sensitive `ifnone` timing
paths, retained in the compile logs. These are functional gate-level checks
without SDF, not timing signoff or full-fabric gate-level reload.

Reproduce from an activated project venv and the supported tool PATH:

```bash
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus guarded validate
bash scripts/fabric_guard_cost.sh build/fabric-reference-warp-reference.OBUfXfus
```

The cost runner downloads only the pinned public library/model files and
Tiny Tapeout simulator package into a local cache if missing.

## Next work

Follow-up: the isolated validator/guard now passes 41 cases in RTL and GL;
see [image validator results](ANISH_IMAGE_VALIDATOR.md). A separate
[validated full-fabric wrapper](ANISH_VALIDATED_FABRIC.md) passes nine RTL
reload/rejection scenarios. The historical wrapper here keeps its trusted
input as a baseline.

Next compare serial checksum cost and extend the integrated wrapper's
handshake/reset and mapped/physical validation. Preserve the existing
wrong-image semantic control.

Then expand isolation to routing-only/DSP/RAM paths and inspect physical
control skew and output mux hazards. Integrate accepted changes into the
fabric definition/generator before claiming a production repair. No phase
gate or architecture freeze is declared by these results.
