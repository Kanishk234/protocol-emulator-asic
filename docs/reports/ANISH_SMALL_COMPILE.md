# Small reference-derived fabric compilation — 2026-09-29

Follow-up: [cold-load execution](ANISH_SMALL_COLD.md) now passes in RTL
and with both LUT tiles mapped. The compilation-only limitations below
describe this original run; reload and full-chip physical gates remain open.

Run `warp-small-compile.khvqjtBG` generates a fabric with two LUT4AB tiles
(16 LUT4 sites), two W_IO tiles (four bidirectional pins), and north/south
terminators. The grid has two columns and two configurable rows; no DSP,
register-file or RAM tiles are instantiated. This is an isolated generation
experiment, not a production fabric definition or physical footprint.

A two-bit counter with reset and enable on pins 0/1 and outputs on pins 2/3
compiles through FABulous 2.2.0 and the supported June OSS CAD Suite.
Yosys/nextpnr produce four LUT-type logic cells, 70 non-comment FASM
features and a 504-byte image. Its SHA-256 is
`e5c8fa594fe4bda05795adc31884d154e8b9e0f365ea7462f01433b77b8e6c36`.
Image length matches 20 header bytes + 2 columns × 20 frames × 3 words ×
4 bytes + 4 footer bytes. Frame structure still needs an independent decoder.

## False-success control and correction

The first run `warp-small-compile.kAys0TJS` is **invalid as a counter
compilation result**, despite its runner's original PASS message. The
generated wrapper left io_in/io_out/io_oeb unconnected; nextpnr routed zero
arcs and bit generation warned that there were no features. A nonempty
binary alone was insufficient evidence.

Inspection of the installed FABulous 2.2 wrapper generator shows that it
automatically connects only its specially named `sequential_16bit_en` demo;
other designs require manual connections, as its warning states. The
corrected runner connects the three buses in a separate generated copy,
checks exact anchors, then invokes compilation. It rejects empty FASM,
fewer than two LUT-type logic cells, zero routing arcs and wrong image size.
Original installation and the existing large reference remain unchanged.

## Reproduction and remaining gate

```bash
# Activate .venv-fabric and the supported June toolchain first.
bash scripts/fabric_small_compile.sh build/fabric-reference-warp-reference.OBUfXfus
```

The run retains generated RTL, wrapper, grid, source hashes, synthesis and
routing logs, tool versions, bitstream and compile-summary.json. The project
template comes from the installed pinned package; no new package install
or physical tool run was performed.

This is compilation evidence only. Live configuration, pin behavior,
mapped execution, hold release, validator geometry and physical timing
remain untested for this grid. Generic nextpnr timing is not CMOS5L timing.
The production GDS source list and placeholder top are unchanged.

Next use this cached project for a public-port cold-load RTL test, then
adapt the checked hold/loader path and run the same oracle on mapped logic.
Do not start with a physical run before that functional gate passes.
