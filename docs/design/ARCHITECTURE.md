# TRIPWIRE: architecture

This document defines the TRIPWIRE hardware:
- what is new about it;
- the top-level structure;
- the data formats and the channel fabric;
- the lane datapath and its reflex instruction set;
- the routine instruction set;
- the pin units, helper units and host interface;
- timing, pin map and area budget.

It is the contract that the RTL and the golden model are both written from. Where a detail is not final it is marked **OPEN** and gets settled in the P1 spec freeze. The lane instruction set (reflex slots, routines, operation table) is specified in `ISA.md`.

Companion documents: `OVERVIEW_TRIPWIRE.md` (the overview and schedule) and `VERIFICATION.md` (how all of this is checked).

---

## 1. Novelties in the architecture

| # | Feature | Status in the field | Why it matters |
|---|---|---|---|
| A1 | **Triggered execution.** Each lane has 12 *reflex* slots of the form "when condition, do one action". All conditions are evaluated by hardware every clock, and the highest-priority true slot fires. There is no program counter and no instruction fetch on the fast path. | New to the competition. Prior art: *Triggered Instructions*, Parashar et al., ISCA 2013 (spatial accelerators). | Fixed ~7-clock (~140 ns) pin-to-pin reaction, always the same, provable |
| A2 | **Multicast channel fabric.** All blocks exchange tokens over a small on-chip network. A producer can feed several consumers at once, each either *blocking* or *tap*. | New to the competition | One stream drives the protocol logic, CRC and capture at once, with zero instructions spent copying |
| A3 | **Reflexes + routines**, a two-tier program store. Urgent logic lives in latch-array slots; everything else runs as bounded routines from the SRAM, and urgent reflexes can interrupt them. | Our design | Fixed reaction time *and* hundreds of instructions of program space |
| A4 | **Determinism by construction.** Single clock domain. The SRAM is shared by a fixed rotation. Pin ownership is a per-pin register, so two drivers are impossible. Pin receivers never stall and have defined overrun behaviour. | Our design choices | Isolation between lanes is a structural fact that can be proven, not a programming convention |
| A5 | **Timed smart pin units** with drift-free relative scheduling and a LATE flag | Building block. Timed I/O exists in TEMPO, Loom, XMOS, FlexPRET. | Wire timing is independent of lane activity |
| A6 | **Helper units on the fabric**: CRC, pattern match, memory (device emulation), capture | Light, reconfigurable version of a systolic stage | Common protocol work without lane instructions |

---

## 2. Global parameters

| Parameter | Value | Note |
|---|---|---|
| Clock | 50 MHz, one domain | Host SCK is sampled, not used as a clock |
| Lanes | 3 (L0–L2) | Parameter; 2 is the fallback |
| Reflex slots per lane | 12 | Parameter; 8 is the flop fallback, 16 if area allows |
| Registers per lane | 4 × 16-bit (r0–r3) | |
| Predicates per lane | 8 bits: STATE[3:0] = p7..p4, FLAGS[3:0] = p3..p0 | f3 is the hardware routine-busy flag (read-only) |
| Lane ports | 2 inputs (I0, I1), 2 outputs (O0, O1) | |
| Token | 16-bit data + 2-bit tag | Tags: 00 DATA, 01 CTRL, 10 EVENT, 11 ERR |
| Pin units | 6 (U0–U5), each with a TX half and an RX half | |
| Helper units | CRC, MATCH, MEM, CAPTURE | |
| SRAM | IHP 512x16 macro (1024x16 optional) | Routines + data + capture ring |
| Global time | 16-bit free-running counter, +1 per clock | Wraps every 1.31 ms; pin units have prescalers for longer times |

---

## 3. Top-level structure

