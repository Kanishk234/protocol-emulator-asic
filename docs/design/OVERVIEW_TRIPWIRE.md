# TRIPWIRE: overview and plan

A protocol emulator ASIC for the Jane Street Protocol Emulator ASIC Competition. Tiny Tapeout, IHP 130 nm CMOS5L, 6x4 tiles, deadline **2027-01-18**.

This is the single overarching document for the idea. It starts with what is new, then covers the concept, architecture, programming model, protocols, verification, CI, schedule with checklists, risks and open decisions.

Status: **concept stage.** All numbers are paper estimates until synthesis.

Companion documents: `ARCHITECTURE.md` (the hardware contract: datapath, formats, instruction sets) and `VERIFICATION.md` (tools, layers, proofs, CI).

**The name.** A tripwire does nothing until something crosses it, then it fires at once. TRIPWIRE's instructions work the same way: each one waits on a condition and fires the instant that condition becomes true.

---

## 1. What is new: the novelties we are going for

Honesty labels:
- **[NEW-FIELD]**: not found in any surveyed competition entry. It may have academic or industry prior art, which is cited. The first survey covered ~40 entries; by 2026-09-23 there are more (e.g. Tempo, Metastable, Sophos, PEMU, Cycle, PRISM, a Hardcaml entry). Re-check every label against the current field before submission.
- **[OURS]**: a design choice of ours not seen elsewhere.
- **[STANDARD]**: table stakes. We do it, but do not claim it as novel.

### 1.1 Architecture

1. **Triggered execution with no program counter on the fast path [NEW-FIELD].**
   - Each lane holds a set of *reflex* rules of the form "when *condition*, do *one action*".
   - Every rule's condition is a small hardware circuit, checked every clock in parallel. The highest-priority true rule fires.
   - Reaction from a pin edge to a pin response is a fixed ~7 clocks (~140 ns at 50 MHz), with no instruction fetch.
   - Prior art: *Triggered Instructions* (Parashar et al., ISCA 2013), proposed for spatial accelerators, never for protocol emulation.
   - Every other entry (PIO clones, Loom, TEMPO, and others) is a program-counter machine.
2. **A multicast channel fabric [NEW-FIELD].**
   - All blocks (pins, lanes, helper units, memory, host) exchange 16-bit tokens over a small on-chip network.
   - One stream can feed several consumers at once, for example protocol logic, a CRC checker and a capture recorder.
   - Each subscription is either **blocking** (the producer waits for it) or **tap** (it never slows anything, and drops are counted).
3. **Reflexes and routines, a two-tier program store [OURS].**
   - Hard-deadline logic lives in a few fast latch-array reflex slots.
   - Everything else lives as bounded *routines* in the SRAM macro.
   - Routines share the SRAM by a fixed rotation, and urgent reflexes can interrupt them.
   - The result is both a fixed reaction time *and* hundreds of instructions of program space.
4. **Pins that never wait, with defined overrun semantics [OURS].**
   - Pin receivers never stall, because the wire does not wait.
   - Whether a program can overrun is a property of the program, checked before loading (§1.2).
5. **Fixed-rotation sharing everywhere [OURS / STANDARD idea].** SRAM access and any other shared resource use fixed time slots, so no lane can ever delay another. This isolation is structural and provable.
6. **Timed smart pin units [STANDARD building block].**
   - Lanes send timed commands (level after delay, shift N bits, generate N clocks, pulse-coded bits) that the pin unit executes on the exact clock.
   - "Time as an operand" is TEMPO's headline idea and is not claimed by us. Loom, BitLoom, XMOS and FlexPRET also do timed I/O.
7. **Helper units on the fabric [STANDARD, light version of a systolic pipeline].** CRC, pattern match, and a memory unit that turns the SRAM into emulated-device memory (EEPROM or flash contents).

### 1.2 Verification

