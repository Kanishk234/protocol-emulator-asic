# WARP end-to-end examples: UART, SPI, I2C

From a protocol written in Verilog to that protocol running on the chip, in four steps: **compile** (host computer), **copy** (to the demo board), **load and run** (demo board), **use** (demo board). This is the software side the organizers asked for (D-032): the flow from a protocol description to a bitstream, how the bitstream is loaded, and working examples.

```
protocols/<p>/*.v + pins.yaml ──tools/compile──▶ <p>.wbit ──mpremote cp──▶ RP2040 ──tools/board/warp.py──▶ chip (host SPI)
                                                                                 └─tools/board/examples.py: talk to the protocol
```

What is tested and how is listed at the end. **Nothing here has run on real hardware yet** (no board).

## The chip's pins

| Tiny Tapeout pin | WARP pin | Used for |
|---|---|---|
| `ui_in[0..2]` | HOST_CS_N, HOST_SCK, HOST_MOSI | the loader (host SPI, ARCHITECTURE §2) |
| `uo_out[0]`, `uo_out[1]` | HOST_MISO, HOST_IRQ | the loader |
| `ui_in[3..7]` | FAB_IN0..4 | protocol inputs |
| `uo_out[2..7]` | FAB_OUT0..5 | protocol outputs |
| `uio[0..7]` | FAB_IO0..7 | protocol bidirectional pins (open drain for I2C) |

A protocol's pin map (`protocols/<p>/pins.yaml`) names which of these its ports use. Every fabric pin is parked (0, output disabled) unless the chip is RUNNING.

## Setup (once)

Host computer: this repository with `scripts/setup_venv.sh`, the OSS CAD Suite and `scripts/fetch_nextpnr.sh` (docs/VERSIONS.md), and `mpremote`. Board: a Tiny Tapeout demo board with the WARP chip and the Tiny Tapeout MicroPython firmware (`ttboard`).

```sh
source .venv/bin/activate
mpremote cp tools/board/warp.py :warp.py
mpremote cp tools/board/examples.py :examples.py
```

The examples below assume a **10 MHz project clock** (`warp.on_demo_board(clock_hz=10_000_000)`); each protocol's rate is a parameter of its design, set at compile time with `--set`.

## UART (115200 baud)

Design: `protocols/uart` (8N1; RX with mid-bit sampling and framing/overrun flags). Pins: `rx_i` = FAB_IN0 (`ui_in[3]`), `tx_o` = FAB_OUT0 (`uo_out[2]`). Divisor: clocks per bit = 10 MHz / 115200 ≈ 87 (0.2 % off).

```sh
cd tools
python -m compile.compile --pins ../protocols/uart/pins.yaml --set DIV=87 \
    -o ../build/ex/uart ../protocols/uart/*.v           # -> build/ex/uart/uart_top.wbit
mpremote cp ../build/ex/uart/uart_top.wbit :uart.wbit
```

```python
import warp, examples as ex
w = warp.on_demo_board(clock_hz=10_000_000)
w.set_fab_in(1)                  # RX idle high until something drives it
w.load_file("uart.wbit")
w.run()
ex.uart_send(w, b"hello\r\n")    # out on uo_out[2]
print(ex.uart_recv(w, 4))        # bytes received on ui_in[3]
print(ex.uart_errors(w))         # (overrun, framing_error, tx_busy)
```

Wire `uo_out[2]` to the other device's RX and its TX to `ui_in[3]` (common ground, 3.3 V levels). To loop back, connect `uo_out[2]` to `ui_in[3]`.

## SPI controller (mode 0, 1 MHz SCK)

Design: `protocols/spi_ctrl` (modes 0–3 by parameter, MSB first, full duplex). Pins: SCK = FAB_OUT0 (`uo_out[2]`), MOSI = FAB_OUT1 (`uo_out[3]`), CS_N = FAB_OUT2 (`uo_out[4]`), MISO = FAB_IN0 (`ui_in[3]`). SCK half period = 5 clocks at 10 MHz.

```sh
python -m compile.compile --pins ../protocols/spi_ctrl/pins.yaml --set HALF=5 \
    -o ../build/ex/spi ../protocols/spi_ctrl/spi_ctrl_top.v
mpremote cp ../build/ex/spi/spi_ctrl_top.wbit :spi.wbit
```

