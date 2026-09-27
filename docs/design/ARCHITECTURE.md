# Architecture (hardware contract), v1

**Status:** v1, written 2026-09-26 at the end of phase 1. RTL, fabric definition (`arch/`), tools and reference models follow this document; changes go through DECISIONS. Items marked **OPEN** are decided in phase 2 with a DECISIONS entry and a version bump here.
**Version tag:** the architecture version is a 16-bit number (`ARCH_VERSION`, §3); v1 of this document = `0x0001`.

WARP is a small FABulous eFPGA fabric specialized for protocol emulation, behind a fixed shell. Users write synthesizable Verilog (§10), compile it on a host into a bitstream, load it through the host interface (§2, §3) and start it (§4). The shell owns loading, run control, parking and the host byte channels; everything protocol-specific is in the bitstream (D-002).

The phase 1 spike top (`src/tt_um_warp.v`, D-018: 16-LUT fabric, bit-bang loader, RUN pin) is a stepping stone, not this contract.

---

## 1. Top level and pin allocation

Top module `tt_um_warp`, TT 6x4 tiles, IHP CMOS5L, clock `clk` (§5).

| Pin | Name | Dir | Owner | Notes |
|---|---|---|---|---|
| `ui[0]` | HOST_CS_N | in | shell | host interface chip select, active low (§2) |
| `ui[1]` | HOST_SCK | in | shell | host interface clock, ≤ clk/8 |
| `ui[2]` | HOST_MOSI | in | shell | host → chip data |
| `ui[3..7]` | FAB_IN0..4 | in | fabric | synchronized (§6) |
| `uo[0]` | HOST_MISO | out | shell | chip → host data, driven 0 while CS_N is high |
| `uo[1]` | HOST_IRQ | out | shell | high when the host should read (§2.4) |
| `uo[2..7]` | FAB_OUT0..5 | out | fabric | registered, parked when not RUNNING (§4, §6) |
| `uio[0..7]` | FAB_IO0..7 | in/out | fabric | registered output + output enable, open-drain capable (§6) |

19 pins belong to the loaded design (5 in, 6 out, 8 bidirectional); 5 to the shell. This is D-006's allocation, now binding.

## 2. Host interface

### 2.1 Physical
SPI target, **mode 0** (sample MOSI on SCK rising, change MISO on SCK falling), MSB first, 8-bit bytes. SCK, MOSI and CS_N are synchronized to `clk` (two flops), so **SCK ≤ clk/8** (6.25 MHz at 50 MHz), CS_N falling to the first SCK rising edge ≥ 8 clk, and CS_N high between transactions ≥ 4 clk (D-021). A transaction is everything between CS_N falling and rising; the first byte is the opcode.

### 2.2 Framing
- During the opcode byte the chip shifts out the **STATUS byte** (§2.4), so every transaction also polls status.
- Multi-byte fields are big-endian.
- A transaction that ends early (CS_N rises mid-byte or mid-payload) discards the partial byte/command; LOAD_DATA keeps whole words already received (§3).

### 2.3 Commands
| Opcode | Name | Payload (host → chip) | Response (chip → host, after the opcode) | Allowed in state |
|---|---|---|---|---|
| `0x01` | READ_ID | — | 4 bytes: `0x57 0x50` ("WP"), ARCH_VERSION (2) | any |
| `0x02` | READ_STATUS | — | STATUS, then ERROR_CODE | any |
| `0x10` | LOAD_BEGIN | ARCH_VERSION (2), LENGTH in 32-bit words (2) | — | any but RUNNING (in LOADING it restarts the load, D-021) |
| `0x11` | LOAD_DATA | n × 4 bytes (bitstream words) | — | LOADING |
| `0x12` | LOAD_END | CRC-32 of all LOAD_DATA words (4) | — | LOADING |
| `0x20` | RUN | — | — | LOADED |
| `0x21` | STOP | — | — | RUNNING |
| `0x22` | USER_RESET | — | — | RUNNING (pulses the user reset, §5) |
| `0x30` | CH_WRITE | FLAGS (bit 0 = last), DATA | — | RUNNING |
| `0x31` | CH_READ | — | DATA (valid only if STATUS.rx_valid was 1) | RUNNING |
| `0x32` | USER_STATUS | — | the user design's status byte (§7.3) | RUNNING |