1. **Checking programs before they load [OURS].** Not new to the field on its own: a Hardcaml entry (MarcosAsh/protocol-emulator) already bounds pin-edge timing with an abstract-interpretation analyser. What is ours is checking the whole *channel graph* (deadlock and overrun across lanes, fabric and pin units), which only works because a TRIPWIRE program is an explicit graph. A program is a graph of channels, reflexes and routines, so the compiler can check it statically:
   - **no deadlock** and **no overrun**, for fixed-rate graphs;
   - a **worst-case length for every routine**;
   - a **reaction-time bound for every urgent reflex**.

   Programs that cannot be checked get a warning, not a false guarantee.
2. **Formal proofs of the fabric [NEW-FIELD].** On blocking subscriptions, no token is lost, duplicated or reordered. Every blocking subscriber of a multicast sees the same sequence. A tap never blocks a producer.
3. **Formal proofs of the reflex scheduler [NEW-FIELD].**
   - The ~7-clock pin-to-pin bound holds whenever the rule is the highest-priority rule ready.
   - The "pending predicate costs exactly +1 clock" rule holds.
   - The routine rotation gives each lane its slot unconditionally.
4. **Compiler and proof tied together [OURS].** For each shipped protocol program, the RTL is formally checked *with that program loaded* (program-specific bounded model checking). This confirms the compiler's static claims on the real hardware.
5. **Independent oracles, all in simulation [NEW-FIELD]:**
   - **sigrok** open-source protocol decoders run on every simulation waveform;
   - **real-world captures** from the public `sigrok-dumps` repository are replayed into our receivers;
   - **third-party RTL cores** act as the other device, for example an open-source I2C controller or an OpenCores CAN controller.
6. **Metamorphic tests [NEW-FIELD].** These check relations instead of exact answers:
   - transmit→receive loopback returns the same bytes;
   - doubling every timing parameter stretches the waveform exactly 2×;
   - swapping which lane runs which program changes nothing;
   - adding idle time between frames never changes decoded data.

   They catch bugs that the golden model and the RTL share.
7. **Table stakes [STANDARD]:**
   - a token-level golden model compared against the RTL cycle by cycle;
   - constrained-random and property-based fuzzing;
   - unit tests;
   - Tiny Tapeout gate-level tests (`gl_test`);
   - mutation testing (kill rate reported);
   - lint;
   - a bug ledger;
   - a claims-with-evidence table.

   Loom and TEMPO already have most of these, so we match them rather than claim them.

---

## 2. The competition and the platform

| Item | Value | Source |
|---|---|---|
| Must build | Open-source, general-purpose protocol emulator: a small processor for reading and writing pins, counting cycles and hitting timing precisely, with protocols in firmware | Jane Street post |
| Required protocols | UART, SPI, I2C | Jane Street post |
| Stretch goals | Low-speed USB, 10 Mbit Ethernet | Jane Street post |
| Also suggested | JTAG, SWD, PS/2, CAN | Jane Street post |
| Judging | "Unique functionality" and "novel approaches to design and verification methodologies"; formal, constrained-random and AI-assisted verification are welcomed | Jane Street post |
| Template | `TinyTapeout/ttihp-verilog-template`, branch **cmos5l** (cloned locally in WSL) | Jane Street post |
| Area | **6x4 tiles** (1289.28 × 710.64 µm; core ≈ 902K µm²). 8x4 is "being worked on" | Jane Street post; Loom's measurements |
| Process | IHP SG13CMOS5L 130 nm; routing layers up to Metal4 | Tiny Tapeout |
| Clock | 50 MHz sign-off default; pads specified to ~66 MHz with up to ~10 ns insertion delay | Tiny Tapeout docs, via Loom's facts file |
| Pins | `ui_in[7:0]` in, `uo_out[7:0]` out, `uio[7:0]` bidirectional (with `uio_oe`), plus `clk`, `rst_n`, `ena` | Template `project.v` |
| SRAM | IHP macros such as 512x16 (45.3K µm²) and 1024x16 (79.7K µm²); integrated on cmos5l by Loom | Loom `docs/tt_cmos5l_facts.md` |
| CI | Workflows `test`, `gds` (gds + precheck + gl_test + viewer → GitHub Pages), `docs`, `fpga` (manual, iCE40UP5K bitstream) | Template |
| CI limit | A 6x4 hardening takes ~4–5 h; GitHub kills jobs at 6 h; routing time grows sharply with congestion | Loom `docs/AREA.md` |
| Lab hardware | **None available.** Everything is verified in simulation; the FPGA workflow only builds a bitstream | Team constraint |

