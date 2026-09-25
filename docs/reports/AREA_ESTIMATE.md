# Area estimate before the RTL (phase 2 task 2.0)

**Question:** does the frozen TRIPWIRE spec (v1.0, D-037) fit the 6x4 core, and if not, what are the options and what does each save?

**Answer: no, not as frozen.** The estimate puts the placed design at about **1.0–1.1 M µm², 109–120 % of the 902K µm² core**, where a routable design needs roughly 50–60 %. The lanes (~196K) and the SRAM (45K) are as expected. The surprise is the **pin units: ~84K µm² each, ~500K for six**, about half of the chip. The phase 1 budget (ARCHITECTURE §12) assumed ~0.55K flops for all six units; the spec now needs about 500 state and configuration bits *per unit*. No single cheap option closes the gap, so the scope decision goes to the team (see "Options").

Date: 2026-09-25. Reproduce: `spikes/area/run_area.sh`, then `python spikes/area/estimate.py` in the venv (outputs in `spikes/area/build/`, not committed).

---

## 1. Method

The chip RTL doesn't exist yet, so the estimate is built from measured pieces:
1. **Building blocks** (`spikes/area/ae_prims.v`): small representative Verilog modules for each datapath piece the spec needs (a 16.8 timer, the TX cursor, shifters, RX framing, a configurable CRC, the BITSYNC counters, pad selects, fabric producer and port, the SPI slave, read-back muxes, configuration storage). Each is written from ARCHITECTURE §4, §7, §9 and §14, not from the model, and is **not chip RTL**. Each is synthesized alone with Yosys onto the cmos5l cells (typical corner), the same recipe as R1.
2. **Counts:** how many of each block every chip part needs, from the spec. Pin-unit configuration bits come straight from the generated `PIN_CFG_FIELDS` table (D-036).
3. **Measured anchors:** one lane = 65.4K µm² (R1, Yosys); latch storage = 35.1 µm²/bit (R1 slot array, with clock gates and write path); flop storage = 73.4 µm²/bit (measured here); SRAM macro = 45.3K µm² (R3).
4. **Two factors that are assumptions**, shown as ranges:
   - **Control logic ("glue")** that the building blocks don't include (FSMs, CTRL-op decode, mode muxing, token formatting, flags): **30 / 45 / 60 %** of the pin-unit datapath.
   - **Layout growth** from Yosys area to placed-and-routed cells (buffers, resizing, hold fixing): **×1.30**, measured on R2 (the lane was ~79K µm² in Yosys and 103K after layout).

The feature use in section 4 comes from compiling every program in `programs/` with tripc.

## 2. Building blocks (Yosys, cmos5l typ, before layout)

| Block | What it is | µm² |
|---|---|---|
| timer24 | 16.8 next-event accumulator + compare with time (bit clock, sample point, carrier) | 3,376 |
| cursor | TX cursor (P4): 24-bit add, max with earliest, LATE; PRESC and tick countdown | 6,102 |
| txshift | 16-bit TX shifter, order, length-in-token, bit count | 2,576 |
| rxframe | RX word framing (P13): bit placement, two lengths, SETN override, taint | 3,224 |
| crc16 | configurable CRC, width 1–16, poly/init/res | 2,798 |
| bitsync_ctl | stuff counters, idle, frame count, resync step (SJW), NRZI, JAM count | 5,762 |
| pulse | PULSE two-phase symbol timer | 2,114 |
| padsel | 1-of-19 pad select + edge detector | 350 |
| event | event generator: 15-bit tick counter, qualifier | 1,239 |
| prod | fabric producer register | 1,540 |
| port7 / port8 / port9 | consumer port with 7 / 8 / 9 sources | 2,709 / 2,970 / 3,175 |
| padout | output pad driver (owner mux, open drain) | 172 |
| cfg22_flop | 22 host-written 16-bit words in flops (352 bits) | 25,833 |
| rdmux22 / rdmux48 | host read-back mux of 22 / 48 words | 4,406 / 10,315 |
| spi | host SPI slave (sync, command, address, data) | 6,837 |

## 3. One pin unit, by feature (glue 45 %, before layout)

| Feature | Config bits | Datapath | Glue | Config in flops | Config in latches | Total, flops | Total, latches |
|---|---|---|---|---|---|---|---|
| core (SHIFT, LINKED, CLKGEN, LEVEL, events, cursor, fabric ports) | 102 | 24.8K | 11.2K | 7.5K | 3.6K | 43.5K | 39.6K |
| pins C, S, N | 17 | 0.7K | 0.3K | 1.2K | 0.6K | 2.3K | 1.6K |
| PULSE | 50 | 2.1K | 1.0K | 3.7K | 1.8K | 6.7K | 4.8K |
| carrier | 24 | 3.4K | 1.5K | 1.8K | 0.8K | 6.7K | 5.7K |
| BITSYNC (with CRC) | 114 | 11.4K | 5.1K | 8.4K | 4.0K | 24.8K | 20.5K |
| **full unit** | **307** | | | | | **84.0K** | **72.2K** |

The core alone (43.5K) is half of a lane. Its biggest pieces are the 24-bit (16.8) time arithmetic: the cursor and two timers are 12.9K of its 24.8K datapath.

## 4. What the programs use (units per program)

| Program | Units | PULSE | carrier | BITSYNC | pins C/S/N |
|---|---|---|---|---|---|
| can, hdlc, usb_ls | 1 | 0 | 0 | 1 | 1 |
| dshot, onewire, ws2812 | 1 | 1 | 0 | 0 | 0 |
| ir_nec | 2 | 1 | 1 | 0 | 0 |
| spi_target | 2 | 0 | 0 | 0 | 2 |
| i2s, jtag, spi_controller | 4 | 0 | 0 | 0 | 0 |
| the other 10 | 1–2 | 0 | 0 | 0 | 0 |
| **most at once in one program** | **4** | **1** | **1** | **1** | **2** |

