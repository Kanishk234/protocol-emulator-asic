# WARP user guide

WARP is a Tiny Tapeout chip that becomes a hardware protocol engine after fabrication: you describe a protocol in Verilog, compile it on a computer into a **bitstream**, and load that bitstream into the chip's small FPGA fabric through its host SPI port. This guide covers the three parts the organizers asked for (D-032): **the flow from a protocol description to a bitstream**, **how the bitstream gets onto the chip**, and **working examples** (`docs/EXAMPLES.md` walks through UART, SPI and I2C step by step).

Status: everything here is tested in simulation (RTL and the hardened gate-level netlist, `docs/CLAIMS.md`); nothing has run on silicon or a board yet.

```
your_protocol.v + pins.yaml ──tools/compile──▶ .wbit ──loader (host SPI)──▶ chip: RUN ──host channel / pins──▶ the world
```

## 1. What you get

| Resource | Amount | Notes |
|---|---|---|
| Logic cells | **88** LUT4 + flip-flop | a flip-flop shares a cell only with the LUT that feeds it alone; each group of 8 cells shares one clock enable and one reset (the compiler handles this, BUGS #15) |
| Hard timers `WP_TIMER` | **2** | 16-bit loadable down-counters (§4) |
| Hard shift registers `WP_SHIFT` | **2** | 8-bit, with a bit count (§4) |
| Pins | 5 inputs, 6 outputs, 8 bidirectional | table in §3 |
| Host byte channel | 1 byte each way per transaction | 2-entry FIFO each way in the chip |
| Clock | the project clock (50 MHz target) | one clock for the whole design |

A bitstream holds one design at a time; loading another replaces it (stop first). The chip keeps every fabric pin **parked** (outputs 0, bidirectional pins released) and the design **in reset** whenever it is not RUNNING.

## 2. Writing a design

A design is a synthesizable Verilog-2005 module (ARCHITECTURE.md §10):

- **One clock** (`clk`) and a synchronous active-low reset (`rst_n`, asserted by the chip whenever the design is not running, and for one clock on the USER_RESET command).
- No `initial` blocks (flip-flops start from `rst_n`), no latches, no internal tri-states (use output-enable ports), no memories (use registers; there is no RAM block).
- **Pins** are ordinary ports: inputs `*_i`, outputs `*_o`, output enables `*_oe` (the names are your choice; the pin map connects them).
- **Host channel** ports, matched by name (use any subset):

| Port | Dir | Meaning |
|---|---|---|
| `h_wdata[7:0]`, `h_wvalid`, `h_wready` | in, in, out | bytes from the host (CH_WRITE); a byte is taken when `h_wvalid && h_wready` |
| `h_wlast` | in | the host marked this byte "last" (CH_WRITE's flag) |
| `h_rdata[7:0]`, `h_rvalid`, `h_rready` | out, out, in | bytes to the host (CH_READ); delivered when `h_rvalid && h_rready` |
| `h_status[7:0]` | out | a byte the host reads any time (USER_STATUS) |
| `h_attention` | out | raises the chip's STATUS bit 1 and its HOST_IRQ pin |

Inputs arrive through two-flop synchronizers in the chip, so designs need none of their own. Outputs leave through a register.

## 3. Pin map

A YAML file names the top module, optional parameters, and where each port goes:

```yaml
top: uart_top
params:            # parameters of the top module (fixed in the bitstream)
  DIV: 87
pins:
  clk: clk
  rst_n: rst_n
  rx_i: FAB_IN0
  tx_o: FAB_OUT0
  sda_oe: FAB_IO0.oe      # a bidirectional pin: .o (value), .oe (enable), .i (input)
  sda_i: FAB_IO0.i
# h_* ports map by name: no entries needed
```

| WARP pin | Tiny Tapeout pin | Direction |
|---|---|---|
| `FAB_IN0..4` | `ui_in[3..7]` | input |
| `FAB_OUT0..5` | `uo_out[2..7]` | output (always driven; **0 while the chip is stopped**) |
| `FAB_IO0..7` | `uio[0..7]` | bidirectional: `.o`, `.oe`, `.i` (released while stopped) |
| (host) | `ui_in[0..2]`, `uo_out[0..1]` | reserved for the host SPI port |

**Active-low outputs** (a chip select, a CAN TXD) should go on a `FAB_IO` pin with an enable and a pull-up, not on `FAB_OUT`: a parked `FAB_OUT` pin is 0, which would assert them while the chip is stopped (BUGS #19). An output mapped without an enable is always enabled while running.

## 4. Hard primitives

Instantiate them by name; the compiler maps them to the fabric's blocks (ARCHITECTURE.md §8 has the cycle-exact definition).

```verilog
WP_TIMER #(.RELOAD(16'd433), .ONESHOT(1'b0)) t (
    .clk(clk), .rst(!rst_n), .load(start), .half(1'b0), .en(1'b1), .tc(tick));

WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b0)) s (
    .clk(clk), .rst(!rst_n), .load(start), .step(tick), .sin(rx), .d(byte_in),
    .sout(bit_out), .done(done), .q(byte_out));
```

- **`WP_TIMER`**: `tc = en & armed & (count == 0)` (combinational). On a clock edge: `rst` → count = RELOAD, armed; else `load` → count = `half` ? RELOAD >> 1 : RELOAD, armed; else if `en & armed`: at 0 reload (and disarm if ONESHOT), otherwise count down. With `en` held high a periodic timer pulses every RELOAD + 1 clocks; `half` gives a first pulse at the middle of a period (mid-bit sampling, a 0-bit's short pulse, a 480 µs half of a 960 µs one-shot: the held-out designs use all of these).
- **`WP_SHIFT`**: `sout` = MSB_FIRST ? `q[7]` : `q[0]`, `done = (steps since load == LEN)`, `q` = the register. On a clock edge: `rst` clears; `load` takes `d` and clears the count; `step` shifts `sin` in at the far end. Transmit: load a byte, step LEN times. Receive: step with `sin` = the line, read `q` when `done`.
- **Timing tip:** avoid combinational paths from your logic into a timer's `en` and back out of `tc` into logic (WS2812 gained 12 MHz by tying `en` high and using `load` to hold the timer).
- **Simulating your design alone:** compile `tools/compile/prims/warp_prims_sim.v` with `arch/prims/wp_timer.v` and `arch/prims/wp_shift.v` (the fabric's own primitive RTL), as `protocols/*/test/Makefile` do.

## 5. Compiling

```sh
source .venv/bin/activate
cd tools
python -m compile.compile --pins ../path/pins.yaml [--set NAME=VALUE ...] -o ../build/mydesign ../path/*.v
```

Needs the OSS CAD Suite (`docs/VERSIONS.md`) and `bash scripts/fetch_nextpnr.sh` once. Output in the `-o` directory:
- `<name>.wbit`: the bitstream (header: architecture version, length, CRC-32);
- `report.json`: logic cells, hard blocks and IO cells used, the parameters, pins, unmapped ports, the tool versions, and an Fmax **estimate** at the slow corner (a model, `tools/timing/README.md`; keep it above your clock);
- logs of every step.

Add `--strict-ports` to reject unmapped inputs and outputs before synthesis.
Without it, omitted inputs are tied to zero and omitted outputs are left open;
both are listed in the report. This option helps catch a forgotten signal in
the pin map. Intentional omissions can use the default behavior.

Errors you may see: a pin-map error (unknown port or pin, a pin used twice),
"no legal placement" (the design does not fit: inspect `synth.log` and
`pnr.log`, then §7), or a missing tool. `report.json` is written only after a
successful build. A placement/routing failure writes `failure.json` with
available resource counts and the error; over-capacity resources are also
printed. A rebuild clears previous success/failure reports so they cannot be
mistaken for its result. The target `.wbit` is also invalidated before rebuilding,
so a failed build cannot leave an old image at the advertised output path;
other images in that directory are preserved. The printed model Fmax is not
whole-chip timing signoff.

Successful reports now also record the placement seed, control-mapping threshold
and SHA-256 fingerprints of listed sources, pin map, architecture/generated
fabric files, compiler files and the emitted image. Check them with:

```sh
python -m compile.audit ../build/mydesign/report.json
```

The audit rejects missing/changed listed inputs, a swapped or corrupt image,
and disagreement between the image and report's architecture/length/CRC.
Reports retain the original absolute paths, so keep those inputs available.
This is a consistency check, not authentication or timing/behavior signoff;
recursive Verilog includes and vendor binaries/libraries are outside its scope.
If a listed input changes during compilation, the compiler rejects the build
before emitting an image. Legacy reports need a rebuild to obtain fingerprints.

`python -m compile.protocols` compiles every design in `protocols/` and prints the fit table.

## 6. Loading and running

**From the Tiny Tapeout demo board** (MicroPython on its RP2040): `tools/board/warp.py` (`tools/board/README.md`):

```python
import warp
w = warp.on_demo_board(clock_hz=10_000_000)
w.load_file("mydesign.wbit")   # refuses a bitstream for another chip; the chip checks length and CRC
w.run()
w.ch_write(0x42); print(w.ch_read(), w.user_status(), w.status())
w.stop()
```

**From any other host:** the chip is an SPI target (mode 0, SCK ≤ clk/8) on `ui_in[0]` CS_N, `ui_in[1]` SCK, `ui_in[2]` MOSI, `uo_out[0]` MISO. Every transaction's first MISO byte is STATUS. Commands (ARCHITECTURE.md §2–3; the reference implementation is `tools/host/protocol.py`):

| Opcode | Command | Bytes after the opcode |
|---|---|---|
| `0x01` | READ_ID | 4 dummies → `'W' 'P'` + architecture version |
| `0x02` | READ_STATUS | 2 dummies → STATUS, error code |
| `0x10` / `0x11` / `0x12` | LOAD_BEGIN / LOAD_DATA / LOAD_END | architecture (2) + length in words (2) / words / CRC-32 (4) |
| `0x20` / `0x21` / `0x22` | RUN / STOP / USER_RESET | — |
| `0x30` / `0x31` / `0x32` | CH_WRITE / CH_READ / USER_STATUS | flags (1) + byte / 1 dummy → byte / 1 dummy → `h_status` |

STATUS = `{state[2:0], rx_valid, tx_ready, ch_overflow, user_attention, error_pending}`; states UNCONFIGURED, LOADING, LOADED, RUNNING, ERROR. Error codes: `0x01` bad command, `0x10` wrong architecture, `0x11` length, `0x12` CRC, `0x13` format. HOST_IRQ (`uo_out[1]`) is high when a byte is waiting, the design wants attention, or the chip is in ERROR. A failed load leaves the chip in ERROR with every pin parked; RUN is refused until a good load.

## 7. Limits and what fits

| Design | Logic cells (of 88) | Hard blocks | Fmax estimate | Where |
|---|---|---|---|---|
| UART (8N1, RX + TX) | 29 | 2 timers, 2 shifts | 90.7 MHz | `protocols/uart` |
| SPI controller (modes 0–3) | 47 | 1, 1 | 78.0 MHz | `protocols/spi_ctrl` |
| I2C controller (with clock stretching) | 70 | 1, 1 | 53.0 MHz | `protocols/i2c_ctrl` |
| WS2812 transmitter | 32 | 2, 1 | 54.3 MHz | `protocols/ws2812` |
| 1-Wire controller | 77 | 2, 1 | 54.5 MHz | `protocols/onewire` |
| SWD host (bit engine) | 44 | 1, 1 | 54.4 MHz | `protocols/swd` + `tools/board/swd.py` |
| I2C target (4 registers) | 169 | — | does not fit | `protocols/i2c_target` |
| CAN 2.0A | 207 | — | does not fit | `protocols/can` |

- **One design at a time**; no pair of the designs above fits together.
- **The host channel is a byte per transaction**: a protocol that needs a byte every few microseconds (WS2812) needs a host that keeps up; the demo board's MicroPython loader does not (milliseconds per transaction).
- Rates on silicon are not measured; the Fmax column is a model.

## 8. Testing a design

- **Alone:** a cocotb test of your module with the primitives' simulation files (§4); `protocols/*/test/` are templates, each against an independent reference model in `tools/refmodels/`.
- **On the chip model:** add a pin map under `tools/compile/examples/` (a `sources:` list may point anywhere), `scripts/build_test_bitstreams.sh`, and a test in `test/test_bitstream.py` using `load_and_run` (the fabric RTL model: `make -C test WARP_FABRIC=rtl`).