---

## 3. The concept in plain words

Most protocol processors are **one worker reading instructions from a notebook**, checking the pins over and over. TRIPWIRE is **a panel of alarm circuits connected by conveyor belts**:

- **Pin units** are exact timers at the wires.
- **Channels** are conveyor belts carrying small packets of data (tokens). One belt can feed several stations.
- **Lanes** are the decision makers. Each has 12 **reflexes** ("when this, do that"), all watching at once, which fire the instant their condition becomes true.
- **Routines** are the non-urgent chores (setup, bookkeeping, error reports), stored in the SRAM and run when a reflex asks.
- **Helper units** (CRC, pattern match, memory) are specialty stations on the belts.

Software decides which alarm watches what and where the belts go. The watching and the moving are done by dedicated circuits, all at the same time. That is why the reaction time is short and exactly the same every time.

---

## 4. Architecture

### 4.1 Block diagram

```
              host SPI (fixed pins) ─► host controller (load program, halt/step, read state, host FIFOs)
                                                   │
 ┌─────────────────────────── channel fabric (16-bit tokens + tag) ───────────────────────────┐
 │  producers:  pin RX ×6 · lane out ×(2×3) · CRC · match · memory · host-in                   │
 │  consumers:  pin TX ×6 · lane in  ×(2×3) · CRC · match · memory · host-out · capture        │
 │  each consumer port: 8-way select + read pointer + blocking/tap flag                        │
 └────────────────────────────────────────────────────────────────────────────────────────────┘
       ▲▼                     ▲▼                      ▲▼                         ▲▼
  ┌─────────┐   ┌──────────────────────────┐   ┌──────────────┐        ┌──────────────────────┐
  │ pin     │   │ lane 0..2                │   │ helper units │        │ SRAM 512x16 (or 1K)  │
  │ units×6 │   │ 12 reflex slots (latches)│   │ CRC, match   │        │ routines + data      │
  │ timed   │   │ 4 regs, 8 predicates     │   └──────────────┘        │ fixed 4-way rotation:│
  │ TX/RX   │   │ priority pick → ALU      │ ◄──── routine steps ──────│ L0, L1, L2, mem/host │
  └─────────┘   │ routine PC (interruptible)│                          └──────────────────────┘
      ▲▼        └──────────────────────────┘
  19 free pins (after host port), open-drain capable on uio
```

### 4.2 Tokens and channels
- **Token** = 16-bit data + a small **tag** (e.g. DATA, CTRL, EVENT, ERR; the width of 2–3 bits is decided in P1).
- **Channel** = a depth-1 register owned by its producer, plus a valid bit.
- **Consumer port** = a select register (8 allowed sources per port), a read flag, and a blocking/tap flag.
- **Multicast rule:** the producer's token is released when all *blocking* subscribers have taken it. Taps take it if they are ready, and otherwise increment a `DROPPED` counter.
- **Pin-receiver rule:** a pin never waits. If a blocking subscriber is full when a new token arrives, the token is lost and a sticky `OVERRUN` flag is set.