```python
w = warp.on_demo_board(clock_hz=10_000_000)
w.load_file("spi.wbit"); w.run()
print(ex.spi_transfer(w, [0x9F, 0, 0, 0]))   # e.g. a flash JEDEC-ID read: CS low for all 4 bytes
```

**Active-low outputs while the chip is stopped (BUGS #19).** Until RUN (and after STOP), every `uo_out` fabric pin is parked at **0**, so a CS_N on `uo_out[4]` is asserted (low) during loading, with SCK idle and no data. A device that reacts to CS alone should get CS_N on a bidirectional pin instead, driven only while running and pulled up: map `cs_n_o` to `FAB_IO2.o` and an always-1 enable to `FAB_IO2.oe` (`uio[2]`), with a pull-up; parked, `uio[2]` is released and the pull-up holds CS_N high.

## I2C controller (~100 kHz)

Design: `protocols/i2c_ctrl` (START / repeated START / STOP, byte write with ACK check, byte read with ACK or NACK, clock stretching). Pins: SDA = FAB_IO0 (`uio[0]`), SCL = FAB_IO1 (`uio[1]`), open drain: **add pull-ups** (e.g. 4.7 kΩ to 3.3 V). SCL phase = 2·Q clocks: Q = 25 → ~100 kHz at 10 MHz.

```sh
python -m compile.compile --pins ../protocols/i2c_ctrl/pins.yaml --set Q=25 \
    -o ../build/ex/i2c ../protocols/i2c_ctrl/i2c_ctrl_top.v
mpremote cp ../build/ex/i2c/i2c_ctrl_top.wbit :i2c.wbit
```

```python
w = warp.on_demo_board(clock_hz=10_000_000)
w.load_file("i2c.wbit"); w.run()
print(ex.i2c_probe(w, 0x48))                      # True if a device ACKs 0x48
ex.i2c_write_regs(w, 0x48, 0x01, [0x60])          # register 1 := 0x60
print(ex.i2c_read_regs(w, 0x48, 0x00, 2))         # registers 0..1
```

## Changing protocols

`w.stop()` parks every fabric pin; `w.load_file(...)` then loads another bitstream (the loader refuses a file built for another architecture before sending anything; the shell refuses a wrong length or a bad CRC, ends in ERROR and keeps every pin parked); `w.run()` starts it. Any number of times, no chip reset needed (tested: `test_two_bitstreams`, `test_reload_from_loaded`).

## Writing your own protocol

A user design is a Verilog module with `clk`, `rst_n`, pin ports (`*_i` / `*_o` / `*_oe`) and optionally the host channel (`h_wdata`, `h_wvalid`, `h_wready`, `h_rdata`, `h_rvalid`, `h_rready`, `h_status`, `h_attention`, `h_wlast`). A pin map YAML names the top and maps ports to WARP pins; `h_*` ports map by name. The fabric has 88 LUT4 logic cells, 2 timers (`WP_TIMER`) and 2 shift registers (`WP_SHIFT`) that designs instantiate by name (ARCHITECTURE §8, §10). The compile report (`report.json`) gives the cells used, pins, parameters and an Fmax estimate (a model at the slow corner; `tools/timing/README.md`).

## What is tested

| Step | Test | Where |
|---|---|---|
| compile (all three protocols, fit and timing model) | `python -m compile.protocols --require uart spi_ctrl i2c_ctrl` | CI `fabric` |
| the protocols' logic | RTL tests against independent reference models (and sigrok for UART), plain and primitive forms | CI `unit` |
| load + run + use, from the host protocol | `test_uart`, `test_spi_ctrl`, `test_i2c_ctrl`: real bitstreams through the chip's pins, reference devices on the fabric pins | CI `gl_test` (hardened chip netlist) and `fabric` |
| **the board code itself** (`warp.py`, `examples.py`) | `test_board_loader` (UART), `test_board_examples_spi`, `test_board_examples_i2c`: the board modules, unchanged, drive the chip model's pins (cocotb bridge/resume) | `test/test_bitstream.py` |
| board module = reference host, byte for byte | `tools/board/tests` | CI `unit` |
| on real hardware | **not yet** (no board): the `ttboard` glue and real pin timing are untested | |

The test bitstreams use faster rates than above (`tools/compile/examples/uart16.yaml`, `spi8.yaml`, `i2c8.yaml`) so simulations stay short; the designs are the same.
