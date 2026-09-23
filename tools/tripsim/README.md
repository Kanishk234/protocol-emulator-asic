# tripsim

The TRIPWIRE token-level, cycle-accurate model. In phase 1 it is the **architecture model**: parameterized, used to measure the questions in `docs/design/ISA.md` §9 (DECISIONS D-008). After the spec freeze it becomes the **golden model** for RTL lockstep.

**Independence rule:** written from `docs/design/ARCHITECTURE.md` (including the §14 cycle semantics) and `docs/design/ISA.md` only. Never read `src/` while working on this package.

| File | Contents |
|---|---|
| `isa.py` | Slot and routine encodings, the shared operation table (hand-written until `tools/gen` exists) |
| `asm.py` | Minimal assembler: `reflex(...)` slot builder, `Routine` builder, `link_routines` |
| `lane.py` | Reflex slots, EVAL/EXEC pipeline, routine sequencer |
| `pinunit.py` | Pin units: TX (LEVEL/OE/GAP/SYNC/SETN/WAIT, timed or linked SHIFT with preload, CLKGEN with STRETCH, PULSE symbols, length-in-token), RX (SHIFT_RX or LINKED_RX with two-phase framing and echo suppression; qualified edge-event generator), pin C select/frame |
| `fabric.py` | Producer registers, consumer ports with tag filters (blocking, tap) |
| `chip.py` | Top level: pads, synchronisers, ownership, SRAM rotation, host FIFOs |
| `vcd.py` | Pad activity to VCD for sigrok |

**Parameters** (`Chip(...)`): `lanes`, `slots`, `pin_units`, `sram_words`, `fire_period` (2 = the R1 "every other clock" fallback), `host_fifo_depth`.

Related: `tools/kernels/` (exploration firmware, e.g. the I2C target) and `tools/protomodels/` (reference protocol models written from the protocol specs, e.g. the I2C controller). Results go to `docs/reports/ARCH_EXPLORATION.md`.

**Not modelled yet:** the helper units CRC, MATCH, MEM and CAPTURE; the host SPI transport (the host is modelled as direct register access); the legal-source table.

**Run the tests:** `source .venv/bin/activate && python -m pytest -q` (also part of `scripts/check_all.sh`).