### 4.3 Lanes and reflexes
The full instruction set is in `ISA.md`.
- **State:** 4 × 16-bit registers, 4 host-loaded 16-bit constants (K0–K3), 8 predicate bits, 2 input ports, 2 output ports, a routine PC and a busy flag.
- **Reflex slot (52 bits, latch array, written only while halted):**
  - **Condition:**
    - STATE and flag mask/value;
    - optionally, a tag match and a `data[15]` match on the input the action reads;
    - an urgent flag.
    - Input-available, output-free and routine-idle checks are **implicit**: the hardware adds them from what the action uses.
  - **Action:** one operation.
    - Sources: a register, an input head (optionally removing it), zero or time; B is a register, an immediate or a constant.
    - Destination: a register or an output port.
    - A static STATE update, and a flag result written to one predicate.
- **Operations:** 16, shared with routines. `MOV ADD SUB AND OR XOR SHL SHR`, plus protocol-shaped ones:
  - `SHOR d=(a<<s)|b` (frame building)
  - `EXT` (bitfield extract)
  - `CMPM p=((a&mask)==val)` (compare into a predicate)
  - `LTU`, `PAR`, `MKCTL`, `CALL`
  - Every op can write a flag result (zero, or the compare result), so a counter decrements and tests in one action.
- **Scheduling:**
  - All 12 conditions are evaluated every clock, and a priority encoder picks one.
  - Static predicate updates apply at select time, so they are visible on the next clock.
  - Dynamic results (compares) mark their predicate *pending* for exactly 1 clock.
  - Result: **1 action per clock** (50 M/s), and +1 clock when a fresh compare is used immediately.
- **Reaction path, pin to pin:** synchronizer (2) → receive token (1) → channel (1) → select (1) → execute and enqueue (1) → pin unit acts (1) ≈ **7 clocks, 140 ns**.

### 4.4 Routines
- 16-bit instructions stored in SRAM. They use the same datapath and operations as reflexes, plus local branches, `DJNZ` with a static bound, and `RET`.
- **Fixed 4-way SRAM rotation:** lane 0 → lane 1 → lane 2 → memory unit/host. That gives 1 routine step per lane every 4 clocks (12.5 M steps/s).
- A routine cannot wait, since waiting belongs to reflexes. It is bounded, and its worst-case length is proven by the compiler.
- **Urgent reflexes pre-empt routines.** A waiting routine step loses EXEC to an urgent reflex and runs on the next free clock; non-urgent reflexes wait at most one clock behind a routine step. Routine timing is guaranteed only "if not pre-empted" (`ISA.md` §5.3).

### 4.5 Pin units (×6)
- Each can be attached to a small set of physical pins; open-drain mode is available on the `uio` pins.
- **Transmit commands:**
  - `LEVEL(v, delay)`, `AT(t)`
  - `SHIFT(n)`, using a fractional bit-period divider, or clocked by another pin's edges
  - `CLK(n)`, with an open-drain, clock-stretch-aware variant
  - `PULSE(n)`, pulse-width-coded bits for WS2812 and DShot
- **Receive modes:**
  - `SHIFT_RX` (start-edge triggered, auto re-arm)
  - sampling on another pin's edges
  - edge timestamps
  - **qualified edge events**, i.e. an edge on this pin, optionally only while that pin is at a level (edge timestamps, I2C START/STOP)
- A per-unit prescaler for slow protocols.

### 4.6 Helper units
- **CRC:** programmable polynomial, init and reflection, up to 16 bits. A 32-bit variant only if area allows.
- **Pattern matcher:** value/mask → MATCH/NOMATCH tag.
- **Memory unit:** takes address, write and read tokens, and is the SRAM's data port on the rotation.
- **Capture:** stores tap tokens with timestamps into a reserved SRAM region.

### 4.7 Host interface
- SPI slave on fixed pins, with an IRQ output. A proposal to verify: follow Loom's finding that `ui_in[4..6]` + `uo_out[7]` match the TT demo board RP2040's hardware SPI0.
- **Address spaces:**
  - control (run/halt per lane, step, IRQ);
  - reflex slot write;
  - SRAM (routines and data);
  - fabric select registers;
  - pin unit configuration;
  - host-in/host-out FIFOs;
  - debug readback (registers, predicates, channel valid bits, flags).
