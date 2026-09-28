![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/unit/badge.svg) ![](../../workflows/fabric/badge.svg) ![](../../workflows/formal/badge.svg)

# WARP: a reprogrammable protocol emulator on Tiny Tapeout

WARP is our entry to the Jane Street Protocol Emulator ASIC competition (Tiny Tapeout, IHP 130 nm CMOS5L, 6x4 tiles). Instead of a small CPU running protocol code, the chip holds a small **FPGA fabric specialized for protocols**: 88 LUT4 logic cells plus two kinds of generic hard blocks (a loadable timer and a shift register with a bit count), behind a management shell with a checked SPI loader. You write a protocol in Verilog, compile it into a bitstream on your computer, and load it into the chip; changing protocols changes the bitstream, not the silicon. The architecture was chosen from measurements of real protocol designs and tested on a held-out set sealed before profiling: the frozen chip runs UART, SPI and I2C, plus three of four protocols it was never tuned for (WS2812, 1-Wire, SWD; CAN does not fit). Everything is verified in simulation and formal proofs; nothing has run on silicon yet.

## Where to look

| | |
|---|---|
| What is claimed, and the evidence for each claim | [docs/CLAIMS.md](docs/CLAIMS.md) |
| How to use it: write, compile, load, run | [docs/USER_GUIDE.md](docs/USER_GUIDE.md), [docs/EXAMPLES.md](docs/EXAMPLES.md) |
| How the architecture was chosen (equal-area comparison) | [docs/reports/architecture_comparison.md](docs/reports/architecture_comparison.md), [docs/reports/g1_limits.md](docs/reports/g1_limits.md), [docs/reports/profiling.md](docs/reports/profiling.md) |
| Protocols it was never designed for | [docs/reports/heldout_results.md](docs/reports/heldout_results.md) |
| Verification: formal proofs, mutation campaign | [docs/reports/formal.md](docs/reports/formal.md), [docs/reports/mutation.md](docs/reports/mutation.md) |
| The hardware contract | [docs/design/ARCHITECTURE.md](docs/design/ARCHITECTURE.md) |
| Decisions, bugs, phase summaries | [docs/DECISIONS.md](docs/DECISIONS.md), [docs/BUGS.md](docs/BUGS.md), [docs/summaries/](docs/summaries/) |
| Tiny Tapeout datasheet page | [docs/info.md](docs/info.md) |

## Quick start (simulation)

Linux or WSL with Python ≥ 3.12 and the tools in [docs/VERSIONS.md](docs/VERSIONS.md) (OSS CAD Suite 2026-06-29, Icarus, Verilator, and sigrok-cli).

```sh
scripts/setup_venv.sh && source .venv/bin/activate
bash scripts/fetch_nextpnr.sh             # the compile flow's nextpnr (D-028)
scripts/check_all.sh                      # lint, unit tests, shell checks, idle-fabric chip tests
scripts/build_test_bitstreams.sh --check  # rebuild and compare the committed bitstreams

# compile a protocol into a bitstream
cd tools && python -m compile.compile --pins ../protocols/uart/pins.yaml -o ../build/uart ../protocols/uart/*.v

# load real bitstreams into the whole chip (fabric RTL model) and run them
cd .. && make -C test WARP_FABRIC=rtl
make -C test_internal/cosim               # source RTL vs the loaded UART bitstream
```

## Repository

| Path | Contents |
|---|---|
| `src/` | the chip: shell (`wp_*`), top level `tt_um_warp`, fabric black box |
| `arch/` | fabric definitions (`warp_g1` is the chip), hard primitives (`arch/prims`) |
| `macro/` | the hardened fabric macros and their tool files |
| `protocols/` | user designs: UART, SPI, I2C controller, I2C target, WS2812, 1-Wire, SWD, CAN |
| `tools/compile/` | the compile flow; `tools/board/` the demo-board loader and examples; `tools/host/` the host protocol; `tools/refmodels/` independent reference models |
| `test/` | chip-level tests (top-level pins only, also run on the gate-level netlist) |
| `formal/`, `test_internal/` | formal proofs; white-box tests and the co-simulation |

## Tiny Tapeout

Tiny Tapeout is an educational project that makes it easier and cheaper to get digital and analog designs manufactured on a real chip: https://tinytapeout.com. This repository started from the [ttihp-verilog-template](https://github.com/TinyTapeout/ttihp-verilog-template); the template's workflows build the GDS, run the precheck and the gate-level test on every change.
