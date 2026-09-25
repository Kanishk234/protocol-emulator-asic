# Tiny FABulous: what we can reuse and what we must prove

Reviewed 2026-09-25. Primary reference: [IHP26a repository at
4b284f5](https://github.com/mole99/tt-fabulous-ihp-26a/tree/4b284f528febbec39208d49a931b75ef63f1937b).
This is source inspection, not a reproduction of its physical results.

## Integration

The project first hardens tiles, then stitches a `tiny_fabric_9x5` macro,
then integrates its GDS, LEF and netlist into the outer Tiny Tapeout block.
See [top config](https://github.com/mole99/tt-fabulous-ihp-26a/blob/4b284f528febbec39208d49a931b75ef63f1937b/config.yaml)
and [fabric config](https://github.com/mole99/tt-fabulous-ihp-26a/blob/4b284f528febbec39208d49a931b75ef63f1937b/fabrics/tiny_fabric_9x5/config.yaml).
The tile library is a pinned submodule. Generated RTL alone is not the
physical integration recipe: power connections, macro placement and
routing-layer constraints also matter.

This example is **8x4 on sg13g2**, not our 6x4 CMOS5L allocation. The fabric
config allows Metal5 and the top uses a custom PDN. Its GDS cannot simply
be imported as a CMOS5L implementation. Also, **9x5 is an internal fabric
grid, not 45 Tiny Tapeout tiles**. The related [IHP26b project
page](https://tinytapeout.com/chips/ttihp26b/tt_um_fabulous_ihp_26b) describes
168 LUT4+FF cells; that is precedent, not a WARP capacity estimate.

## Loading and testing

The [top wrapper](https://github.com/mole99/tt-fabulous-ihp-26a/blob/4b284f528febbec39208d49a931b75ef63f1937b/src/tt_um_fabulous_ihp_26a.sv)
enables configuration while the external reset is low. A bit-bang receiver
on `ui[0:1]` assembles words for a frame loader. Clock continues during
configuration. This reuses pins for normal fabric operation afterward;
it does not provide WARP's proposed runtime data/management channel.

The [README](https://github.com/mole99/tt-fabulous-ihp-26a/blob/4b284f528febbec39208d49a931b75ef63f1937b/README.md)
distinguishes constant-initialized emulation from dynamic-loading RTL
simulation, and describes gate-level tests. Only the dynamic path can
establish that configuration storage and the loader actually work.
The [test loader](https://github.com/mole99/tt-fabulous-ihp-26a/blob/4b284f528febbec39208d49a931b75ef63f1937b/tb/testcases/common.py)
also clears configuration before loading to avoid transient logic loops.
WARP needs an explicit initialization/reload protocol, not just output
masking: masking a pad does not stop an internal combinational loop.

## WARP consequence

Use FABulous as infrastructure, start with a small live-configured reference,
and separately demonstrate a CMOS5L physical path. Prefer the flat small
experiment first; consider a hardened tile/fabric macro only after routing
evidence and organizer clarification. Preserve upstream attribution and
pins. Do not copy relaxed congestion settings or sign-off exceptions as
proof of correctness.