- The same host protocol drives the simulation testbench, and later the silicon.

### 4.8 Budget (estimates; confirm by synthesis)

| Configuration | Est. area incl. SRAM | Utilisation |
|---|---|---|
| **3 lanes × 12 reflex slots, 6 pin units, 8-way fabric, 512x16 SRAM** | ~482K µm² | **~53%** (recommended) |
| Same with 1024x16 SRAM (room for a 256-byte EEPROM image plus ~890 routine words) | ~517K µm² | ~57% |
| 3 lanes × 16 slots | ~519K µm² | ~58% |

Reference: Loom's README (checked 2026-09-23) reports 78.8% utilisation on 6x4 with its 512x16 SRAM, and 4–5 h gds runs. Jane Street's brief budgets "about 1K logic cells per tile" (~24K cells for 6x4). These estimates need checking against both at the R1 synthesis.

**Pin budget:** 24 pins minus 4 for the host and 1 for IRQ = **19 free** (5 input-only, 6 output-only, 8 bidirectional).

---

## 5. Programming model and toolchain

- **Source:** a small text language describing:
  - the **channel graph** (which producer feeds which consumers, blocking or tap);
  - each lane's **reflexes** (`when … do …`);
  - its **routines** (straight-line code);
  - **pin unit settings**.
- **Compiler** (Python) outputs:
  1. reflex slot images;
  2. routine code for SRAM;
  3. fabric select registers;
  4. pin configuration;
  5. a **report of static checks**: routine worst-case lengths, urgent-reflex reaction bounds, deadlock/overrun analysis for fixed-rate graphs, and slot and SRAM usage.
- **Golden model** (Python, token-level and cycle-accurate), written from the spec independently of the RTL.
- **Host library:** load, run, halt, step, read state; one API across the simulation and the silicon.
- **Protocol library:** one source file per protocol, each doubling as a test.

---

## 6. Protocol support

| Tier | Protocol | Hot slots (of 12) | Notes |
|---|---|---|---|
| **Required** | UART TX + RX | ~4 | Error reporting in a routine |
| | SPI controller | 3 | Received data routed straight to the host by the fabric |
| | I2C controller | ~7 | START/STOP/errors in routines; arbitration-loss detection from the multicast readback |
| **Core showcase** | I2C target (EEPROM emulation) | ~8 + memory unit | ACK in ~140 ns: fine at 400 kHz and 1 MHz |
| | SPI target (flash emulation) | ~8–10 + memory unit | ~2.5 MHz SCK, higher with fast-read dummy cycles |
| **Likely** | 1-Wire (incl. overdrive) | ~4 | |
| | PS/2 | 3 | |
| | WS2812 / SK6812 / DShot | 1–2 | `PULSE` mode |
| | JTAG, SWD | est. 4–8 | Clocked like SPI; not yet written out |
| | UART-based: MIDI, DMX512, LIN | | Firmware variants |
| **Stretch** | CAN (with arbitration) | ~10 bit lane + ~6 frame lane | 2 lanes; destuffed stream multicast to CRC and frame lane |
| **Not planned** | USB low-speed | | Needs a clock-recovering receive mode and ~3 lanes |
| | 10 Mbit Ethernet | | Too fast for the pads without extra hardware |

**Concurrency:** 3 lanes, and small protocols can share a lane. The 19 free pins are the real cap.

---

## 7. Verification plan

**Principle:** every claim in the README links to the check that proves it, and states that check's blind spot.