A command not allowed in the current state is ignored and sets ERROR_CODE `0x01` (bad command) without changing state, except that it never leaves RUNNING or starts a load.

### 2.4 STATUS byte
| Bits | Field |
|---|---|
| [7:5] | STATE: 0 UNCONFIGURED, 1 LOADING, 2 LOADED, 3 RUNNING, 4 ERROR |
| [4] | rx_valid: a design → host byte is waiting (CH_READ) |
| [3] | tx_ready: the host → design channel has space (CH_WRITE) |
| [2] | ch_overflow (sticky until READ_STATUS): a CH_WRITE arrived while full, byte dropped |
| [1] | user_attention: the user design raised its attention output (§7.3) |
| [0] | error_pending: ERROR_CODE ≠ 0 (cleared by READ_STATUS once its ERROR_CODE byte is sent) |

HOST_IRQ = rx_valid | user_attention | (STATE == ERROR).

ERROR_CODE (second response byte of READ_STATUS): `0x00` none, `0x01` bad command, `0x10` wrong ARCH_VERSION, `0x11` LENGTH mismatch, `0x12` CRC mismatch, `0x13` bitstream sync/format error. A load error always replaces ERROR_CODE; a bad command sets it only when it is 0 (D-021).

## 3. Configuration loading

- **Bitstream:** the FABulous frame-based bitstream for the current architecture (`tools/compile/` output), a sequence of 32-bit words starting with the sync word `0xFAB0FAB1`, then per frame a header word (frame select + column) and one data word per fabric row, ending with a desync header (bit 20). The shell forwards words to FABulous's `ConfigFSM` (`src/fabric_gen/`) as they arrive.
- **Checks:** LOAD_BEGIN's ARCH_VERSION must equal the chip's (else ERROR `0x10`, no word is forwarded). LOAD_END's CRC-32 (IEEE 802.3 polynomial, over all LOAD_DATA words in order, big-endian bytes) must match, and exactly LENGTH words must have arrived (else ERROR `0x11`/`0x12`). The first word must be the sync word (else `0x13`; forwarding stops at once; a load with no words is also `0x13`, BUGS #12). Wrong ARCH_VERSION is reported at LOAD_BEGIN; sync, LENGTH and CRC at LOAD_END, in that order (D-021). Words beyond LENGTH are not forwarded.
- **Consequence of streaming:** words are written into configuration latches before the CRC is known, so after any load error the fabric holds partial configuration. The shell then stays in ERROR (fabric stopped, outputs parked) until a new complete, correct load. **A load that fails any check never reaches RUNNING** (formal property F2, VERIFICATION).
- **Time:** ~(bitstream words × 32) SCK cycles; the 96-LUT fabric's bitstream is estimated at ~2–3 K words (≈ 15–25 ms at 6 MHz). To measure in phase 2.

## 4. Run control and output parking

States (§2.4): UNCONFIGURED → (LOAD_BEGIN) LOADING → (LOAD_END ok) LOADED → (RUN) RUNNING → (STOP) LOADED. Any load error → ERROR; LOAD_BEGIN from LOADING, LOADED or ERROR starts a new load (the design is stopped first). `rst_n` low → UNCONFIGURED.

**Parking (hard rule):** unless STATE is RUNNING, every fabric output pin is 0 and every `uio_oe` bit is 0 (all `uio` pins inputs), and the user design is held in reset. The parking gate is an AND after the shell's output registers (§6), so pins are 0 in the same cycle STATE leaves RUNNING, and it sits after the fabric, so no configuration state can override it (formal property F1).

