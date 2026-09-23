# Phase 7 (optional): hardware validation

| | |
|---|---|
| **Dates** | Any time hardware becomes available. **7A** can run alongside phases 3–5; **7B** happens after chips return (2027, if we win). |
| **Goal** | Upgrade claims from "verified in simulation" to "tested on real parts" by running the same programs, host scripts and sigrok decoders on an FPGA and, later, on silicon. |
| **Devices needed** | **Yes** (see §2) |
| **References** | `../VERIFICATION.md` §6 (L3), `../PHYSICAL_DESIGN_AND_CI.md` §8 |

This phase is **not on the critical path**. Nothing in phases 0–6 depends on it.

---

## 1. Principle
Use the same programs, the same `tools/host` API and the same sigrok decoders as in simulation. The only thing that changes is the transport:
- simulation;
- a USB-to-SPI bridge (e.g. a Raspberry Pi Pico running a small bridge firmware) talking to the FPGA;
- the TT demo board's RP2040 talking to the chip.

## 2. Equipment

| Item | Needed for | Rough cost | Notes |
|---|---|---|---|
| iCE40UP5K board (e.g. iCEBreaker) | 7A | ~$70–100 | Matches the `fpga` workflow's target; runs the reduced build |
| Raspberry Pi Pico (or similar) | 7A host bridge | ~$5 | Speaks the host SPI protocol; MicroPython or C |
| USB logic analyzer (8 ch, ≥ 24 MS/s, sigrok-supported) | 7A, 7B | ~$10–20 | Captures pins for sigrok decoding |
| 24C02 EEPROM, W25Qxx SPI flash | 7A | ~$5 | Real I2C/SPI peers |
| DS18B20 (1-Wire) | 7A | ~$3 | Real 1-Wire peer |
| WS2812 LED strip | 7A | ~$5 | Pulse-mode check |
| USB-UART adapter (FTDI/CH340) | 7A | ~$5 | Real UART peer at many bauds |
| Arduino or a second Pico as an I2C/SPI controller | 7A | ~$5 | Drives our target programs |
| 2 × MCP2515 + TJA1050 CAN modules | 7A (only if CAN built) | ~$10 | Real CAN bus |
| TT demo board + TRIPWIRE chip | 7B | Comes with the chips | Silicon bring-up |

## 3. Tasks

### 7A: pre-silicon, on FPGA
1. Build the reduced bitstream from the `fpga` workflow artefact; pin constraints for the chosen board.
2. Host bridge firmware on the Pico; the `tools/host` transport for it.
3. Board-level loopback first: UART TX → RX on the same FPGA, checked with the logic analyzer + sigrok.
4. Interop matrix, one row at a time:

| Protocol | Our role | Real peer | Evidence |
|---|---|---|---|
| UART | TX/RX | USB-UART adapter at 9600–1 Mbaud | sigrok `uart` capture + host log |
| SPI | Controller | W25Qxx: JEDEC ID, read | sigrok `spi`/`spiflash` |
| I2C | Controller | 24C02 read/write | sigrok `i2c` |
| I2C | Target (EEPROM) | Arduino/Pico as controller | sigrok `i2c` + controller log |
| 1-Wire | Master | DS18B20: read ROM, temperature | sigrok `onewire_*` |
| WS2812 | TX | LED strip | Visual + capture |
| CAN | Node | 2 × MCP2515 | sigrok `can`; peers' error counters stay 0 |

5. Note FPGA-specific differences (the reduced build, the clock source) in the report, so FPGA results are not confused with silicon results.

### 7B: post-silicon, on the chip
6. Power-up and ID read over the host port.
7. Run the same interop matrix on silicon, and measure the pin-to-pin reaction time with the logic analyzer.
8. Compare against simulation and publish the differences.

## 4. Phase exit checklist
**7A:**
- [ ] Reduced bitstream running on the board; host bridge working; the ID register reads correctly.
- [ ] Board loopback UART verified with sigrok.
- [ ] At least UART, SPI controller, I2C controller and I2C target interoperate with real parts, each with a saved capture.
- [ ] Results added to `CLAIMS.md` as "tested on FPGA with real parts" (distinct from silicon).

**7B:**
- [ ] Chip ID read; all lanes run.
- [ ] The interop matrix on silicon, with captures.
- [ ] Measured reaction time compared with the 140 ns design value; differences explained.
- [ ] Silicon results published in the repo.

## 5. Risks
| Risk | Response |
|---|---|
| The reduced FPGA build differs from the chip | Label FPGA evidence clearly; never present it as silicon |
| Level/voltage mismatches with peers | Check each peer's I/O voltage; use level shifters where needed |