| Layer | What | Tools | Pass criterion |
|---|---|---|---|
| L0 static | Verilator lint, Yosys synthesis sanity, no unintended latches (latches only in slot arrays, waived) | Verilator, Yosys | Clean, waivers reviewed |
| L1 unit | Each block against Python references: ALU ops, CRC against a catalogue of standard CRCs, pin unit modes, channel handshakes, priority encoder | cocotb + pytest (+ Hypothesis) | All pass |
| L2 model lockstep | RTL against the golden model, cycle by cycle, on random programs and random stimuli | cocotb | Zero divergences over N million cycles; injected bugs caught |
| L3 protocol | Each protocol program against its own model, **and against sigrok decoders on the VCD** | cocotb + `sigrok-cli` | Decoded bytes equal the intended bytes |
| L3b independent peers | Third-party RTL as the other device (open-source I2C controller/target, OpenCores CAN); `sigrok-dumps` real captures replayed into our receivers | Icarus/Verilator co-simulation | Peers accept our traffic and we accept theirs |
| L4 metamorphic | Loopback identity, time scaling, lane permutation, idle insertion | cocotb | Relations hold |
| L5 formal (hardware) | Fabric: no loss, duplication or reordering; multicast consistency; taps never block. Scheduler: reaction bound, pending-bit rule, rotation fairness. Lane isolation. Host port safety. | SymbiYosys (smtbmc, abc pdr) | Proven, or bounded with the depth stated |
| L5b formal (program-specific) | The RTL with each shipped protocol program loaded: ACK deadline met, no overrun, framing properties on the pins | SymbiYosys | Matches the compiler's static report |
| L6 compiler checks | Static deadlock/overrun, routine bounds, reaction bounds; fuzzing the compiler against the model | Our compiler + model | Every shipped program checked |
| L7 test quality | Mutation testing of the RTL | mcy or our own script | Kill rate reported per block |
| L8 gate level | Tiny Tapeout `gl_test` runs the cocotb suite on the netlist; SDF-annotated gate-level simulation if artefacts allow | CI | Pass |

**Policies:**
- Model and RTL are written independently from the spec.
- `docs/BUGS.md` logs every bug: symptom, root cause, the layer that caught it, and the check that now covers it.
- `docs/CLAIMS.md` lists each claim with its evidence status.
- AI-assisted work is recorded, including which reviews were human.

---

## 8. CI: what makes each workflow green

| Workflow / job | Green when | Owner phase |
|---|---|---|
| `test` | The cocotb suite passes under Icarus; `test/Makefile` lists every source | P0 (placeholder), P2 onward |
| `gds` → `gds` | LibreLane hardens within 6 h; timing met at 50 MHz; SRAM macro config correct | P2 (first), P4 (final) |
| `gds` → `precheck` | Tiny Tapeout DRC, pins and power checks pass | P2, P4 |
| `gds` → `gl_test` | The same tests pass on the netlist (no X after reset, no `initial` dependence) | P2 onward |
| `gds` → `viewer` | Repo Settings → Pages → Source = **GitHub Actions**; the gds job passed | P0 (enable), P4 |
| `docs` | `info.yaml` valid, `docs/info.md` filled in | P0 (placeholder), P5 (final) |
| `fpga` (manual) | iCE40UP5K bitstream builds; needs an FPGA build parameter (fewer lanes/slots, SRAM mapped to FPGA block RAM) | P3 |

**Rules for CI:**
- Only run `gds` when `src/`, `info.yaml` or `macro/` changes.
- Make one hardware change per hardening run.
- Judge each change by the global-routing overflow, not by cell count.

---

## 9. Schedule and checklists

The dates avoid late-semester crunch: RTL freezes before finals week.

### P0: setup and decisions (Sep 23 → Oct 4)
- [ ] Set the project name in `info.yaml` (`tt_um_tripwire` top module) and the docs.
- [ ] Submit the Jane Street sign-up form; email asic-competition@janestreet.com about tile size (6x4 vs 8x4) and SRAM macro acceptance.
- [ ] Template repo (cmos5l branch) pushed to GitHub; Pages enabled (Source = GitHub Actions).
- [ ] Trivial design (e.g. a counter on `uo_out`) passes `test`, `gds`, `precheck`, `gl_test`, `viewer` and `docs`.
- [ ] Local WSL loop: OSS CAD Suite (Icarus, Verilator, Yosys, SymbiYosys), Python + cocotb, `sigrok-cli`.
- [ ] Assign roles: architecture/RTL, verification (does not write RTL), compiler/tools, physical/CI.
- [ ] `docs/DECISIONS.md` and `docs/BUGS.md` created.

