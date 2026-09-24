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
| WS2812 LED strips | ✅ every datasheet timing tolerance met (added with PULSE mode, point 11) |
| DShot150–1200 motor control | ✅ frames, checksums and bit timing correct (point 11) |
| PS/2 keyboard/mouse (host side) | ✅ both directions, parity errors caught (point 12) |
| 1-Wire (e.g. temperature sensors) | ✅ reset, presence, read/write with exact standard timing (point 12) |
| SWD (ARM chip debugging) | ✅ reads, writes, "wait" replies, up to 8.3 MHz (point 12) |
| JTAG (chip debugging/testing) | ✅ any scan sequence, up to 12.5 MHz (point 12) |
| CAN 2.0A/B (cars, industrial machines) | ✅ 11- and 29-bit IDs, arbitration, error flags, error counters, bus-off, up to 1 Mbit/s (points 13, 14) |
| MIDI, DMX512 (stage lighting), servo PWM, IR remotes (NEC) | ✅ (point 14) |
| SMBus with packet error checking, LIN (cars), I2S (audio), HDLC | ✅ (point 14) |
| USB low-speed | ⚠️ feasibility only: enumerated by a reference host on the model (point 14); not a support claim |
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
- **Expected with today's features** (the programs are still to be written): I2S, MIDI, DMX, SMBus, IR. (SWD, JTAG, PS/2 and 1-Wire have since been done, see 12.)
- **One planned feature away:** WS2812 and DShot (since done, see 11).
- **CAN** needed a few more general features (since done, see 13).
- **USB low-speed** now needs only a couple more (NRZI coding, end-of-packet detection, a paired output), and is only studied for feasibility.
- **10 Mbit Ethernet** is honestly out of reach at a 50 MHz clock.

**11. We added PULSE mode, and two more protocols work.** One general feature (each bit is a short "level A for a while, then level B for a while" pattern) covers LED strips (WS2812), drone motor controllers (DShot), IR remotes and Manchester codes. WS2812 and DShot now run on the model, checked against their datasheet timing and, for WS2812, sigrok. For DShot the chip computes the frame checksum itself in a routine.

**12. Four debug and peripheral protocols now work: PS/2, 1-Wire, SWD and JTAG.** Each ran against its own reference device, written from its spec (for example an ARM debug port for SWD and an IEEE 1149.1 test port for JTAG), and sigrok agreed. Two needed one small general addition (D-020): the chip can now say *when* to start counting bits on an input, and it can sample an input at a time it picks rather than on a clock edge. PS/2 needed the first because the chip's own "please wait" signal looked like a data bit; 1-Wire needed the second because its read slots have no clock at all. SWD and JTAG needed nothing new. Along the way the tests caught a real mistake in the SWD program (leftover data leaking into the next transaction) and an off-by-one bug in sigrok's own PS/2 decoder.

**13. CAN, the first stretch goal, works on the model.** CAN is much harder than the others: every node listens while it talks, the lowest ID wins a collision bit by bit, a receiver must answer inside the sender's frame, and the clock is recovered from the data itself. We added one general pin-unit mode (BITSYNC, D-023) that does the bit-level work: it re-syncs to the line on every edge, inserts and removes "stuff" bits, computes and checks a CRC, compares what it sends with what it hears, and can answer in one bit of someone else's frame. None of it is CAN-specific: the same unit also runs an HDLC-style configuration (different stuffing, different CRC) in its own tests. A reference CAN node written from the Bosch spec, and sigrok's CAN decoder, both agree with the chip at 125 kbit/s, 500 kbit/s and 1 Mbit/s. Building it exposed three real design problems (commands stuck behind queued data, a stale length command, an acknowledgement one bit early in a rare case), all fixed in general ways and logged (BUGS #10–#15). Error frames and bus-off handling are not done yet.