```
 ui_in/uio/uo_out pads
   │ 2-FF synchronisers                      pin ownership registers (one owner per output pin)
   ▼                                                           ▲
 ┌──────────────────────── PIN UNITS U0..U5 (TX half ◄ consumer port, RX half ► producer) ───────┐
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
          ▲▼                                   ▲▼                                   ▲▼
 ┌──────────────────────────────── CHANNEL FABRIC (tokens: 16b data + 2b tag) ──────────────────────┐
 │ producer registers:  U0..U5.rx · L0..L2.{O0,O1} · CRC · MATCH · MEM · HOST_IN        (16)        │
 │ consumer ports:      U0..U5.tx · L0..L2.{I0,I1} · CRC · MATCH · MEM · HOST_OUT · CAPTURE (17)   │
 │ each consumer port: select (≤8 legal sources) · enable · blocking/tap · last-seq bit             │
 └──────────────────────────────────────────────────────────────────────────────────────────────────┘
          ▲▼                          ▲▼                           ▲▼
   ┌──────────────┐        ┌───────────────────┐        ┌───────────────────────┐
   │ LANE L0..L2  │        │ HELPERS           │        │ SRAM 512x16            │
   │ 12 slots     │ ◄──────┤ CRC, MATCH, MEM,  │        │ rotation (clk mod 4):  │
   │ EVAL → EXEC  │ routine│ CAPTURE           │ ◄──────┤ 0:L0 1:L1 2:L2 3:MEM/  │
   │ r0-r3, p7-p0 │ steps  └───────────────────┘        │   CAPTURE/HOST         │
   └──────────────┘ ◄─────────────────────────────────── └───────────────────────┘
          ▲
   HOST CONTROLLER (SPI slave): load slots/SRAM/config, run/halt/step, debug readback, host FIFOs, IRQ
```

---

## 4. Tokens and the channel fabric

### 4.1 Token format

```
 17 16 | 15 ............................ 0
  tag  | data
  00 DATA   payload bytes/words
  01 CTRL   commands (pin-unit ops, helper ops)            data[15:12] = op, data[11:0] = argument
  10 EVENT  things that happened (START, STOP, edge + timestamp, MATCH index, CRC result)
  11 ERR    error reports (framing error, overrun, NACK, arbitration lost)
```

### 4.2 Producer register (one per producer)
- Holds `valid`, `tag`, `data` and a sequence bit `seq`. Depth 1.
- A producer may load a new token when `!valid`, or when every **blocking** subscriber has taken the current one. Loading toggles `seq`.
- Taps never hold a producer back.