### P1: spec, model and risk spikes (Oct 5 → Oct 18)
- [ ] `SPEC.md`: token format and tags, channel/fabric rules, reflex slot encoding, routine ISA, pin unit commands, host protocol, exact cycle timing (the contract for both RTL and model).
- [ ] Golden model v0 (token-level, cycle-accurate) from the spec.
- [ ] Compiler v0: parse the language → images; static checks for routine bounds and slot usage.
- [ ] UART, SPI and I2C (controller + target) written in the language and running on the model.
- [ ] **Risk spike R1:** synthesize one lane (slots + scheduler + ALU) and check the 50 MHz critical path.
- [ ] **Risk spike R2:** harden one lane with its latch slot array through the TT flow (precheck + gl_test).
- [ ] **Risk spike R3:** SRAM macro smoke hardening using the public cmos5l recipe (credit the source).

### P2: RTL core (Oct 19 → Nov 8)
- [ ] RTL: lane, fabric, pin units, helpers, SRAM rotation, host controller, top level with pin map.
- [ ] L1 unit tests and L2 lockstep against the model are green.
- [ ] UART/SPI/I2C pass L3 in RTL simulation, including sigrok decoding.
- [ ] First full `gds` hardening: record area, timing and routing overflow in `docs/AREA.md`.
- [ ] `gl_test` green.

### P3: showcase protocols and verification depth (Nov 9 → Nov 29)
- [ ] I2C target (EEPROM) and SPI target (flash) with the memory unit; 1-Wire, PS/2, WS2812/DShot.
- [ ] L3b: third-party RTL peers and `sigrok-dumps` replay in CI.
- [ ] L4 metamorphic tests.
- [ ] L5 formal: fabric properties, scheduler bound, rotation fairness, lane isolation.
- [ ] L6 compiler: deadlock/overrun analysis for fixed-rate graphs.
- [ ] FPGA build parameter; the `fpga` workflow goes green.

### P4: stretch and RTL freeze (Nov 30 → Dec 6)
- [ ] CAN across 2 lanes (only if P3 is fully green).
- [ ] L5b program-specific formal checks for the shipped protocols.
- [ ] **RTL freeze on Dec 6.** Final `gds` on the freeze commit; every workflow green.

### P5: evidence and docs (Dec 7 → Jan 4, reduced pace during finals and holidays)
- [ ] L7 mutation run; SDF gate-level run if possible.
- [ ] `VERIFICATION_REPORT.md`, `CLAIMS.md`, the complete `BUGS.md`.
- [ ] `docs/info.md` datasheet (pinout, how to use, host commands).
- [ ] README with the novelties, results table and honest limits.
- [ ] Demo material: waveforms, sigrok decodes, compiler reports.

### P6: submit (Jan 5 → Jan 11; buffer to Jan 18)
- [ ] A fresh clone builds everything green.
- [ ] Tag `v1.0`; submit through Jane Street's process.

---

## 10. Risks

| # | Risk | Mitigation / retire by |
|---|---|---|
| R1 | Firing every clock needs predicate forwarding; the critical path may not close at 50 MHz | Static/dynamic predicate split; synthesize one lane in P1; fallback: 1 action per 2 clocks (still 25 M/s) |
| R2 | Latch arrays in the TT cmos5l flow | PRISM precedent on IHP; harden one lane in P1; fallback: 8 flop slots per lane plus more routines |
| R3 | SRAM macro acceptance / precheck | Public cmos5l recipe; smoke run in P1; ask Jane Street/TT; fallback: small flop routine store |
| R4 | Fabric routing congestion (6 h CI limit) | 8-way select, depth-1 channels, local muxes; judge by routing overflow; drop to 2 lanes if needed |
| R5 | Program capacity for complex protocols | Routines in SRAM; host reload between phases; 1024x16 SRAM if area allows |
| R6 | Routines starved by urgent reflexes | Routine timing guaranteed only if not interrupted; compiler warns when a deadline depends on a routine |
| R7 | Toolchain effort (language + compiler + model) | Start in P1; keep the language minimal; programs double as tests |
| R8 | Closest competitor is PRISM (table-driven state machine + latch config) | Pitch the difference: predicated instructions with a datapath, multicast channel fabric, program-level static checks |
| R9 | No lab hardware | Independent oracles in simulation (sigrok, `sigrok-dumps`, third-party RTL, metamorphic); say plainly that everything is simulation-verified |

