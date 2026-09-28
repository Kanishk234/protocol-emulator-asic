# Timing of the WARP hard primitives (BUGS #17, D-028)

nextpnr's FABulous back end times a user design with:
- **routing:** the pip delays the fabric flow extracted from the hardened tiles (STA of each tile netlist, FABulous timing model), at the sign-off corner `nom_slow_1p08V_125C`;
- **tile library cells:** nextpnr's built-in fixed arcs (LUT 3.00 ns, clock-to-Q 1.00 ns, setup 2.50 ns, carry 0.20 ns);
- **WARP primitives** (`wp_timer`, `wp_shift`): the arcs in `macro/<fabric>/fabulous/.FABulous/placement_estimate.txt`, generated here. Without them nextpnr leaves every path through a primitive untimed.

## How the arcs are made

1. `tools/timing/prim_sta.sh`: Yosys synthesizes each primitive alone (`arch/prims/*.v`) onto the IHP CMOS5L standard cells (slow corner liberty `sg13cmos5l_stdcell_slow_1p08V_125C`); OpenSTA reports, with a 100 ns clock, zero input/output delays, 0.2 ns input transitions and 10 fF output loads, and the configuration bits as false paths (they are static while a design runs):
   - clock-to-out of every output, setup and hold of every input (to the primitive's flip-flops), and every combinational input → output delay (the timer's `en` → `tc`).
   - Result: `tools/timing/prims.arcs` (committed).
2. `scripts/gen_prim_timing.py`: writes them as nextpnr `BelBegin`/`SetupHold`/`ClkToOut`/`Delay` lines, with margins: **clock-to-out ×1.5, setup and combinational ×3.0**, negative holds as 0.

## Margins and the cross-check against the hardened tile

The standalone synthesis has no placement, wires or fanout loading; the hardened `PRIM2T2S` tile places the same logic among the switch matrix. `tools/timing/tile_check.sh` runs OpenSTA on the hardened tile (routed netlist, extracted parasitics, slow-corner liberty; configuration latches as false paths) and compares, at the tile boundary, with what the compile flow's model allows for the same paths (primitive arc + the longest chain of in-tile pips):

| Worst path (2026-09-28) | Hardened tile STA | Model |
|---|---|---|
| clock → tile output wire | 6.79 ns | 15.17 ns (arc 4.48 + pips 10.70); with a single pip 9.63 |
| tile input wire → primitive flip-flop | 8.06 ns | 12.06 ns (arc 4.20 + pips 7.85) |

The worst input path runs through five switch-matrix muxes and then, inside the timer, a 4-input NOR driving 33 loads (2.90 ns) before `count[0]`: the timer's own setup in the tile is about 4.0 ns, against 1.40 ns standalone. A ×1.5 margin did not cover that (first version of this model), so setup and combinational arcs use ×3.0; clock-to-out stays ×1.5, which bounds the tile even counting a single pip. The comparison is at the tile boundary and for the one identified internal path, not path by path for every primitive pin (their nets lose their names in the hardened netlist); nor is a configured design timed end to end by STA.

Consequence (G1, slow corner, nextpnr estimates): UART 90.7 MHz, SPI controller 78.0, I2C controller 53.0; all above the 50 MHz clock, the I2C controller with little margin.

## Numbers (2026-09-27, slow corner, standalone, before the margins)

| Primitive | Arc | ns |
|---|---|---|
| `wp_timer` | clock → `tc` | 2.98 (16-bit compare with zero) |
| `wp_timer` | `en` → `tc` | 0.34 |
| `wp_timer` | setup `rst`, `load`, `en`, `half` | 1.40, 1.39, 1.29, 0.90 |
| `wp_shift` | clock → `q`, `sout`, `done` | 0.30–0.32, 0.60, 0.92 |
| `wp_shift` | setup `step`, `load`, `sin`, `rst`, `d` | 1.08, 1.03, 0.64, 0.63, 0.55–0.62 |