No program uses more than one unit with PULSE, carrier or BITSYNC, and none uses more than four units. Six units exist so that two or more protocols can run at the same time.

## 5. Whole chip

Other blocks (before layout): fabric outside lanes and units 25.9K, pad drivers/owners/synchronisers 7.8K, host interface 23.3K (with lane-register read-back), time base and SRAM wrapper 3.2K. **Placed = Yosys × 1.30 + the SRAM macro.**

| Scenario | Lanes | Pin units | Other | Placed (glue 30 / 45 / 60 %) | Share of core |
|---|---|---|---|---|---|
| **A. spec as frozen:** 6 full units, config in flops | 196K | 504K | 60K | 984K / 1,034K / 1,083K | **109 / 115 / 120 %** |
| B. A + slot and config read-back | 224K | 504K | 87K | 1,055K / 1,105K / 1,154K | 117 / 122 / 128 % |
| C. 6 full units, config in latches | 196K | 433K | 60K | 893K / 942K / 992K | 99 / 104 / 110 % |
| D. 2 full + 4 lean units (core + pins C/S/N), config in flops | 196K | 351K | 60K | 799K / 835K / 871K | 88 / 93 / 97 % |
| E. 2 full + 4 lean units, config in latches | 196K | 309K | 60K | 744K / 781K / 817K | 82 / 87 / 91 % |
| F. E with 2 lanes | 131K | 309K | 60K | 659K / 696K / 732K | 73 / 77 / 81 % |
| G. 4 units (2 full + 2 lean), config in latches | 196K | 227K | 60K | 647K / 674K / 700K | 72 / 75 / 78 % |
| H. G with 2 lanes | 131K | 227K | 60K | 562K / 589K / 615K | 62 / 65 / 68 % |

**What share of the core is routable?** R2 needed a local placement density near 42 % for the slot-array logic (Metal3 was 66 % used even then). The template default is 60 %. So a target of **about 50–60 %** (450–540K µm² placed) is realistic, and the lower end is safer for a first full hardening.

## 6. How sure is this?

- **Robust:** the conclusion that the frozen spec does not fit. Even the most optimistic column of scenario A is 109 %, about twice a routable target.
- **Uncertain (±20–30 %):** the absolute numbers. The glue share is a guess until real pin-unit RTL exists; LibreLane's own synthesis may map 10–20 % smaller than plain Yosys ABC; the ×1.30 layout factor comes from one lane.
- **Not counted:** the slot read-back port (unless stated), anything in phase 3–4 (helpers, the hardcaml checks don't add area), spare area for ECO fixes.

## 7. Options, with what each saves (placed, glue 45 %)

| Option | Saves | What we lose | General? (D-012) |
|---|---|---|---|
| 1. Configuration storage in latches (like the slots) | ~92K (A → C) | Nothing functional; more latch timing exceptions (the R2 SDC fix applies) | Yes |
| 2. Heterogeneous units: BITSYNC, PULSE and carrier on 2 of the 6 units | ~199K with config in flops (A → D) / ~161K in latches (C → E) | Two CAN/USB/HDLC or two WS2812/DShot at the same time need both full units; four at once is impossible | Yes: the same primitives, placed on fewer units. Programs name units, so tripc must place them |
| 3. Shrink the pin-unit core (design work) | est. 10–20K placed per unit (a guess until real RTL exists) | Depends: e.g. share one 24-bit adder between the cursor and the timers, or narrow the fraction from 8 to 4 bits | Yes, if the rules still hold (a DECISIONS entry per change) |
| 4. Fewer units: 6 → 4 | ~107K (E → G) | Fewer protocols at once; the four-unit programs (I2S, JTAG, SPI controller) then use every unit | Yes |
| 5. Two lanes instead of three | ~85K (E → F) | The two-lane CAN and LIN programs leave no free lane; fewer protocols at once | Yes |
| 6. No slot or config read-back | ~71K (B → A; already excluded from the other scenarios) | Host can't read back slots or pin settings (it wrote them; lane registers stay readable) | Yes |
| 7. 8x4 tiles | +~300K of core | Not offered yet; Jane Street and Tiny Tapeout are "working on it". Not designed for until confirmed in writing (PHYSICAL §2) | n/a |

**Combinations (glue 45 %):**
- 1 + 2 (scenario E): 87 %.
- 1 + 2 + 4 (scenario G, four units): 75 %; with option 3 on the four units, about 66–70 %.
- 1 + 2 + 4 + 5 (scenario H, four units and two lanes): 65 %; with option 3, about **56–61 %**, the first combination inside the routable range.

So on these numbers, reaching the range takes nearly every option at once. That is why the next step is to measure, not to cut.

## 8. Recommendation

1. **Decide now** on the options that cost no function or little: **1 (latch config)** and **6 (no slot/config read-back)**. And **2 (heterogeneous units)**: every program uses at most one BITSYNC, PULSE or carrier unit, so two full units keep every program working, with room for two such protocols at once.
2. **Measure before cutting further.** The pin-unit core is the largest and least certain number. The RTL session should write `trw_pin_unit` first (before the lane, which R1 already measured), synthesize it, and replace the glue guess. Then choose between option 3 (shrink the core) and option 4 or 5 (fewer units or lanes), with real numbers.
3. **Ask Tiny Tapeout and Jane Street about 8x4** (asic-competition@janestreet.com). We don't design for it, but the answer changes how much we cut.

Each change to the frozen spec needs its own DECISIONS entry (D-037).
