# Small fabric: cold-loaded user logic execution

On 2026-09-29, the cached 16-LUT grid ran its compiled two-bit counter
after loading the real 504-byte image through the public word port.
The same independent pin oracle passed with both LUT4AB tiles replaced
by their cached CMOS5L standard-cell netlist. This is mixed-level
simulation, not a complete gate-level chip or physical signoff.

## Evidence

| Icarus 13 run | Implementation | Result |
|---|---|---|
| `warp-small-cold.ResnzZRo` | All RTL | 1,074 pin checks; negative control detected |
| `warp-small-cold.8oi2sd91` | Both LUT tiles mapped; surrounding logic RTL | Same checks and negative control |

Tests cover synchronous reset, reset-over-enable priority, repeated
wraparound, disabled retention and 1,024 deterministic randomized cycles.
Only public ports are driven/read. The source counter is not instantiated
as the oracle, and no configuration state is forced or deposited.
Only the two enabled output pins are compared for data; all four external
output-enable bits must match. Data on input-only pins can be unknown.
The deliberately wrong expected counter value fails at check zero with
exit 1; a timeout is not accepted as a successful negative control.

The independent framing audit checks all 126 big-endian words: the five
header words, 40 ordered one-hot frame addresses (two columns, 20 frames),
two row-data words per address and the desynchronization footer. It does
not independently decode each LUT/routing configuration bit. Image SHA-256:
`e5c8fa594fe4bda05795adc31884d154e8b9e0f365ea7462f01433b77b8e6c36`.

Mapped reuse requires byte-identical copies of all six LUT-tile source
dependencies against `warp-tile-mapping.sOBN3KHk/base`. Both instantiated
tiles retain their dynamic configuration storage. The runner retains
the netlist, PDK models, hashes, simulator version, image audit and logs.
It reuses the generated fabric and mapped cells without new synthesis.

## Interface correction

The initial test `warp-small-cold.50s9yEGa` incorrectly expected `T_top`
to have the user's `io_oeb` polarity. The generated I/O primitive explicitly
assigns `T_top = ~T`: external T is active-high output enable. External
pin order matches the compiler wrapper; there is no pin permutation.
The correct enable pattern is `1100`, with reset/enable on pins 0/1 and
counter data on pins 2/3. No generated RTL or bitstream was changed.
Earlier June-suite Icarus 14 runs also passed, but the table above records
the final runner using the cached TT-compatible Icarus 13 toolchain.

## Reproduce

```bash
source .venv-fabric/bin/activate
bash scripts/fabric_small_cold.sh build/warp-small-compile.khvqjtBG
bash scripts/fabric_small_cold.sh build/warp-small-compile.khvqjtBG build/warp-tile-mapping.sOBN3KHk
```

The test sends one word every four management clocks. This is a functional
test cadence, not a maximum supported load rate or physical clock claim.
Icarus reports the PDK's unsupported edge-sensitive `ifnone` paths; no SDF
is applied and these runs establish no timing result.

## Remaining gates

This only tests cold loading of one counter. Safe reload, output parking,
second-design execution, small-grid validator/hold integration, fully
mapped loader/I/O, protocol capacity, physical fit, and equal-area CPU/PIO
comparisons remain open. The production top and GDS source list still use
the placeholder. No phase exit box is closed by this experiment.