### 4.3 Consumer port (one per consumer)
- Registers: `sel` (3 bits, indexing the port's legal-source list), `en`, `mode` (blocking/tap), `last_seq`.
- **Available** to the consumer when `en && src.valid && last_seq != src.seq`.
- **Taking** sets `last_seq = src.seq`.
- For a **tap**: if the producer loads a new token before the tap took the old one, the tap's `DROPPED` counter increments (8-bit, saturating).
- `accept` (4 bits, D-015): a tag mask. A token whose tag is not accepted is dropped at the port without reaching the consumer, so one producer can feed several consumers that each keep only their own kind of token (§14 F7).

### 4.4 Release rule, stated precisely
`src.all_taken = AND over consumer ports p with (p.en && p.mode==blocking && p.sel==src) of (p.last_seq == src.seq)`

When `all_taken`, the producer register is free for its next load. (The draft semantics in §14, rules F3–F6, make this exact. `valid` stays set, and a taken token is not seen again because `last_seq == seq`.)

**Throughput (OPEN, Q7):** the original target was one token per clock per producer. That needs a combinational path from a consumer's take back to the producer's load, and lane-to-lane channels would turn that path into a loop. The model therefore uses registered release (§14 F3). Measured cost: a lane can load the same output port at most once every 3 clocks, and HOST_IN can deliver to a lane at most once every 2 clocks. `docs/reports/ARCH_EXPLORATION.md` checks whether any protocol needs more.

### 4.5 Pin receivers never wait
If a pin RX half completes a token while its producer register still holds an untaken token for a blocking subscriber:
- the **new token is discarded**;
- the unit's sticky `OVERRUN` flag is set;
- an ERR token is optionally emitted when the channel next frees (configurable).

The old token is kept so that sequence order is never violated.

### 4.6 Legal sources (connectivity table)

This is an initial proposal, **OPEN**, to be tuned in P1 for routing. Each consumer port selects among at most 8 sources, and the multiplexer sits next to the consumer.

| Consumer | Legal sources (≤8) |
|---|---|
| Lk.I0 | U0–U5.rx, HOST_IN, MATCH |
| Lk.I1 | the other two lanes' O0/O1 (4), CRC, MEM, HOST_IN, MATCH |
| Un.tx | L0–L2.O0/O1 (6), HOST_IN, MEM |
| CRC.in / MATCH.in | U0–U5.rx, Lk.O1 of 2 lanes (a set chosen per build) |
| MEM.in | L0–L2.O1, HOST_IN |
| HOST_OUT | L0–L2.O0, U0–U3.rx, MEM |
| CAPTURE | U0–U5.rx, L0.O0, HOST_IN |

---

## 5. Lanes

### 5.1 Lane state

| Item | Width | Notes |
|---|---|---|
| r0–r3 | 4 × 16 | General registers |
| STATE (p7..p4) | 4 | Current protocol state, 16 states |
| FLAGS (p3..p0) | 4 | f0–f2 are compare results and user flags; f3 = RB (routine busy, read-only) |
| PEND | 4 | Per-flag "result pending" bits (see 5.4) |
| I0/I1 head latch | 2 × 18 | Token captured at select time |
| O0/O1 | producer registers | Owned by the lane (see §4) |
| RPC, RRET | 9 + 9 | Routine PC and saved PC for interruption |
| RUN, HALT, STEP | control | Set from the host |

| K0–K3 | 4 × 16 | Per-lane constants, host-written while halted, read-only to programs (`ISA.md` §2) |

### 5.2 Reflex slot encoding and 5.3 operations

Moved to **`ISA.md`** (§3 operation table, §4 reflex slots), which is now the single description of what a lane executes. Summary: 52-bit slots in a latch array, written only while the lane is halted. Channel readiness is implicit in the operands. The lowest-index ready slot fires, and urgent slots pre-empt a waiting routine step. There are 16 ops, shared with routines, and every op can write a flag result.

### 5.4 The two-stage lane pipeline

```
clock n   EVAL : evaluate 12 conditions → priority encode → selected slot s
                 apply s's static updates now: STATE := NS (if NSE), dequeue the input (DQ), reserve the output
                 latch the chosen input head into the operand latch
                 if DFE: PEND[DF] := 1
clock n+1 EXEC : read s's action fields → ALU → write r[d] / load O0|O1 / write f[DF] and clear PEND[DF]
```

- **Throughput:** one action per clock per lane.
- **Pending rule:** a slot whose flag mask covers a pending flag cannot fire that clock. So using a fresh compare result costs exactly one extra clock, a static, compiler-known delay.
- **Output reservation:** an output reserved at EVAL counts as "not free" for the next EVAL until EXEC loads it. This prevents two back-to-back enqueues overflowing a depth-1 register.

### 5.5 Reaction latency, pin to pin (the headline number)

| Step | Clocks |
|---|---|
| Pad → 2-FF synchroniser | 2 |
| RX half detects the sample/edge, completes the token, loads its producer register | 1 |
| Lane EVAL sees `avail` and selects the slot | 1 |
| Lane EXEC loads the output register | 1 |
| Pin unit TX half accepts the token | 1 |
| TX half updates the pad output register | 1 |
| **Total** | **7 clocks = 140 ns at 50 MHz** |

This holds when the reacting slot is the highest-priority ready slot in its lane and its output is free. Both conditions can be checked statically per program and proved formally.

---

## 6. Routines

### 6.1 Routine instruction set

Moved to **`ISA.md`** §5. Routines use 16-bit words in SRAM with the same operation table as reflexes, plus `LDI/LDIH`, `BR` (on the routine-local `RZ` bit), `DJNZ`, `LD/ST`, `OUT` and `SYS` (`SETST`, `SETF`, `CLRF`, `TSTF`, `CPYF`, `GETT`, `GETK`, `RET`). §6.2–6.3 below describe execution; `ISA.md` §5.3 defines exactly how routine steps and reflexes share EXEC.

### 6.2 Execution
- **SRAM access is a fixed rotation:** cycle mod 4 = 0 → L0, 1 → L1, 2 → L2, 3 → MEM/CAPTURE/HOST.
- A lane with RB set fetches one routine word on its slot and executes it in its EXEC stage on a clock when no reflex fires. So a routine gets **1 step per 4 clocks** (12.5 M steps/s), or fewer if reflexes fire.
- `LD`/`ST` use the lane's next slot for the data access, so they cost 2 steps.
- **CALL** reads the routine's start address from an entry table in the first 32 SRAM words, taking one slot. It sets RB, and `RET` clears it.

### 6.3 Interruption and bounds
- Every reflex stays eligible while RB is set. `U` only decides who wins EXEC when a routine step is waiting: an urgent reflex beats it, and a non-urgent one waits one clock (`ISA.md` §5.3). A reflex that must wait for the routine to finish includes f3 (RB) = 0 in its condition.
- **Routines never wait on pins.** `OUT` may stall while its output register is full, and the compiler reports these stalls separately in the routine's bound.
- Loops need a static bound (`DJNZ` with a compile-time-known count), so every routine has a compiler-computed worst-case step count.

---

## 7. Pin units (U0–U5)

### 7.1 Attachment
- Each unit has **pin A** (drive and/or sample) and **pin B** (link or condition input), chosen from the 19 free pins (§10).
- **Output ownership:** every drivable pad has a 3-bit `owner` register (U0–U5 or none). Only the owner's TX half can drive it, so drive conflicts are impossible by construction.
- Open-drain mode is available on the `uio` pads: writing 1 releases (OE = 0), writing 0 drives low.

### 7.2 Configuration (host-written while halted)

| Field | Meaning |
|---|---|
| TXMODE | LEVEL-only, SHIFT, CLKGEN, PULSE |
| RXMODE | off, SHIFT_RX (timed from a start edge), LINKED_RX (sampled on an edge of pin B) |
| EV_EDGE, EV_QUAL, EV_RESET | Event generator (D-013): EVENT on rise/fall/both edges of pin A, optionally only while pin B is at level EV_QUAL (stable for 2 samples); EV_RESET restarts word framing. Covers edge timestamps and I2C START/STOP with one mechanism |
| PERIOD | Bit period in clocks, 16.8 fixed point (fractional divider) |
| PRESC | Tick prescaler for LEVEL delays (1–256 clocks per tick) |
| NBITS | Shift length, 1–16 |
| ORDER | LSB- or MSB-first |
| OD, IDLE | Open-drain enable, idle level |
| T0, T1 | PULSE high times (ticks) for bit 0 / bit 1 |
| RX_EDGE, TX_EDGE | For linked modes, separately for each half: the edge of pin B on which RX samples and TX changes pin A (rise, fall). I2C samples on SCL rise and drives on SCL fall, so one shared field is not enough (D-010) |
| RX_NBITS, RX_NBITS2 | RX word length, if different from TX NBITS. RX_NBITS2 ≠ 0: words alternate between RX_NBITS and RX_NBITS2 bits (two-phase framing, e.g. I2C 8 + 1), right-aligned in `data` (D-013, replaces D-010's RX_TAIL) |
| RX_ECHO | 0: RX words sampled while this unit's own TX was shifting are dropped (echo suppression on half-duplex lines: I2C, 1-Wire, SWD, half-duplex UART). 1: keep them (readback for collision checks) (D-013) |
| TX_LENTOK | DATA tokens carry their bit count: `data[15:12]` = NBITS − 1, payload `data[11:0]`. Variable-length shifts need no SETN (D-013) |
| SAMPLEOFS | For SHIFT_RX: sample position within a bit (fraction of PERIOD) |
| AUTOREARM | For SHIFT_RX: re-arm on the next start edge automatically |
| STRETCH | CLKGEN waits for the line to read high before timing the high phase |
| TX_PRELOAD | Linked shift: bit 0 goes out at once when idle, the rest on TX_EDGE (SPI CPHA = 0) (D-011, §14 P9) |

### 7.3 TX half: tokens consumed
- **DATA token:** the payload for the configured TXMODE.
  - SHIFT sends NBITS of data at PERIOD, or on pin B's TX_EDGE if linked.
  - PULSE sends NBITS pulse-coded bits.
- **CTRL token:** `data[15:12]` is the op.

| Op | Name | Argument | Effect |
|---|---|---|---|
| 1 | LEVEL | [11] v, [10:0] delay (ticks) | Drive v at *cursor + delay* |
| 2 | OE | [11] oe, [10:0] delay | Change output enable at *cursor + delay* |
| 3 | CLK | [7:0] n | Generate n clock periods (CLKGEN mode): each period IDLE for PERIOD/2, then ACTIVE for PERIOD/2; with STRETCH, each IDLE half is timed from when pin A actually reads IDLE (§14 P11) |
| 4 | GAP | [11:0] ticks | Advance the cursor (idle spacing) |
| 5 | SYNC | none | Set cursor := now (re-anchor to the present) |
| 6 | SETN | [4:0] n | Change NBITS for the next DATA token |
| 7 | WAIT | [0] edge (1 = rise) | Stop taking tokens until pin B shows this edge, then restart the timeline there (cursor := that edge). Arm a WAIT before the edge it waits for (D-016, §14 P16) |

**Drift-free scheduling:** each TX half keeps a **cursor**, the scheduled time of its last action. Delays are relative to the cursor, not to when the token arrived, so a sequence of commands never accumulates error. If a token arrives after its computed time, it executes immediately and sets the sticky **LATE** flag. Lateness is detectable, never silent.

### 7.4 RX half: tokens produced

| RXMODE | Produces |
|---|---|
| SHIFT_RX | Waits for a start edge on pin A, samples NBITS at PERIOD (first sample at SAMPLEOFS), emits a DATA token; re-arms if AUTOREARM |
| LINKED_RX | Samples pin A on each RX_EDGE of pin B, emits a DATA token per word (RX_NBITS, or alternating with RX_NBITS2) |
| Event generator (any RXMODE) | EVENT `{new level of A, time[14:0]}` on EV_EDGE of pin A, qualified by EV_QUAL. Edge timestamps: EV_EDGE = both. I2C START/STOP: EV_EDGE = both, EV_QUAL = 1 (SCL high), EV_RESET; START is `data[15]` = 0 (SDA fell), STOP `data[15]` = 1 |

EVENT tokens from pin units always carry the new level of pin A in `data[15]`, so reflex conditions can test it directly (`ISA.md` §4.2, `HS` = 0). Short words keep their low bit in `data[0]` (`HS` = 1), for example the I2C ACK/NACK bit.

---

## 8. Helper units

| Unit | Input tokens | Output tokens | Configuration |
|---|---|---|---|
| **CRC** | DATA (width set by config, 1–16 bits); CTRL RESET; CTRL READ | EVENT with the CRC value | poly (16), init (16), refin, refout, xorout. CRC-32 only if area allows (OPEN) |
| **MATCH** | DATA | EVENT: index of the first matching entry (0–3) or NOMATCH; optionally forwards the original token | 4 × (value, mask) |
| **MEM** | CTRL ADDR a; DATA (write at addr++); CTRL READ n | n DATA tokens from addr++ | Base/limit of the data region; uses rotation slot 3 |
| **CAPTURE** | Any tap token | None. Writes {time, tag, data} into a ring in SRAM; the host reads it back | Ring base/length; shares slot 3 (MEM has priority, and capture counts its drops) |

---

## 9. Host interface

- **Physical:** SPI slave, mode 0. Proposed pins: `ui_in[4]` CS_n, `ui_in[5]` SCK, `ui_in[6]` MOSI, `uo_out[7]` MISO, `uo_out[6]` IRQ (**OPEN**: confirm against the TT demo board's RP2040 SPI0 mapping). SCK ≤ clk/8.
- **Transaction:** `CMD[7:0]` (bit 7 = write), `ADDR[15:0]`, then 16-bit data words with auto-increment. Reads insert one dummy byte.

| Address range | Space |
|---|---|
| 0x0000–0x00FF | Control/status: RUN/HALT per lane, STEP, IRQ enable/status, sticky flags (OVERRUN, DROPPED, LATE, ERR counts), ID/version |
| 0x1000–0x1FFF | Reflex slots: `lane[9:8] slot[7:4] word[1:0]` (4 × 16-bit words per slot) |
| 0x2000–0x20FF | Fabric consumer port registers (sel, en, mode) |
| 0x3000–0x30FF | Pin unit configuration + pin owner registers |
| 0x4000–0x40FF | Helper configuration (CRC, MATCH, MEM, CAPTURE) |
| 0x5000–0x50FF | Debug readback: r0–r3, STATE, FLAGS, PEND, RPC, per-channel valid/seq, head tokens |
| 0x6000 / 0x6001 | HOST_IN push / HOST_OUT pop (+ status) |
| 0x8000–0x81FF | SRAM words (routines, entry table, data, capture ring) |

**Debug:**
- Any lane can be halted, single-stepped (exactly one EVAL/EXEC) and inspected.
- Slots, SRAM and configuration are writable only while the affected lane is halted.
- **IRQ** = OR of enabled status bits.

---

## 10. Pin map (proposal, OPEN)

| Pads | Use |
|---|---|
| `ui_in[4..6]`, `uo_out[7]` | Host SPI |
| `uo_out[6]` | IRQ |
| `ui_in[0..3]`, `ui_in[7]` | 5 input-only pins (sample-only for pin units) |
| `uo_out[0..5]` | 6 output-only pins |
| `uio[0..7]` | 8 bidirectional pins (open-drain capable) |

**19 free pins** for protocols, plus the IRQ output.

---

## 11. Timing and critical paths (to check at synthesis)

| Path | Contents | Concern |
|---|---|---|
| EVAL | 12 × condition (≈20-input AND) → 12-bit priority encoder → next-STATE mux | Main lane path; fallback: fire every other clock |
| EXEC | Operand mux → 16-bit ALU / shifter → register/output write | Standard |
| Fabric release | OR over ≤17 consumer "taken" terms per producer | Keep select decode local |
| Pin unit | 16.8 accumulator compare, cursor compare | Similar to Loom's timer path, which closed at 50 MHz |
| SRAM | Macro clock-to-Q into the routine decode | Loom's macro-launched path had +2 ns at the slow corner |

---

## 12. Area budget (estimates; replace with synthesis numbers)

| Block | Estimate |
|---|---|
| 3 lanes (registers, predicates, pipeline, routine control) | ~0.4K flops |
| Reflex slots, 3 × 12 × 52 bits, plus 3 × 4 × 16 constant (K) bits, latch arrays | ~2.1K latch bits (~90K µm²) |
| Fabric (16 producer registers, 17 ports, 8-way muxes) | ~0.5K flops + muxes |
| Pin units ×6 | ~0.55K flops |
| Helpers + host + time base | ~0.5K flops |
| SRAM 512x16 macro | 45.3K µm² |
| **Total** | **~480–520K µm², ~53–57% of the 6x4 core** |

The hard-deadline rule for physical design: the full gds run must finish routing within GitHub's 6 h. Judge every change by global-routing overflow.

---

## 13. Worked example: I2C target ACK, cycle by cycle

Setup:
- U0: pin A = SDA (`uio0`, open-drain), pin B = SCL (`uio1`); RXMODE = LINKED_RX (8 + 1 bits on SCL rise) + qualified events (START/STOP); TX linked to SCL fall.
- L0.I0 ← U0.rx (blocking). L0.O0 → U0.tx.
- r1 = own address << 1. r2 = 0x00FE (address-bits mask), for comparing against the byte with its R/W bit masked off.

The slot program for this example, in the current ISA, is in `ISA.md` §7.2. In outline: START (slot 0) → address byte compared with `CMPM` into f0 (slot 1) → if it matches, `SETN 1` then a single DATA 0 bit to U0.tx (slots 2–3). The timeline below is unchanged by the ISA revision.

**Timeline:** the 8th SCL rising edge at the pad is t = 0.

| Clock | Event |
|---|---|
| t = 2 | Synchronised |
| t = 3 | U0.rx loads DATA(addr byte) |
| t = 4 | EVAL picks slot 1 |
| t = 5 | EXEC writes f0 (pending cleared) |
| t = 6 | EVAL picks slot 2 |
| t = 7 | EXEC enqueues SETN |
| t = 8 | EVAL picks slot 3 |
| t = 9 | EXEC enqueues DATA 0 |
| t = 10 | U0.tx armed |

SDA is driven low at the next SCL falling edge.

**Worst case ≈ 10 clocks (200 ns) from the address's last bit to armed.** The SCL high time left before the fall is ≥ 600 ns (400 kHz) or ≥ 260 ns (1 MHz Fm+), so there is margin at both speeds.

**Improvement noted for P1:** preload SETN during the address byte to save 2 clocks. This is also an example of the kind of bound the compiler reports.
---

## 14. Cycle-exact semantics (DRAFT, from the phase 1 model)

This section is the text that both `tools/tripsim` and the RTL implement. It is a **draft**. Each rule was fixed while writing the model, and each is open to change at the spec freeze. The rule numbers are referenced from the model's source code.

**Conventions:**
- *Clock n* is a cycle.
- *Edge n* is the rising edge that ends clock n.
- All decisions in clock n read registered state as it was at the start of clock n. Their effects become visible in clock n+1.

### Fabric
- **F1.** A consumer port sees a token when `en && src.valid && last_seq != src.seq`.
- **F2.** Taking a token sets `last_seq := src.seq` at the edge.
- **F3.** A producer is **free** in clock n when `!valid`, or when every enabled blocking subscriber has `last_seq == seq` at the start of clock n. Takes made in clock n do not count; there is no combinational path from consumers back to producers.
- **F4.** At an edge, takes are applied first and loads second (`seq` toggles, `valid := 1`). A tap that had the old token available and did not take it counts a drop (8-bit, saturating). **The drop counts as a take** (`last_seq := old seq`), so a tap never aliases after missing two tokens (BUGS #2).
- **F5.** Enabling or re-pointing a port sets `last_seq := src.seq`, so a newly enabled port never sees a stale token.
- **F6.** `valid` stays set until the next load.

### Lanes
- **L1.** EVAL runs every clock (every 2nd clock in the R1 fallback, `fire_period = 2`).
- **L2.** Selection order is given in `ISA.md` §4.3: urgent ready slots, then a waiting routine step, then other ready slots, each group lowest index first.
- **L3.** EXEC in clock n+1 executes the action selected at EVAL in clock n:
  - registers and K are read in EXEC;
  - the input head token and global time are latched at EVAL.
- **L4.** Static updates of the selected slot are applied at edge n: `STATE := NS`, dequeue (the take), output reservation, and `PEND[DF] := 1`.
- **L5.** EXEC writes are applied at edge n+1: `r[d]`, the output load (which also clears that output's reservation), and `f[DF]` (which also clears `PEND[DF]`).
- **L6.** `CALL` sets RB, and requests the entry-table read, at its EVAL edge (not at EXEC). A second CALL slot therefore sees RB = 1 on the very next clock.
- **L7.** An output is free for EVAL when it is not reserved and its producer is free (F3).

### Routines
- **R1.** SRAM rotation: `cycle mod 4` = 0, 1, 2 → lanes L0, L1, L2; 3 → MEM/CAPTURE/HOST. The SRAM read data is registered, so a word read on slot k is usable from clock k+1.
- **R2.** On its slot, a lane fetches `SRAM[RPC]` into RIR only when RB = 1, RIR is empty, no routine step is waiting to execute, and no data access is pending. This guarantees RPC is final before the fetch.
- **R3.** A pending data access (the entry-table read after CALL, or an LD/ST) uses the lane's slot before any fetch.
  - `LD` returns its data as a second routine step, which competes for EXEC like any step.
  - `ST` completes on the slot.
- **R4.** If a reflex's static `NS` and a routine `SETST` land on the same edge, the reflex update wins.

### Pins
- **P1.** Pad inputs pass through 2-FF synchronisers: the value sampled in clock n is the pad value of clock n−2.
- **P2.** An RX half samples in clock n and loads its producer at edge n. If the producer is not free, the new token is discarded and `OVERRUN` is set.
- **P3.** A TX half takes a token in clock n only when all its pending pad actions fall on edges ≤ n+1. The earliest edge a newly taken token can act on is n+1, so a pad output changes at the earliest in clock n+2.
- **P4.** The TX cursor counts 1/256 clocks.
  - `LEVEL`/`OE` act at `cursor + d·PRESC`. If that is earlier than the earliest edge, they act at the earliest edge, and `LATE` is set if `d > 0`.
  - `SYNC` sets `cursor :=` the earliest edge.
  - A DATA shift starts at `max(cursor, earliest)` and never sets `LATE`.
  - Bit i changes the pad at edge `(start + i·PERIOD) >> 8`. After the last bit the pad returns to IDLE, unless the next shift's first bit lands on the same edge.
- **P5.** `SHIFT_RX` shifts raw bits, including start and stop bits, first sample in bit 0 (LSB order). The start edge is the first synchronised sample that differs from IDLE; sample i is taken in clock `t0 + (SAMPLEOFS·PERIOD + i·PERIOD) >> 8`.

With these rules, the §5.5 path is exactly 7 clocks. The model measures it (`tools/tripsim/tests/test_pins.py::test_pin_to_pin_reaction_is_seven_clocks`).

Pin rules added with the I2C modes:
- **P6.** A linked TX shift changes pin A at the edge of the clock in which the synchronised pin B shows TX_EDGE, which is 3 clocks after the pad edge. The TX half takes a new DATA token as soon as the previous shift has put out all its bits. The new shift's first bit then replaces the pending return-to-IDLE on the next TX_EDGE, so consecutive bytes have no gap.
- **P7.** Pin B may be a `uo` output pad (for example, SPI data linked to our own SCK). The unit then sees the driven value directly, without a synchroniser.
- **P8.** Event generator (D-013): an EVENT `{new level of A, time[14:0]}` is emitted when the synchronised pin A shows EV_EDGE, and, if EV_QUAL is set, pin B was at EV_QUAL in both this clock and the previous one. It uses this clock's RX load, so a sample due in the same clock is skipped. With EV_RESET it restarts word framing (phase 0, no bits).

Measured with these rules: the I2C target kernel queues its ACK 7 clocks after the 8th SCL rise, and SDA goes low 3 clocks after the SCL fall. It works for SCL high times ≥ 6 clocks (`tools/kernels/tests/test_i2c_target.py`). This is on an ideal bus in simulation; no rise times are modelled.

Pin rules added with the SPI modes (D-011):
- **P9.** Linked TX with TX_PRELOAD: if the unit is idle when it takes a DATA token, bit 0 goes out at the earliest edge (P3), and the remaining bits on each TX_EDGE. If the previous shift is still waiting for its final TX_EDGE, that edge carries bit 0 instead. This is continuous clocking, and it is how consecutive SPI mode-0 bytes join without a gap.
- **P10.** (Superseded by §14 F7, D-015: tag filtering moved from pin units to every fabric consumer port.)
- **P11.** CLKGEN, `CLK n` (D-016): n periods, each **IDLE for PERIOD/2, then ACTIVE for PERIOD/2**, starting from `max(cursor, earliest)`. The leading IDLE half gives SPI data setup before the first edge and I2C START hold (tHD;STA). Without STRETCH, the IDLE half after each ACTIVE half is timed from the release edge. With STRETCH, it is timed from the first clock in which the synchronised pin A reads IDLE: another device holding the line extends the phase. That costs up to 3 clocks per period (synchroniser + register). After the burst, `cursor` = the time of the final release (or of the line reading IDLE). A `CLK` token taken while a burst runs extends it seamlessly; other tokens wait for the burst to end.
- **P12.** In LEVEL mode, a DATA or EVENT token drives `data[0]` at `max(cursor, earliest)`.

Measured with these rules: the SPI controller kernel works in mode 0 up to SCK = 16.7 MHz (3 clocks per period). MISO passes through the 2-clock input synchroniser, which is what fails at 25 MHz. It takes about 38 clocks per byte at 12.5 MHz, against 32 for the bits alone.

Pin rules added with the generalized RX/TX primitives (D-013):
- **P13.** RX word framing: bits accumulate into a word of RX_NBITS bits (or, with RX_NBITS2 ≠ 0, alternately RX_NBITS then RX_NBITS2). The word is emitted right-aligned (LSB order: first bit in `data[0]`; MSB order: last bit in `data[0]`). A word is *tainted* if any of its samples was taken while a shifted bit from this unit's own TX was on pin A (from its first bit until its return to IDLE; D-016). A queued shift that has not started, LEVEL commands and released lines do not taint. With RX_ECHO = 0, tainted words are dropped instead of emitted, but framing still advances.
- **P14.** TX_LENTOK: a DATA token shifts `data[15:12] + 1` bits taken from `data[11:0]`, in ORDER. SETN is not needed, and payloads are limited to 12 bits.
- **P15.** Pin C (D-014): a unit is *selected* while its synchronised pin C equals C_ACTIVE (always, if no pin C).
  - While deselected, RX framing is held in reset, and no LINKED_RX/SHIFT_RX samples are taken.
  - In the clock pin C becomes inactive, a linked TX shift in progress is aborted: its remaining bits are dropped and pin A returns to IDLE.
  - With C_OE, pin A's output enable is on only while selected, taking effect one clock after the synchronised change (3 clocks after the pad edge).
  - Tokens may still be taken while deselected, so a preload can prepare the first bit before selection.
  - With EV_PIN = C, the event generator watches pin C: EVENT `data[15]` = new level of C.
- **P16.** WAIT (D-016): the TX half takes no further tokens until the synchronised pin B shows the given edge; in that clock, `cursor := earliest`. A WAIT that is taken after its edge has passed waits for the next one, so firmware must arm it first (as the I2C controller does: SCL's WAIT for the START edge before SDA falls).

Fabric rule added (D-015):
- **F7.** Each consumer port has a 4-bit `accept` tag mask. A token that is available to the port (F1) but whose tag is not accepted is not visible to the consumer, and is dropped at the edge of the clock it is available in (`last_seq := seq`), exactly as if it had been taken. So a filtered subscriber never delays the producer.

Measured with these rules: the I2C controller kernel runs 100 kHz / 400 kHz / 1 MHz with and without clock stretching, meeting tLOW/tHIGH ≥ PERIOD/2 on the bus. Stretch awareness adds 3 clocks to each high phase (943 kHz at a nominal 1 MHz), and the SPI controller's limit is 12.5 MHz with a symmetric clock (§ exploration report).
