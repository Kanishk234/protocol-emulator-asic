# Management wrapper mapped cost — 2026-09-27

The existing reference wrapper, including validator, guard, word pacing,
pad parking and demo user-reset muxes, maps to **13,869.1224 µm² with byte
CRC**, versus **14,773.3740 µm² with word CRC**. Saving: 904.2516 µm²
(6.12%). This is wrapper standard-cell area, not the complete chip or host.

Retained run: `build/warp-management.xWb9WYPm/`.

| CRC mode | Mapped standard cells | Liberty area (µm²) |
|---|---:|---:|
| Word-wide | 981 | 14,773.3740 |
| Byte-at-a-time | 886 | 13,869.1224 |

Both use Yosys 0.66+179 and pinned IHP PDK
`2bbec755dc67ca3db0261c3d6163e15735d66710`, CMOS5L typical 1.20 V/25 C.
The boundary is the actual `reference_validated_top`, retaining its
existing status/control ports. Word mode remains the default.

## Keeping the measurement honest

Synthesis reads `loader_fixture.v` with `read_verilog -lib`, discarding its
entire implementation. Thus `eFPGA_top` is an opaque module: its output
values are unavailable to optimization. The constant outputs used by the
simulation fixture cannot eliminate the pad muxes in the area measurement.

The runner verifies the saved netlist has exactly one empty black-box
`eFPGA_top` definition and one instance. All other physical cells must be
CMOS5L cells; only Yosys scope metadata is excluded alongside that black box.
Strict pre/post-mapping checks report zero problems.

Excluded: the programmable fabric, configuration storage **and the actual
configuration loader/row registers inside eFPGA_top**, a future host/CDC
interface, placement, wires, clock/control buffering and physical timing.
This does not measure the entire management system needed for tapeout.

## Functional validation

Each mapped wrapper passes the same 12,129-step handshake test with
15 busy cancellation/priority cases, 3,006 continuously requested words
and exact payload checks at 200 frame writes.

This simulation mixes the **mapped management wrapper** with the **RTL
loader fixture**. Standard-cell/UDP models use Tiny Tapeout Icarus 13.
It is neither an all-gate-level loader test nor a full-fabric GL test.
The fixture's constant user outputs check parking/release; actual user
counter/LFSR execution remains covered by earlier full-fabric RTL runs.
Unsupported edge-sensitive `ifnone` timing-model warnings remain in the
compile logs. No SDF, frequency or physical glitch-safety claim follows.

## Reproduction and next gates

Follow-up: the [loader-inclusive experiment](ANISH_LOADER_COST.md) maps and
tests the loader and row registers too. Its larger cost boundary and
retained serial logic must not be confused with the wrapper-only figures.

With the project venv and supported tool PATH active:

```bash
bash scripts/fabric_management_cost.sh build/fabric-reference-warp-reference.OBUfXfus
```

The runner uses cached images, PDK and simulator; retains source/hash
snapshots, versions, mapped netlists, statistics and both functional logs.
No production architecture or phase gate changes.

Next include the configuration loader in an explicitly bounded cost/test
target, then address broader routing/DSP/RAM isolation and physical control
distribution. A future host interface is still unspecified and cannot yet
be included in a complete-shell claim.
