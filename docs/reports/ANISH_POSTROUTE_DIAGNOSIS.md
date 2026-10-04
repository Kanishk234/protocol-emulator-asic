# Failed physical run: functional netlist and timing diagnosis

Source commit: `f478ee0`. CI run: [36603402850](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36603402850).
The downloaded GDS_logs artifact is cached in `build/ci-36603402850`.
No new hardening run was launched for this diagnosis.

## Actual post-route netlist passes functional simulation

The `final/nl/tt_um_warp.nl.v` netlist from that physical run passes the
same public-pin cocotb test using cached Icarus 13 and the CMOS5L cell
models. This includes loading the actual image, 256 counter checks,
incomplete-image and bad-CRC rejection, recovery on the same DUT, and
output parking/deselection. Simulation spans 4,692 clock periods.

Reproduce from the project root in `.venv-fabric`:

```bash
python scripts/test_small_top.py --netlist build/ci-36603402850/runs/wokwi/final/nl/tt_um_warp.nl.v
```

Evidence: `build/small-top-postroute.log`, `build/small-top-gl/results.xml`,
and `build/small-top-gl/inputs.json` with all netlist/model/test input hashes.
The runner now deletes stale result XML before running and requires an
actual passing testcase. RTL and netlist runs have separate build directories.

This is a functional gate-level test **without SDF** at the test's 1 us clock
period. It neither proves 50 MHz nor overrides the physical flow's failure.
The automatically dependent CI gate-level job did not run after GDS failed;
this is a separate local test of the preserved physical netlist.

## Worst reported path is disabled in the counter configuration

Post-route typical-corner max.rpt starts at `uio_in[3]`, ends at
`uio_out[2]`, and reports -93.720856 ns slack. Slow-corner worst slack is
-156.240806 ns. These are the unconstrained programmable fabric's reports,
not a measured maximum counter frequency.

The first functional gate after the input buffer is `_4259_`, an
`sg13cmos5l_a21oi_2`. Its A1 receives net14 from input3; A2 is tile X1Y1
frame1 bit4, and B1 is tile X1Y1 frame2 bit6. Its function is
`Y = ~((A1 & A2) | B1)`.

The counter image's column1 frame1 and frame2 row1 words are both zero.
They are words 70 and 73 (zero-based) in the independently framed image:
`5 + (column*20 + frame)*3 + 2`. The generated ConfigMem explicitly maps
frame2 bit6 to FrameData[6]/FrameStrobe[2]; row1 receives the last data word
of each frame. Thus A2=0 and B1=0 after this image loads: `_4259_/Y` is 1
independently of input3. The reported arc through that gate cannot be
sensitized in the stable counter configuration. The later `_4269_` mux
also has frame1 bits28/29=0, selecting A0 rather than the reported A3 path.

This is a **specific path/configuration witness**, not proof that all reported
violations are false, that other images are safe, or that loading transients
meet timing. The fabric permits different routing in other configurations.
Do not add a blanket false-path exception between these pins.

## Next gate

Follow-up local replay: `scripts/prepare_configured_sta.py` emits baseline
OpenSTA Tcl using the saved final netlist, SDC and nominal SPEF with the
cached typical CMOS5L Liberty. Cached OpenSTA 2.7.0 reproduces worst slack
**-93.72 ns** and reports TNS **-1876.43 ns**. Evidence is under
`build/configured-sta/` (`baseline.log`, `baseline.tcl`, `audit.json`).
This matches the worst-slack baseline before introducing case analysis.

The bounded decoder resolves 860 latch outputs to original frame/bit names.
Another 352 latch outputs use optimized aliases (for example LUT mux A15),
so the script deliberately does not emit counter.tcl. These counts describe
the physical netlist's latch instances, not a proof of complete configuration
storage correspondence. Resolve aliases and audit optimized-away/merged
storage before accepting a complete image-to-netlist map. No configured
timing pass is claimed from this partial mapping.

Build reproducible configuration-aware STA for the loaded image while
retaining separate management/load-mode analysis. Audit every case-analysis
assignment against the frame decoder and verify the resulting configuration
state; do not synthesize away the configuration storage in the actual chip.
Only then choose changes to routing, sequential boundaries or timing targets.
Generated-fabric lint is still open. No production constraints changed here.
