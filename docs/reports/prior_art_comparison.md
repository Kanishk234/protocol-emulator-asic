# WARP and prior art (phase 5)

**Basis:** WARP's numbers are ours (sources in `docs/EVIDENCE.md`). Everything about the other designs is **their published description** (`docs/notes/prior_art.md`, read 2026-09-25), not measured by us. No equal-area measurement against any of them exists, so nothing here says WARP is better at protocols per area (CLAIMS rules).

| | **WARP** | PRISM lite (TTIHP26b) | Tiny FABulous (TT SKY26a) | RP2040 PIO | TI PRU |
|---|---|---|---|---|---|
| Process / platform | TT 6x4, IHP CMOS5L | TT, IHP | TT, SKY130 | RP2040 MCU | TI SoCs |
| Programmable element | LUT4 fabric (88 cells) + 2 hard timers + 2 hard shift registers | indexed state machine: 32 states per 128-bit words, two LUT3 decisions per state | generic LUT4 fabric (128 cells), no hard blocks | 4 state machines, 9-instruction ISA, 32-instruction memory | 32-bit RISC cores |
| Execution | spatial: all logic every clock, several state machines in parallel | one state transition per clock | spatial | one instruction per clock per state machine | sequential instructions |
| User writes | Verilog (+ pin map) | a Verilog Mealy machine | Verilog | PIO assembly | C / assembly |
| Toolchain | Yosys + nextpnr + our bitgen, checked `.wbit` | Yosys backend | FABulous flow | pioasm | TI compilers |
| Protocol datapath | chosen from profiling; generic timer and shift register only | fixed per shard: counters, shifter, FIFO, CRC, Manchester recovery, sampler | none | shift registers, FIFOs, side-set | none (software) |
| Loading / safety | host SPI loader checking architecture, length, CRC-32; every pin parked unless a checked design runs (proven, F1) | CPU writes the state table (shift chains) | FABulous loader | from the MCU | from the host CPU |
| Needs a CPU on chip | no | yes (TinyQV RISC-V) | no | (it is part of an MCU) | (is the CPU) |
| Protocols shown | UART, SPI, I2C controller; held out: WS2812, 1-Wire, SWD (CAN, I2C target do not fit) — simulation only | UART, SPI, I2C, 1-Wire, WS2812, USB LS device, 10BASE-T (larger build) — their claims | generic examples | many (widely used) | many (widely used) |
| Method | profiling, equal-area comparison of fabric variants, sealed held-out set | not published | not applicable | — | — |

## What WARP does differently, as far as the evidence goes

1. **How the architecture was chosen.** The hard blocks come from profiling the design set (counters 23 %, shift registers 17 % of its LUTs) and were kept only after an equal-area comparison with a plain fabric (3 of 4 design-set protocols vs 1), then tested on protocols sealed before profiling (3 of 4 run). We have not seen this method published for the designs above.
2. **Spatial execution with no CPU.** Unlike PRISM, PIO and PRU, a WARP design is logic evaluated every clock, and the chip has no processor. Whether that is better or worse per area than PRISM's state machine is **not measured**; PRISM shows more protocols on similar silicon by its own account.
3. **Generic blocks only.** PRISM's datapath includes protocol-oriented units (Manchester recovery, CRC); WARP's two blocks are a counter and a shifter (D-002). UART, SPI and I2C controller behaviour is in their bitstreams; SWD packet decisions run in host software. The held-out results show the blocks being used in ways they were not designed for.
4. **A verified load path.** Output isolation is proven for all fabric behaviour (F1), corrupt loads are rejected (F2, bounded), and the chip-level tests run on the hardened netlist.

## Not claimed
- "First" FPGA or first reprogrammable protocol engine on Tiny Tapeout or IHP: Tiny FABulous and PRISM predate WARP, and FABulous's own IHP tapeouts were not checked in detail.
- Better protocol coverage per area than PRISM, PIO or PRU: no equal-area measurement.