---

## 11. Positioning against the field

| Entry | Their core idea | Our difference |
|---|---|---|
| Loom | 4-thread barrel CPU, deadline timing, bit engines, strong verification | No program counter on the fast path; multicast fabric; program-level static checks |
| TEMPO (Dave Graham) | Time as an operand; timestamped pin ops; riscv-formal-style ISA proofs, mutation 98% | Timed pins are only our building block; our novelty is the triggered control plus the fabric |
| PRISM (Ken Pettit) | Table-driven 8-state machine + TinyQV RISC-V; latch config macros | Instructions with a datapath, not a state table; a channel network with multicast; compiler-proven bounds |
| core-asic | 2 PIO engines + sub-ns delay-line TDC/DTC | Different axis entirely |
| PIO clones (Metastable, BitLoom, Sophos, Cycle, and others) | RP2040-style state machines | Different execution model |

---

## 12. What we must NOT claim
- That we invented triggered instructions (ISCA 2013), timed I/O (XMOS, FlexPRET, TEMPO), or message passing.
- Zero latency. Say "fixed ~7 clocks, proven".
- That fuzzing *proves* anything. Fuzzing finds bugs; formal proves.
- Hardware tested against real devices. We have none: say "verified in simulation against independent decoders, captures and third-party RTL".
- USB or Ethernet support.
- "Formally verified" without naming the property and whether the proof is bounded or unbounded.

---

## 13. Open decisions (owner, due date)
1. Tile size 6x4 vs 8x4 (Jane Street reply, P0).
2. SRAM 512x16 vs 1024x16 (after the P1 risk spike).
3. Tag width, reflex slot encoding, routine ISA details (P1 spec).
4. 12 vs 16 slots per lane; 3 vs 2 lanes (after the first hardening).
5. Host pin map (confirm the demo board SPI pins, P1).
6. ~~RTL language: Verilog (default) vs Hardcaml for part of the toolchain (P0).~~ Resolved by D-021: the RTL is Verilog; Hardcaml is used for verification (`VERIFICATION.md` L9).

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **Lane** | One decision-making engine (reflex slots, registers, routine runner) |
| **Reflex** | A "when condition, do action" rule, checked by hardware every clock |
| **Routine** | Short non-urgent code in SRAM, started by a reflex |
| **Predicate** | A 1-bit state flag inside a lane, used in reflex conditions |
| **Token** | A 16-bit data packet plus a tag, moved over channels |
| **Channel / fabric** | The conveyor belts / the whole network of them |
| **Blocking / tap** | A subscriber the producer waits for / one that never slows anything |
| **Pin unit** | A timer-and-shifter block that drives or samples pins on exact clocks |
| **ACK** | "Acknowledge": the receiver's yes-I-got-it bit in I2C |
| **CRC** | Checksum used to detect transmission errors |
| **SRAM** | Dense on-chip memory block (a hard macro from IHP) |
| **Latch / flip-flop** | 1-bit storage cells; latches are about half the area |
| **Deterministic** | Always takes exactly the same time |
| **Formal verification** | Mathematically proving a property holds for all inputs |
| **Golden model** | A simple software version of the chip used as the reference |
| **gl_test** | Tiny Tapeout's test run on the synthesized gate-level netlist |