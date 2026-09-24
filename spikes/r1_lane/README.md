# R1 risk spike: one lane at 50 MHz

Throwaway RTL for phase 1 task 13 (R1). The results and decision are in `docs/reports/R1_LANE_TIMING.md` and DECISIONS D-030. This is **not** the phase 2 RTL. It lives outside `src/`, so it never triggers a hardening, and no CI workflow reads it.

Written only from `docs/design/ARCHITECTURE.md`, `docs/design/ISA.md` and `spec/tripwire.yaml` (through the generated `src/trw_defs.vh`), without reading `tools/tripsim` or `tools/kernels`.

| File | What |
|---|---|
| `trw_lane.v` | One lane: 12 ready() terms, the §4.3 selection, EVAL static updates, EXEC with the shared ALU, r0–r3, STATE, f0–f2, RB, PEND, output reservations, O0/O1 producer registers; routine steps from a RIR input (ALU, LDI, LDIH, DJNZ, OUT, SYS) |
| `trw_alu.v` | The 16-op table (ISA.md §3) |
| `trw_slots.v` | 12 slots + K0–K3: an Ibex-style latch array (one clock gate per 16-bit host word); `-DTRW_SLOTS_FLOPS` gives the flop fallback |
| `trw_cport.v` | A fabric consumer port: source mux, F1/F2/F7 |
| `trw_r1_top.v` | Timing harness: dummy producers (9), subscriber state (17) for the release term, RIR, RUN and the host write port, all registers on one shift chain |
| `tb_r1_lane.v` | Sanity simulation: ISA.md §7.1 (forward r0 bytes, 3 clocks per byte, then an EVENT) |
| `sta.tcl` | OpenSTA script: EVAL and EXEC endpoint groups |
| `run_r1.sh` | Everything: simulation, Verilator lint, Yosys synthesis (latch/flop slots × plain/sized mapping), STA (typ/slow × configuration dynamic/static) |

Not modelled: the routine sequencer (RPC, fetch, BR/LD/ST, SRAM rotation), host debug reads, the fire-every-other-clock fallback, F5 (port re-pointing).

## Run

```
spikes/r1_lane/run_r1.sh          # 20 ns; or run_r1.sh <period_ns>
```

It needs Icarus, the OSS CAD Suite (Yosys, Verilator) and network access on first use: it downloads the cmos5l liberty files at the PDK revision `scripts/gl_local.sh` uses, and extracts the standalone `sta` binary from a prebuilt OpenROAD package (plus `libtcl8.6` and `tcl-tclreadline` via `apt-get download`, no root) into `~/.cache/tripwire/openroad`. Output goes to `build/` (git-ignored); `build/summary.txt` is the table in the report.
