# Timing of the WARP hard primitives (BUGS #17, D-028)

nextpnr's FABulous back end times a user design with:
- **routing:** the pip delays the fabric flow extracted from the hardened tiles (STA of each tile netlist, FABulous timing model), at the sign-off corner `nom_slow_1p08V_125C`;
- **tile library cells:** nextpnr's built-in fixed arcs (LUT 3.00 ns, clock-to-Q 1.00 ns, setup 2.50 ns, carry 0.20 ns);
- **WARP primitives** (`wp_timer`, `wp_shift`): the arcs in `macro/<fabric>/fabulous/.FABulous/placement_estimate.txt`, generated here. Without them nextpnr leaves every path through a primitive untimed.

## How the arcs are made

1. `tools/timing/prim_sta.sh`: Yosys synthesizes each primitive alone (`arch/prims/*.v`) onto the IHP CMOS5L standard cells (slow corner liberty `sg13cmos5l_stdcell_slow_1p08V_125C`); OpenSTA reports, with a 100 ns clock, zero input/output delays, 0.2 ns input transitions and 10 fF output loads, and the configuration bits as false paths (they are static while a design runs):
   - clock-to-out of every output, setup and hold of every input (to the primitive's flip-flops), and every combinational input → output delay (the timer's `en` → `tc`).
   - Result: `tools/timing/prims.arcs` (committed).
2. `scripts/gen_prim_timing.py`: writes them as nextpnr `BelBegin`/`SetupHold`/`ClkToOut`/`Delay` lines, **multiplied by 1.5**, negative holds as 0.

## Why a margin, and what it does not cover

The standalone synthesis has no placement, no wires and no tile-level buffering; the hardened `PRIM2T2S` tile places the same logic with the switch matrix around it. The ×1.5 factor stands for that wiring, as a documented conservative model, not a measurement. The switch matrix itself (tile wires ↔ primitive pins) is in the pip delays.

Not yet done (phase 2 timing-model item): a cross-check against STA of the hardened tile, or of one configured design on the fabric.

## Numbers (2026-09-27, slow corner, before the margin)

| Primitive | Arc | ns |
|---|---|---|
| `wp_timer` | clock → `tc` | 2.98 (16-bit compare with zero) |
| `wp_timer` | `en` → `tc` | 0.34 |
| `wp_timer` | setup `rst`, `load`, `en`, `half` | 1.40, 1.39, 1.29, 0.90 |
| `wp_shift` | clock → `q`, `sout`, `done` | 0.30–0.32, 0.60, 0.92 |
| `wp_shift` | setup `step`, `load`, `sin`, `rst`, `d` | 1.08, 1.03, 0.64, 0.63, 0.55–0.62 |