**14. We added every remaining protocol on the list.** MIDI (the UART program at MIDI speed), DMX512 lighting, RC servos, NEC infrared remotes, SMBus with its checksum computed on chip, LIN (the car body bus), I2S audio, HDLC framing, the rest of CAN (29-bit IDs, remote frames, error flags, error counters and bus-off), and a USB low-speed feasibility study where a reference PC-side host enumerates the chip. Where a protocol exposed a real gap we added one general feature, never a protocol block: timestamps in coarser ticks and an IR/RF carrier (D-024), flag-delimited framing and a separate transmit CRC (D-025), error signalling and a listen-only mode (D-026), NRZI coding, a complementary output and end-of-packet handling (D-027), and lookup tables in the compiler (D-028). Every feature is now also tested outside its first protocol, and deliberately breaking each one makes a test fail. The independent checks found real mistakes again: several in my programs (a race that stretched servo frames, a register overwritten mid-routine in CAN, branches the wrong way round in USB), in the compiler (a timing bound that hid long paths, an address expression cut short), in the chip model (a transmitter re-syncing to its own echo, caught by sigrok decoding our USB packets), and in two of sigrok's own decoders. All are logged (BUGS #16-#31). USB stays a feasibility study: no hardware, one endpoint, and our rules forbid claiming USB support.

**15. We measured whether the lane is the right size, and wrote down what to freeze.** A new script (`tools/explore/metrics.py`) counts what every program uses. All 23 lanes fit in 12 rules. Six use exactly 12, so the lane is right-sized with no room to spare. Only one lane (CAN) uses all four registers.

Turning each shortcut off on paper shows that each one earns its place:
- Without testing a bit of the incoming word directly in the rule, five lanes would no longer fit.
- Without getting a flag from any arithmetic result, two lanes would no longer fit.
- Without the four built-in constants, five lanes would run out of registers.

We also reran every protocol test with each lane working only every other clock, the fallback if the real chip turns out too slow. All 103 still pass. So even the fallback would lose no protocol; what it costs is the fast reaction time we advertise.

All of this is proposed as one freeze decision (D-029) for both of us to review:
- close the seven early open questions;
- set a connection table that fits every program;
- leave out the four optional helper blocks, which no program needed;
- move one host pin so the demo board's standard SPI hardware can talk to the chip.

We also made the per-push tests about 20 times faster locally by moving the five longest simulations to a nightly run.

**16. The first hardware experiment (R1): a lane can decide every clock at 50 MHz.** In a fresh session that never looked at the model, we wrote one lane in Verilog from the design documents alone: the 12 rules, the logic that picks one, the arithmetic unit, and the channel ports that feed it. A small simulation checked that it works; it forwards bytes at exactly the 3 clocks each the documents promise. We then turned it into real IHP 130 nm cells with Yosys and timed it with OpenSTA, the timing tool the chip flow uses.

| | Typical chip | Slow chip (hot, low voltage) |
|---|---|---|
| Time to decide (worst case we could build) | 7.3 ns | 11.4 ns |
| Time to decide (planned design, buffered) | 3.6 ns | 5.6 ns |
| Time available per clock | 20 ns | 20 ns |

So the "every other clock" fallback isn't needed (D-030, accepted). These numbers are before layout: real wires will add delay, but the worst case would have to grow by more than 70 % to fail. The R2 run will measure it after layout. One lane with latch-based rule memory comes to about 65K µm², so three lanes use about a fifth of the chip. Writing the Verilog without the model also turned up eight places where the documents leave a choice open or contradict themselves (for example, which register one field selects). None of them affects timing, but they need answering in the rules before the real Verilog is written.

## What's left in Phase 1
1. **Freeze the spec:** flip `spec/tripwire.yaml` from draft to frozen once the hardware experiments below have had their say.
2. **A second person reviews the cycle-by-cycle rules.** The freeze decision (D-029) is accepted and applied: the connection table is in the spec and the compiler enforces it, the host's MISO pin moved so the demo board's hardware SPI can reach it, and no open questions remain in the design documents.
3. **Hardware experiments:**
   - R1: done (item 16); D-030 accepted;
   - R2: check that latch-based rule memory survives Tiny Tapeout's flow (a small separate hardening run, reusing the R1 lane);
   - R3: check that the SRAM macro is usable (another small hardening run).
4. **Answer the eight open choices** R1 found (`docs/reports/R1_LANE_TIMING.md` §6) in the cycle-by-cycle rules.

## In one line
Phase 1 so far has shown, in a faithful simulation, that the architecture handles every required protocol at the speeds that matter, and it has corrected the design along the way. What's left is locking that design down and testing the riskiest hardware assumptions.
