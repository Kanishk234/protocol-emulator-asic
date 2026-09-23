# TRIPWIRE: architecture

This document defines the TRIPWIRE hardware:
- what is new about it;
- the top-level structure;
- the data formats and the channel fabric;
- the lane datapath and its reflex instruction set;
- the routine instruction set;
- the pin units, helper units and host interface;
- timing, pin map and area budget.

It is the contract that the RTL and the golden model are both written from. Where a detail is not final it is marked **OPEN** and gets settled in the P1 spec freeze.

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

### 4.4 Release rule, stated precisely
`src.all_taken = AND over consumer ports p with (p.en && p.mode==blocking && p.sel==src) of (p.last_seq == src.seq)`

The producer's `valid` clears when `all_taken`. Throughput is one token per clock per producer.

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

### 5.2 Reflex slot encoding (~51 bits, stored in a latch array, written only while the lane is halted)

```
CONDITION (22 bits)
  [0]      V      slot valid
  [1]      U      urgent (may interrupt a routine; see 6.3)
  [2]      SE     state-match enable
  [6:3]    SV     required STATE value
  [10:7]   FM     flag mask   (over f3..f0)
  [14:11]  FV     flag value
  [16:15]  IN     00 none | 01 I0 available | 10 I1 available | 11 reserved
  [17]     TE     tag-match enable on the chosen input's head
  [19:18]  TAG    required tag
  [21:20]  OUT    00 none | 01 O0 free | 10 O1 free | 11 reserved
ACTION (29 bits)
  [25:22]  OP     operation (see 5.3)
  [28:26]  DST    0-3 r0-r3 | 4 O0 | 5 O1 | 6 none (flags only) | 7 CALL
  [31:29]  ASRC   0-3 r0-r3 | 4 I0 head | 5 I1 head | 6 zero | 7 global time (low 16)
  [32]     DQ     dequeue the input used in the condition
  [33]     BSEL   0: B = r[IMM[1:0]] | 1: B = IMM (zero-extended)
  [41:34]  IMM    8-bit immediate / sub-fields
  [42]     NSE    next-STATE enable (static update)
  [46:43]  NS     next STATE value
  [47]     DFE    dynamic-flag enable (compare result)
  [49:48]  DF     which flag f0-f2 receives the result
  [50]     OTAG   output token tag override: 0 = DATA, 1 = use IMM[7:6] as tag (CTRL/EVENT/ERR)
```

**Firing condition:**
`V && (!SE || STATE==SV) && ((FLAGS ^ FV) & FM)==0 && !(PEND & FM) && (IN==0 || (avail(IN) && (!TE || head.tag==TAG))) && (OUT==0 || free(OUT))`

**Priority:** the lowest slot index wins.

### 5.3 Operations (OP field, 4 bits)

| OP | Name | Effect | Used for |
|---|---|---|---|
| 0 | MOV | d = A | Forwarding tokens, loading registers |
| 1 | ADD | d = A + B | Counters, pointers |
| 2 | SUB | d = A − B | |
| 3 | AND | d = A & B | Masking |
| 4 | OR | d = A \| B | |
| 5 | XOR | d = A ^ B | Arbitration readback compare |
| 6 | SHL | d = A << B[3:0] | |
| 7 | SHR | d = A >> B[3:0] | |
| 8 | SHOR | d = (A << IMM[3:0]) \| r[IMM[5:4]] | Frame building (start/stop bits, ACK bit) in one action |
| 9 | EXT | d = (A >> IMM[3:0]) & mask(IMM[7:4]+1) | Pull a field out of a frame |
| 10 | CMPEQ | f[DF] = (A == B) | Address match, state checks |
| 11 | CMPM | f[DF] = ((A & r[IMM[1:0]]) == r[IMM[3:2]]) | Check several bits at once (start/stop/ACK) |
| 12 | PAR | f[DF] = XOR-reduce(A) | UART/PS/2 parity |
| 13 | TSTZ | f[DF] = (A & B) == 0 | Bit tests |
| 14 | MKCTL | d = {IMM[7:4], 0, A[10:0]}, tag CTRL | Pin commands whose argument comes from a register |
| 15 | CALL | start routine number IMM (entry-table lookup); set RB | Hand off to routines |

A output tag is DATA unless `OTAG` is set or OP = MKCTL. Compare ops normally use DST = 6 (none).

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

### 6.1 Routine instruction set (16-bit words in SRAM)

| Format | Bits | Instructions |
|---|---|---|
| R | `op[15:12] rd[11:10] ra[9:8] rb[7:6] -[5:0]` | MOV ADD SUB AND OR XOR SHL SHR (op 0–7) |
| I | `op[15:12] rd[11:10] imm[9:0]` | LDI (zero-extend 10-bit), ADDI (signed 10-bit), LDIH (r[15:10] = imm[5:0]) |
| B | `op[15:12] cond[11:9] rel[8:0]` | BF f / BNF f / BRA / DJNZ r (signed 9-bit offset) |
| M | `op[15:12] rd[11:10] ra[9:8] off[7:0]` | LD rd,[ra+off] / ST rd,[ra+off] (data region) |
| O | `op[15:12] port[11] tag[10:9] ra[8:7] -` | OUT port, ra, tag (enqueue a token; blocks if full) |
| S | `op[15:12] kind[11:10] val[3:0]` | SETST v, SETF f, CLRF f, RET |

