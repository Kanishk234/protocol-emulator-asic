# Phase 1: will the idea actually work?

**Status:** in progress. The feasibility work is done; the spec freeze, the compiler and the hardware experiments remain (see the end). The plan and checklist are in `docs/design/phases/PHASE1_SPEC_MODEL_RISKS.md`.

## The goal
Phase 0 proved the *tools* work. Phase 1 asks whether the *idea* works, before we spend weeks building hardware. We changed the plan's order to answer that first ("model first", DECISIONS D-008): build a faithful software copy of the chip, run real protocols on it, and let the results shape the design before it is frozen.

## What we did

**1. We wrote down the instruction set (`docs/design/ISA.md`).** We researched how others do it: RP2040 PIO, TI PRU, the competing entry Loom, NXP FlexIO, and the academic *Triggered Instructions* paper. TRIPWIRE splits the work three ways:
- **Pin units** (smart pin hardware) handle bit timing: shifting bits out at a rate, sampling on clock edges.
- **Reflex slots**, rules of the form "when X happens, do Y", handle the protocol's decision-making, all checked every clock.
- **The channel fabric** moves data around, including one stream to several places at once.

**2. We built a software copy of the chip (`tools/tripsim`).** A Python model that behaves exactly like the chip would, clock by clock. Think of it as a flight simulator before building the plane: fast to change, and it tells you whether the design flies. Later, the same model checks the real Verilog clock by clock.

**3. We "flew" real protocols on it.** For each protocol, we wrote a small TRIPWIRE program (`tools/kernels/`) and ran it against an **independent reference device** written from the official protocol spec (`tools/protomodels/`), for example an I2C controller written from NXP's I2C document. sigrok then decoded the wires as a neutral referee.

| Protocol role | Result on the model |
|---|---|
| UART send / receive | ✅ up to 1 Mbaud tested, including fractional baud rates |
| SPI controller | ✅ up to 12.5 MHz |
| SPI target (we are clocked by someone else) | ✅ up to 12.5 MHz |
| I2C controller | ✅ 100 kHz / 400 kHz / 1 MHz, including a slow target stretching the clock |
| I2C target (reads and writes) | ✅ 100 kHz / 400 kHz / 1 MHz, about 2x margin on the ACK deadline |
| The headline "reaction time" claim | ✅ exactly 7 clocks (140 ns), as designed |

All numbers are from simulation with ideal wires. The full table, with the test behind each number, is `docs/reports/ARCH_EXPLORATION.md`.

**4. Every protocol exposed something missing or wrong, and we fixed the design.** This is the real value of the phase: finding mistakes on paper and in Python, where fixing them costs minutes, not in silicon, where it costs everything. Examples:
- A real bug in how the fabric counts dropped data: after missing two items, a listener went deaf (BUGS #2).
- A missing instruction (`MOVB`) that the reaction-time claim depended on (D-009).
- I2C needs separate "sample" and "drive" clock edges (D-010).
- SPI needs a third pin (chip select), which became the general "pin C" (D-014).
- The I2C controller needs clock stretching and a "wait for another pin's edge" command (D-016).

**5. We adopted a design principle: general *and* optimized (D-012).** Every gap was fixed with the most general mechanism that is still efficient, never an "I2C block" or an "SPI block". Protocol logic stays in firmware. That is also why the full I2C target went from needing 14–18 slots to fitting in exactly 12.

**6. We kept the numbers honest.** Several times a result looked better than physics allows. Each time we traced it before recording anything:
- 4 MHz I2C looked too good; it turned out to be real, but the test was tightened anyway.
- An SPI result of 16.7 MHz came from a lopsided clock; the honest figure is 12.5 MHz.
- A lucky test byte was hiding a timing limit; the test data was changed so it can't hide again.

We also broke the model on purpose many times to prove the tests notice. When one didn't, we fixed the test, not the story.

**7. A worry got smaller.** The biggest hardware risk (R1) is "can a lane decide every clock at 50 MHz?". The model showed that even the fallback of deciding every *other* clock doesn't reduce any protocol's speed limit.

**8. We wrote the design down in one machine-readable place.** `spec/tripwire.yaml` now holds every bit position and code in the chip's instruction and command formats. A generator (`tools/gen/gen.py`) turns it into:
- the tables the simulator uses;
- the Verilog constants the hardware will use;
- the tables in our design documents.

A check runs on every push and fails if anything drifts, so the documents, the model and (later) the hardware can't quietly disagree. The simulator now reads its encodings from this file instead of keeping its own copy. It's still marked *draft*: it gets "frozen" after the hardware experiments, which might still change a field width.

**9. We built a compiler, so programs are real firmware.** `tripc` turns a small, readable language (`.trw`) into exactly what gets loaded into the chip, and writes a report:
- how many rule slots and how much memory each program uses;
- the worst-case length of every routine;
- which rules can delay which.

It also catches mistakes before anything runs, such as testing an input the rule doesn't read, or using an undeclared state. The protocol programs now live in `programs/`. We proved the compiler right by checking that its output is **bit-for-bit identical** to the hand-built versions, and all the protocol tests now run on the compiled programs.

**10. We mapped which other protocols are within reach** (`docs/reports/PROTOCOL_SUPPORT.md`):
- **Expected with today's features** (the programs are still to be written): SWD, JTAG, PS/2, 1-Wire, I2S, MIDI, DMX, SMBus, IR.
- **One planned feature away:** WS2812 and DShot.
- **CAN** needs a few more general features: re-syncing the receiver on every edge, bit stuffing, detecting a lost arbitration, and a CRC unit.
- **USB low-speed** needs the CAN features plus a couple more, and is only studied for feasibility.
- **10 Mbit Ethernet** is honestly out of reach at a 50 MHz clock.

## What's left in Phase 1
1. **Freeze the spec:** flip `spec/tripwire.yaml` from draft to frozen once the hardware experiments below have had their say.
2. **Finish the checklist items the model still owes:** PULSE mode (for WS2812/DShot), turning each new feature off one at a time to measure its value, and a second person reviewing the cycle-by-cycle rules.
3. **Three hardware experiments**, each a small separate hardening run:
   - R1: build one lane in Verilog and check it runs at 50 MHz;
   - R2: check that latch-based slot memory survives Tiny Tapeout's flow;
   - R3: check that the SRAM macro is usable.

   These need real Verilog, which should be written in a fresh session that hasn't seen the model, so the two stay independent.

## In one line
Phase 1 so far has shown, in a faithful simulation, that the architecture handles every required protocol at the speeds that matter, and it has corrected the design along the way. What's left is locking that design down and testing the riskiest hardware assumptions.