## 5. Clocking and reset
- One clock, `clk`, target **50 MHz** (`CLOCK_PERIOD` 20 ns). The shell and the user design both run on it; the fabric receives it through a global buffer (south IO tile → GBUF, as in the spike).
- **OPEN:** whether user designs meet 50 MHz on the fabric. If not, phase 2 adds a shell clock enable (user logic runs every N-th cycle) rather than a second clock domain. Protocol rates in user READMEs are stated against the achieved rate.
- `rst_n` (synchronous, active low) resets the shell. The user design's reset (fabric SYS_RESET and the user reset input) is asserted while STATE ≠ RUNNING and for one cycle on USER_RESET.
- The configuration path runs on `clk`; it is idle while RUNNING.

## 6. I/O cells
Implemented in the shell for G0/G1 (phase 3 may move them into fabric IO tiles, see §9):
- **Inputs** (`ui[3..7]`, `uio_in`): two-flop synchronizers before the fabric. User designs need no synchronizers of their own (profiling rank 4, `docs/reports/profiling.md`).
- **Outputs** (`uo[2..7]`, `uio_out`, `uio_oe`): registered after the fabric (one `clk` of latency), with the parking gate (§4).
- **Open drain:** a user design drives a `uio` pin open-drain by keeping its output value 0 and toggling output enable (pull low = oe 1, release = oe 0), as the I2C designs do. No separate mode bit.

## 7. Fabric resources (current variant)

### 7.1 G1 (planned phase 2 build; D-008, D-016)
- Grid: 4 × 3 LUT-size tile slots (plus IO/edge tiles), next to a shell column (`docs/reports/capacity.md`). One slot holds the primitive tile (§8): **88 LUT4+FF**, 2 timers, 2 shift registers.
- Logic: `LUT4x8_ha` tiles from `mole99/fabulous-tiles` 7999e5a (8 × LUT4 + FF, carry chain) with the WARP CMOS5L patch (D-010, D-017).
- Clock: 4 global buffers.
- Configuration: frame-based latches, 32 frame bits per row, up to 20 frames per column; loaded through §3.
- **G0** = the same grid with all 12 slots LUT tiles (96 LUT4): the equal-area baseline (D-004), built and measured, not the fallback.