**OPEN:** exact opcode assignment is settled in P1. Everything is generated from one ISA table (see VERIFICATION.md §4.1).

### 6.2 Execution
- **SRAM access is a fixed rotation:** cycle mod 4 = 0 → L0, 1 → L1, 2 → L2, 3 → MEM/CAPTURE/HOST.
- A lane with RB set fetches one routine word on its slot and executes it in its EXEC stage on a clock when no reflex fires. So a routine gets **1 step per 4 clocks** (12.5 M steps/s), or fewer if reflexes fire.
- `LD`/`ST` use the lane's next slot for the data access, so they cost 2 steps.
- **CALL** reads the routine's start address from an entry table in the first 32 SRAM words, taking one slot. It sets RB, and `RET` clears it.

### 6.3 Interruption and bounds
- A reflex with **U = 1** can fire while RB is set, and the routine simply continues at its next free step.
- A reflex with U = 0 can fire only when its condition holds; its condition may include f3 (RB) to wait until the routine is done.
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
| RXMODE | off, SHIFT_RX, LINKED_RX, EDGE_TS, COND_EDGE |
| PERIOD | Bit period in clocks, 16.8 fixed point (fractional divider) |
| PRESC | Tick prescaler for LEVEL delays (1–256 clocks per tick) |
| NBITS | Shift length, 1–16 |
| ORDER | LSB- or MSB-first |
| OD, IDLE | Open-drain enable, idle level |
| T0, T1 | PULSE high times (ticks) for bit 0 / bit 1 |
| LINKEDGE | For linked modes: rise, fall |
| SAMPLEOFS | For SHIFT_RX: sample position within a bit (fraction of PERIOD) |
| AUTOREARM | For SHIFT_RX: re-arm on the next start edge automatically |
| STRETCH | CLKGEN waits for the line to read high before timing the high phase |

### 7.3 TX half: tokens consumed
- **DATA token:** the payload for the configured TXMODE.
  - SHIFT sends NBITS of data at PERIOD, or on pin B's LINKEDGE if linked.
  - PULSE sends NBITS pulse-coded bits.
- **CTRL token:** `data[15:12]` is the op.

| Op | Name | Argument | Effect |
|---|---|---|---|
| 1 | LEVEL | [11] v, [10:0] delay (ticks) | Drive v at *cursor + delay* |
| 2 | OE | [11] oe, [10:0] delay | Change output enable at *cursor + delay* |
| 3 | CLK | [7:0] n | Generate n clock periods (CLKGEN mode) |
| 4 | GAP | [11:0] ticks | Advance the cursor (idle spacing) |
| 5 | SYNC | none | Set cursor := now (re-anchor to the present) |
| 6 | SETN | [4:0] n | Change NBITS for the next DATA token |

**Drift-free scheduling:** each TX half keeps a **cursor**, the scheduled time of its last action. Delays are relative to the cursor, not to when the token arrived, so a sequence of commands never accumulates error. If a token arrives after its computed time, it executes immediately and sets the sticky **LATE** flag. Lateness is detectable, never silent.

### 7.4 RX half: tokens produced

| RXMODE | Produces |
|---|---|
| SHIFT_RX | Waits for a start edge on pin A, samples NBITS at PERIOD (first sample at SAMPLEOFS), emits a DATA token; re-arms if AUTOREARM |
| LINKED_RX | Samples pin A on each LINKEDGE of pin B, emits a DATA token after NBITS |
| EDGE_TS | Emits an EVENT token per edge: data = {polarity, time[14:0]} |
| COND_EDGE | Emits EVENT tokens `START`/`STOP` when pin A changes while pin B is high (I2C). Combinable with LINKED_RX on the same unit. |

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
| Reflex slots, 3 × 12 × ~51 bits, latch arrays | ~1.8K latch bits (~80K µm²) |
| Fabric (16 producer registers, 17 ports, 8-way muxes) | ~0.5K flops + muxes |
| Pin units ×6 | ~0.55K flops |
| Helpers + host + time base | ~0.5K flops |
| SRAM 512x16 macro | 45.3K µm² |
| **Total** | **~480–520K µm², ~53–57% of the 6x4 core** |

The hard-deadline rule for physical design: the full gds run must finish routing within GitHub's 6 h. Judge every change by global-routing overflow.

---

## 13. Worked example: I2C target ACK, cycle by cycle

Setup:
- U0: pin A = SDA (`uio0`, open-drain), pin B = SCL (`uio1`); RXMODE = LINKED_RX (8 bits on SCL rise) + COND_EDGE; TX linked to SCL fall.
- L0.I0 ← U0.rx (blocking). L0.O0 → U0.tx.
- r1 = own address << 1. r2 = 0x00FE (address-bits mask), for comparing against the byte with its R/W bit masked off.

```
slot 0 (U): when I0 has EVENT(START)                  do STATE:=ADDR, DQ
slot 1 (U): when STATE==ADDR & I0 has DATA             do f0 := CMPM(I0.head, mask r2, val r1), DQ, STATE:=ACKQ
slot 2 (U): when STATE==ACKQ & f0==1 & O0 free          do O0 := {SETN 1}(CTRL) ; STATE:=ACK1
slot 3 (U): when STATE==ACK1 & O0 free                 do O0 := DATA 0 (1-bit shift of 0 at next SCL fall) ; CALL addr_ok
slot 4 (U): when STATE==ACKQ & f0==0                   do STATE:=IDLE      ; not us: stay released
...
```

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