### 7.2 Pins into the fabric
The 19 user pins of §1 connect to IOBUF BELs in the west, east and south IO tiles. Pin → BEL mapping is fixed per architecture version and published in `arch/` (the compile flow's pin constraints).

### 7.3 Host channel into the fabric (D-014)
The shell's host byte channels and status reach the user design through dedicated IOBUF BELs on the fabric's north edge:
- host → design: `h_wdata[7:0]`, `h_wlast`, `h_wvalid` (into the fabric), `h_wready` (out of the fabric);
- design → host: `h_rdata[7:0]`, `h_rvalid` (out), `h_rready` (in);
- `h_status[7:0]` (out, read by USER_STATUS) and `h_attention` (out, STATUS bit 1).
Each direction has a 2-entry FIFO in the shell (D-021; revisit with the fabric's area), emptied whenever STATE ≠ RUNNING. In G0 (`arch/warp_g0`) the signals use 15 IO cells on the west, north, south and east edges; each cell carries one signal into the fabric and two out (value and enable wires), so `h_status` keeps its 8 bits (D-024). Pin map: `arch/warp_g0/pins.csv`; user designs' `h_*` ports map by name.

## 8. Hard primitives

**Candidates** (profiling ranks 1–2, D-016; G1 builds them, D-026). Each becomes part of the architecture only through the phase 3 method: DECISIONS entry (profiling data, users, area, cost to non-users), Yosys mapping, nextpnr placement, bitstream configuration, and a compiled user design using it after loading through §3.

### 8.1 Timer (loadable down-counter), `wp_timer`
- Config bits (per bitstream): `RELOAD[15:0]`, `ONESHOT`.
- Inputs (from routing): `rst`, `load`, `half`, `en`. Output: `tc`. Clock: the tile's global clock.
- **Cycle-exact behaviour** (state `count[15:0]`, `armed`; priority rst > load > en; v2 of this section, 2026-09-27):
  - `tc` = `en` ∧ `armed` ∧ (`count` = 0) (combinational from the current state and `en`);
  - on the clock edge: `rst` → `count` := RELOAD, `armed` := 1; else `load` → `count` := (`half` ? RELOAD ≫ 1 : RELOAD), `armed` := 1; else if `en` ∧ `armed`: `count` = 0 → (`count` := RELOAD, `armed` := ¬ONESHOT), otherwise `count` := `count` − 1.
  - So with `en` held high a free-running timer pulses `tc` every RELOAD + 1 cycles (a divider by N uses RELOAD = N − 1), and `load` with `half` gives the first `tc` after RELOAD/2 + 1 cycles (sampling at mid-bit).
- Users (design set): UART (2: TX bit timer, RX bit timer), SPI controller (1: SCK half-period), I2C controller (1: quarter period).

### 8.2 Shift register with bit count, `wp_shift`
- Config bits: `LEN[3:0]` (steps until `done`, 1–15), `MSB_FIRST`.
- Inputs: `rst`, `load`, `d[7:0]`, `step`, `sin`. Outputs: `sout`, `q[7:0]`, `done`.
- **Cycle-exact behaviour** (state `sr[7:0]`, `n[3:0]`; priority rst > load > step):
  - `sout` = MSB_FIRST ? `sr[7]` : `sr[0]`; `q` = `sr`; `done` = (`n` = LEN) (combinational from the state);
  - on the clock edge: `rst` → `sr` := 0, `n` := 0; else `load` → `sr` := `d`, `n` := 0; else `step` → `sr` := MSB_FIRST ? {`sr[6:0]`, `sin`} : {`sin`, `sr[7:1]`}, `n` := (`n` = LEN ? `n` : `n` + 1).
  - Transmit: `load` a byte, then `step` LEN times, `sout` carries each bit. Receive: `step` with `sin` = the line, `q` holds the byte when `done`.
- Users (design set): all four (UART TX/RX data, SPI MOSI/MISO, I2C controller and target data).
- Parallel width 8 (the design set moves bytes; frames longer than 8 bits, such as UART start/stop, are sequenced by user logic). **OPEN:** how many timers and shift registers one primitive tile holds, set by the tile's port budget (§9, D-026).

## 9. Architecture variants under evaluation
All compared at equal total area and the same clock target (D-004); results in `docs/reports/architecture_comparison.md` (phase 3).

| Variant | Content | Status |
|---|---|---|
| G0 | 12 LUT tiles (96 LUT4), shell with synchronizers/registered outputs | baseline |
| G1 | G0 with one slot = primitive tile (2 timers + 2 shift regs), 88 LUT4 | planned fallback (D-008) |
| G1 + regfile | + a register-file tile (FABulous `RegFile`) for the I2C target's map | only with a second user or a DECISIONS justification (D-016) |
| IO-tile features | synchronizers/registers moved from the shell into fabric IO tiles | phase 3 experiment |
| No carry | LUT tiles without the carry chain | phase 3 experiment (profiling: carry saves 0–18 LUTs per design) |

LUT size is fixed at LUT4 (the hardened tile library); LUT3/LUT6 are not pursued (profiling shows LUT6 fewer LUTs but 4× the LUT configuration bits; no LUT6 tile exists for this flow).

## 10. Supported user Verilog
- Synthesizable Verilog-2005 that Yosys `synth_fabulous` maps (the subset in CLAUDE.md): `default_nettype none`, no `initial` (flip-flops start from the user reset, §5), no latches, no internal tri-states (use output-enable ports), no memories unless a register-file primitive exists.
- **One clock**, the user clock (§5); synchronous or asynchronous resets to the user reset input.
- **Top module port convention** (D-014): `clk`, `rst_n`; pins as `pin_i`/`pin_o`/`pin_oe` bits named in the design's pin constraints (§7.2); host channel `h_w*`, `h_r*`, `h_status`, `h_attention` (§7.3), any subset.
- Settings are parameters fixed in the bitstream by default (D-014); primitives are instantiated explicitly by name (§8) until inference exists.
- Resource and rate limits per protocol are stated in each `protocols/<name>/README.md`.
