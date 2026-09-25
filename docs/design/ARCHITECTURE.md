# TRIPWIRE: architecture

This document defines the TRIPWIRE hardware:
- what is new about it;
- the top-level structure;
- the data formats and the channel fabric;
- the lane datapath and its reflex instruction set;
- the routine instruction set;
- the pin units, helper units and host interface;
- timing, pin map and area budget.

It is the contract that the RTL and the golden model are both written from. The phase 1 OPEN items were closed by DECISIONS D-029 (after the model measurements); any new open point is marked **OPEN** and needs a DECISIONS entry to close. The lane instruction set (reflex slots, routines, operation table) is specified in `ISA.md`.

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
| Helper units | None in phase 2 (CRC, MATCH, MEM, CAPTURE deferred, §8) | D-029 |
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
 │ producer registers:  U0..U5.rx · L0..L2.{O0,O1} · HOST_IN                            (13)        │
 │ consumer ports:      U0..U5.tx · L0..L2.{I0,I1} · HOST_OUT                           (13)       │
 │ each consumer port: 4-bit select (≤9 legal sources, §4.6) · enable · blocking/tap · last-seq     │
 └──────────────────────────────────────────────────────────────────────────────────────────────────┘
          ▲▼                          ▲▼                           ▲▼
   ┌──────────────┐        ┌───────────────────┐        ┌───────────────────────┐
   │ LANE L0..L2  │        │ HELPERS           │        │ SRAM 512x16            │
   │ 12 slots     │ ◄──────┤ (deferred, §8)    │        │ rotation (clk mod 4):  │
   │ EVAL → EXEC  │ routine│                   │ ◄──────┤ 0:L0 1:L1 2:L2 3:HOST  │
   │ r0-r3, p7-p0 │ steps  └───────────────────┘        │                        │
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
- Registers: `sel` (4 bits, indexing the port's legal-source list, §4.6), `en`, `mode` (blocking/tap), `last_seq`.
- **Available** to the consumer when `en && src.valid && last_seq != src.seq`.
- **Taking** sets `last_seq = src.seq`.
- For a **tap**: if the producer loads a new token before the tap took the old one, the tap's `DROPPED` counter increments (8-bit, saturating).
- `accept` (4 bits, D-015): a tag mask. A token whose tag is not accepted is dropped at the port without reaching the consumer, so one producer can feed several consumers that each keep only their own kind of token (§14 F7).

### 4.4 Release rule, stated precisely
`src.all_taken = AND over consumer ports p with (p.en && p.mode==blocking && p.sel==src) of (p.last_seq == src.seq)`

When `all_taken`, the producer register is free for its next load. (The draft semantics in §14, rules F3–F6, make this exact. `valid` stays set, and a taken token is not seen again because `last_seq == seq`.)

**Throughput (Q7, closed by D-029):** release is registered (§14 F3). A same-clock release would need a combinational path from a consumer's take back to the producer's load, and lane-to-lane channels would turn that path into a loop. Cost: a lane can load the same output port at most once every 3 clocks, and HOST_IN can deliver to a lane at most once every 2 clocks. The densest stream in any program is one token per 32 clocks (`docs/reports/ARCH_EXPLORATION.md`), so producers stay depth 1.

### 4.5 Pin receivers never wait
If a pin RX half completes a token while its producer register still holds an untaken token for a blocking subscriber:
- the **new token is discarded**;
- the unit's sticky `OVERRUN` flag is set (host-visible).

A firmware-visible overrun token was dropped for phase 2 (D-035 O); it can return with its own entry if a program needs it.

The old token is kept so that sequence order is never violated.

### 4.6 Legal sources (connectivity table)

Each consumer port selects among at most 16 sources with its 4-bit `sel`; the multiplexer sits next to the consumer. The table comes from what the 20 programs in `programs/` use (D-029) and is symmetric across lanes and units, so tripc can place a program on any lane or unit. `Lk.I1` has 9 sources (the 6 units, the host, and the neighbouring lanes, for the two-lane CAN and LIN programs). The other ports have at most 8. tripc rejects a `connect` that is not in this table. The helper units of §8 are not in phase 2, so they have no sources here.

<!-- GENERATED:legal_sources -->
<!-- GENERATED by tools/gen/gen.py from spec/tripwire.yaml. DO NOT EDIT. Edit spec/tripwire.yaml. -->
| Consumer | Legal sources, in `sel` order (4-bit `sel`) | Count |
|---|---|---|
| L0.I0 | 0 U0.rx, 1 U1.rx, 2 U2.rx, 3 U3.rx, 4 U4.rx, 5 U5.rx, 6 HOST_IN, 7 L2.O1 | 8 |
| L1.I0 | 0 U0.rx, 1 U1.rx, 2 U2.rx, 3 U3.rx, 4 U4.rx, 5 U5.rx, 6 HOST_IN, 7 L0.O1 | 8 |
| L2.I0 | 0 U0.rx, 1 U1.rx, 2 U2.rx, 3 U3.rx, 4 U4.rx, 5 U5.rx, 6 HOST_IN, 7 L1.O1 | 8 |
| L0.I1 | 0 U0.rx, 1 U1.rx, 2 U2.rx, 3 U3.rx, 4 U4.rx, 5 U5.rx, 6 HOST_IN, 7 L1.O0, 8 L2.O1 | 9 |
| L1.I1 | 0 U0.rx, 1 U1.rx, 2 U2.rx, 3 U3.rx, 4 U4.rx, 5 U5.rx, 6 HOST_IN, 7 L2.O0, 8 L0.O1 | 9 |
| L2.I1 | 0 U0.rx, 1 U1.rx, 2 U2.rx, 3 U3.rx, 4 U4.rx, 5 U5.rx, 6 HOST_IN, 7 L0.O0, 8 L1.O1 | 9 |
| U0.tx | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 HOST_IN | 7 |
| U1.tx | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 HOST_IN | 7 |
| U2.tx | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 HOST_IN | 7 |
| U3.tx | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 HOST_IN | 7 |
| U4.tx | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 HOST_IN | 7 |
| U5.tx | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 HOST_IN | 7 |
| HOST_OUT | 0 L0.O0, 1 L1.O0, 2 L2.O0, 3 L0.O1, 4 L1.O1, 5 L2.O1, 6 U0.rx, 7 U1.rx | 8 |
<!-- /GENERATED:legal_sources -->

---

## 5. Lanes

### 5.1 Lane state

| Item | Width | Notes |
|---|---|---|
| r0–r3 | 4 × 16 | General registers |
| STATE (p7..p4) | 4 | Current protocol state, 16 states |
| FLAGS (p3..p0) | 4 | f0–f2 are compare results and user flags; f3 = RB (routine busy, read-only) |
| PEND | 3 | Per-flag "result pending" bits for f0–f2 (f3 = RB has none; `ISA.md` §4.4) |
| I0/I1 head latch | 2 × 18 | Token captured at select time |
| O0/O1 | producer registers | Owned by the lane (see §4) |
| RPC, RIR | 9 (10 with 1K SRAM) + 16 | Routine PC and fetched-instruction register (`ISA.md` §2) |
| RUN, HALT, STEP | control | Set from the host (§14 H2) |
| K0–K3 | 4 × 16 | Per-lane constants, host-written while halted, read-only to programs (`ISA.md` §2) |

### 5.2 Reflex slot encoding and 5.3 operations

Moved to **`ISA.md`** (§3 operation table, §4 reflex slots), which is now the single description of what a lane executes. Summary: 53-bit slots in a latch array, written only while the lane is halted. Channel readiness is implicit in the operands. The lowest-index ready slot fires, and urgent slots pre-empt a waiting routine step. There are 16 ops, shared with routines, and every op can write a flag result.

### 5.4 The two-stage lane pipeline

```
clock n   EVAL : evaluate 12 conditions → priority encode → selected slot s
                 apply s's static updates now: STATE := NS (if NSE), dequeue the input (DQ), reserve the output
                 latch the chosen input head into the operand latch
                 if DFE and DF != 3: PEND[DF] := 1
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
- **SRAM access is a fixed rotation:** cycle mod 4 = 0 → L0, 1 → L1, 2 → L2, 3 → HOST (and MEM/CAPTURE if they return, §8).
- A lane with RB set fetches one routine word on its slot and executes it in its EXEC stage on a clock when no reflex fires. So a routine gets **1 step per 4 clocks** (12.5 M steps/s), or fewer if reflexes fire.
- `LD` uses the lane's next slot for the data access and returns its data as a second step, so it costs 2 steps. `ST` costs 1 step plus the slot (§14 R3).
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

Each unit has a block of configuration registers in the host space (§9), written while the lanes are halted (§14 H1). The layout is generated from `spec/tripwire.yaml` (`pin_config`, D-036). Times are exact 16.8 fixed-point clock counts. The SHIFT_RX / BITSYNC sample point is stored as an offset in 1/256 clocks, not as a fraction of PERIOD, so its rounding is fixed by the host (P5). What each setting does is in §14 (P-rules) and in the DECISIONS entry that introduced it (D-010, D-011, D-013, D-014, D-016, D-019, D-020, D-023 to D-027). The model runs every configuration through this encoding (`tools/tripsim/pinregs.py`), so it only uses values the registers can hold.

<!-- GENERATED:pin_config -->
<!-- GENERATED by tools/gen/gen.py from spec/tripwire.yaml. DO NOT EDIT. Edit spec/tripwire.yaml. -->
Unit u's block: `0x3000 + u·0x20`; output owners: `0x30c0 + (pad − 8)`, `[2:0]` = unit, 7 = none.

| Word | Bits | Field | Encoding | Meaning |
|---|---|---|---|---|
| 0 | [2:0] | TXMODE | 0 level, 1 shift, 2 clkgen, 3 pulse, 4 bitsync | TX mode |
| 0 | [4:3] | RXMODE | 0 off, 1 shift_rx, 2 linked_rx, 3 bitsync | RX mode (bitsync with txmode bitsync) |
| 0 | [5] | ORDER | 0 lsb, 1 msb | bit order of shifted words |
| 0 | [6] | OD | 0/1 | open drain on pin A: 1 releases, 0 drives low |
| 0 | [7] | IDLE | value | idle level of pin A (BITSYNC: the recessive level) |
| 0 | [8] | AUTOREARM | 0/1 | SHIFT_RX re-arms after each word |
| 0 | [9] | RX_ECHO | 0/1 | keep RX words sampled while our own TX shifted (0: drop them) |
| 0 | [10] | TX_LENTOK | 0/1 | DATA carries its length: data[15:12] = n - 1 |
| 0 | [11] | TX_PRELOAD | 0/1 | linked TX: bit 0 at once when idle (SPI CPHA = 0) |
| 0 | [12] | STRETCH | 0/1 | CLKGEN waits for the line to read IDLE |
| 0 | [13] | NRZI | 0/1 | BITSYNC NRZI line coding |
| 0 | [14] | OE_AUTO | 0/1 | BITSYNC: drive the pads only while sending |
| 1 | [4:0] | PIN_A | pad number, 31 = none | drive and/or sample pad |
| 1 | [9:5] | PIN_B | pad number, 31 = none | link / condition pad |
| 1 | [10] | RX_EDGE | 0 rise, 1 fall | LINKED_RX samples on this edge of pin B |
| 1 | [12:11] | TX_EDGE | 0 none, 1 rise, 2 fall | linked TX shifts on this edge of pin B (none = timed) |
| 2 | [4:0] | PIN_C | pad number, 31 = none | select / frame pad |
| 2 | [5] | C_ACTIVE | value | pin C level that selects the unit |
| 2 | [6] | C_OE | 0/1 | drive pin A only while selected |
| 2 | [11:7] | PIN_S | pad number, 31 = none | sense pad, read instead of pin A |
| 3 | [4:0] | PIN_N | pad number, 31 = none | complement output of pin A |
| 3 | [5] | EV_PIN | 0 a, 1 c | event source pin |
| 3 | [7:6] | EV_EDGE | 0 none, 1 rise, 2 fall, 3 both | event on this edge |
| 3 | [9:8] | EV_QUAL | 0 none, 2 0, 3 1 | only while pin B is at this level (2 samples) |
| 3 | [10] | EV_RESET | 0/1 | an event restarts RX word framing |
| 4 | [15:0] + 5[7:0] | PERIOD | 16.8 clocks | bit period, 16.8 clocks, 1.0 to < 65536 |
| 5 | [15:8] | PRESC | value − 1 | clocks per tick, 1..256 |
| 6 | [15:0] + 7[7:0] | SAMPLEOFS | 16.8 clocks from the bit start | sample point after the bit start / start edge, 16.8 clocks |
| 7 | [11:8] | NBITS | value − 1 | TX shift length, 1..16 |
| 8 | [4:0] | RX_NBITS | value | RX word length, 1..16 (0 = NBITS) |
| 8 | [9:5] | RX_NBITS2 | value | two-phase framing second length, 0 = off |
| 9 | [11:0] | SYM0_T1 | value | bit 0: first level, ticks |
| 9 | [12] | SYM0_FIRST | value | bit 0: first level |
| 10 | [11:0] | SYM0_T2 | value | bit 0: second level, ticks |
| 11 | [11:0] | SYM1_T1 | value | bit 1: first level, ticks |
| 11 | [12] | SYM1_FIRST | value | bit 1: first level |
| 12 | [11:0] | SYM1_T2 | value | bit 1: second level, ticks |
| 13 | [15:0] + 14[7:0] | CARRIER | 16.8 clocks | carrier period, 16.8 clocks (0 = off) |
| 15 | [15:0] + 16[7:0] | SJW | 16.8 clocks | max resync step, 16.8 clocks (0 = hard sync only) |
| 16 | [12:8] | IDLE_BITS | value | recessive samples that make the bus idle, 1..31 |
| 16 | [13] | RESYNC | 0 dom, 1 both | resync on recessive-to-dominant edges only, or both |
| 16 | [15:14] | DELIM | 0 none, 1 flag, 2 se0 | frame delimiter |
| 17 | [3:0] | STUFF_N | value | stuff after n equal bits, 0 = off |
| 17 | [5:4] | STUFF_LVL | 0 none, 2 0, 3 1 | stuff only runs of this level |
| 17 | [10:6] | CRC_WIDTH | value | CRC width, 0 = none, 1..16 |
| 17 | [15:11] | CRC_SKIP | value | RX CRC starts after this many frame bits |
| 18 | [15:0] | CRC_POLY | value | CRC polynomial (MSB-first LFSR) |
| 19 | [15:0] | CRC_INIT | value | CRC register at frame start |
| 20 | [15:0] | CRC_RES | value | expected RX CRC register after the frame |
| 21 | [15:0] | CRC_XOR | value | XOR-ed into the TX CRC when appended |
<!-- /GENERATED:pin_config -->

### 7.3 TX half: tokens consumed
- **DATA token:** the payload for the configured TXMODE.
  - SHIFT sends NBITS of data at PERIOD, or on pin B's TX_EDGE if linked.
  - PULSE sends NBITS bits, each as its two-phase symbol, then returns to IDLE (§14 P17).
- **CTRL token:** `data[15:12]` is the op.

<!-- GENERATED:pin_commands -->
<!-- GENERATED by tools/gen/gen.py from spec/tripwire.yaml. DO NOT EDIT. Edit spec/tripwire.yaml. -->
| Op | Name | Argument | Effect |
|---|---|---|---|
| 1 | LEVEL | [11] v, [10:0] delay (ticks) | drive v at cursor + delay (LATE if already past and delay > 0) |
| 2 | OE | [11] oe, [10:0] delay | change output enable at cursor + delay |
| 3 | CLK | [7:0] n | CLKGEN: n periods, each IDLE half then ACTIVE half; STRETCH waits for the line |
| 4 | GAP | [11:0] ticks | advance the cursor (idle spacing) |
| 5 | SYNC | none | cursor := earliest (re-anchor to the present); BITSYNC: the next bit starts a frame at bus idle, and re-arms TX after a readback abort |
| 6 | SETN | [5] rx, [4:0] n | rx = 0: TX NBITS for the following DATA tokens; rx = 1: RX word length, and RX framing restarts (1..16) |
| 7 | WAIT | [1] sample point, [0] edge (1 = rise) | take no tokens until pin B shows the edge (or, with [1] in BITSYNC, until the next sample point); cursor := that time |
| 8 | SAMPLE | [11:0] delay (ticks) | at cursor + delay, sample pin A into the RX word framing; cursor := that time |
| 9 | FRAME | [11] next frame, [10:0] n | BITSYNC RX: the frame (in progress, or the next one with [11]) has n destuffed bits; then stuffing stops, the CRC is checked and the last word is flushed. LATE if none is in progress or it is already at or past n. An RX command: never waits behind TX data |
| 10 | LINE | [11:8] SE0 bits - 1, [6] reset TX CRC, [4] SE0, [3] append CRC, [2] stuff, [1:0] readback | BITSYNC TX, in stream order: [4] ends the frame with SE0 (pin A and pin N low) for n bits, then idle for 1 bit, then releases; readback 0 off / 1 arbitration (stop quietly on a mismatch) / 2 expect an override (report; error if nobody drove the other level) / 3 strict (a mismatch is a bit error); stuffing on/off; reset the TX CRC; then optionally shift out the TX CRC XOR CRC_XOR |
| 11 | JAM | [11:8] n-1, [7:6] d, [5] level, [4] on error, [2] TX on, [1] TX off, [0] disarm (with [4]) | BITSYNC: drive level for n bits, bypassing the TX queue. [4]=0: after d more sample points (a response: skipped in a frame this unit transmits); [4]=1: armed, fires from the next bit after the next detected error (stuff error, bit error, missing override). [1]/[2] (alone): TX off/on switch (off = listen-only): while off nothing is driven and a frame's SYNC is refused with EVENT 0xC001 |
<!-- /GENERATED:pin_commands -->

**Drift-free scheduling:** each TX half keeps a **cursor**, the scheduled time of its last action. Delays are relative to the cursor, not to when the token arrived, so a sequence of commands never accumulates error. If a token arrives after its computed time, it executes immediately and sets the sticky **LATE** flag. Lateness is detectable, never silent.

### 7.4 RX half: tokens produced

| RXMODE | Produces |
|---|---|
| SHIFT_RX | Waits for a start edge on pin A, samples NBITS at PERIOD (first sample at SAMPLEOFS), emits a DATA token; re-arms if AUTOREARM |
| LINKED_RX | Samples pin A on each RX_EDGE of pin B, emits a DATA token per word (RX_NBITS, or alternating with RX_NBITS2) |
| Event generator (any RXMODE) | EVENT `{new level of A, time[14:0]}` on EV_EDGE of pin A, qualified by EV_QUAL. Edge timestamps: EV_EDGE = both. I2C START/STOP: EV_EDGE = both, EV_QUAL = 1 (SCL high), EV_RESET; START is `data[15]` = 0 (SDA fell), STOP `data[15]` = 1 |

EVENT tokens from pin units always carry the new level of pin A in `data[15]`, so reflex conditions can test it directly (`ISA.md` §4.2, `HS` = 0). Short words keep their low bit in `data[0]` (`HS` = 1), for example the I2C ACK/NACK bit.

---

## 8. Helper units (deferred, D-029)

None of the helper units below is in the phase 2 RTL: no program in `programs/` needed one. CRC is covered by BITSYNC for serial streams and by table routines for byte checksums (SMBus PEC, LIN); MATCH by `CMPM` in slots; MEM by routines with `ld`/`st` and tripc `table`s. Any of them can return in phase 4 with its own DECISIONS entry if a showcase needs it and the area allows (MEM is the likeliest, for SPI flash / EEPROM emulation). CRC-32 is dropped with the CRC helper. The descriptions are kept as the starting point:

| Unit | Input tokens | Output tokens | Configuration |
|---|---|---|---|
| **CRC** | DATA (width set by config, 1–16 bits); CTRL RESET; CTRL READ | EVENT with the CRC value | poly (16), init (16), refin, refout, xorout |
| **MATCH** | DATA | EVENT: index of the first matching entry (0–3) or NOMATCH; optionally forwards the original token | 4 × (value, mask) |
| **MEM** | CTRL ADDR a; DATA (write at addr++); CTRL READ n | n DATA tokens from addr++ | Base/limit of the data region; uses rotation slot 3 |
| **CAPTURE** | Any tap token | None. Writes {time, tag, data} into a ring in SRAM; the host reads it back | Ring base/length; shares slot 3 (MEM has priority, and capture counts its drops) |

---

## 9. Host interface

- **Physical:** SPI slave, mode 0. Pins (D-029): `ui_in[4]` CS_n, `ui_in[5]` SCK, `ui_in[6]` MOSI, `uo_out[3]` MISO, `uo_out[6]` IRQ. On the TT demo board (RP2350) these are GPIO21 SPI0 CSn, GPIO22 SPI0 SCK, GPIO23 SPI0 TX and GPIO36 SPI0 RX (RP2350 datasheet, Table 645), so the board's hardware SPI0 drives the host link. SCK ≤ clk/8.
- **Transaction:** `CMD[7:0]` (bit 7 = write), `ADDR[15:0]`, then 16-bit data words with auto-increment. Reads insert one dummy byte.

| Address range | Space |
|---|---|
| 0x0000–0x00FF | Control/status: RUN/HALT per lane, STEP, IRQ enable/status, sticky flags (OVERRUN, DROPPED, LATE, ERR counts), ID/version |
| 0x1000–0x1FFF | Reflex slots: `lane[9:8] slot[7:4] word[1:0]` (4 × 16-bit words per slot); slot index 12, words 0–3 = K0–K3 (§14 H1) |
| 0x2000–0x20FF | Fabric consumer port registers (sel, en, mode) |
| 0x3000–0x30FF | Pin unit configuration, `0x3000 + u·0x20` (22 words used, §7.2), and output owners at `0x30C0 + (pad − 8)` |
| 0x4000–0x40FF | Reserved (helper configuration, if a helper returns; §8) |
| 0x5000–0x50FF | Lane registers and debug, `0x5000 + lane·0x20`: +0..+3 r0–r3 and +4 STATE (read any time, **writable while the lane is halted**, D-035 E2); read-only FLAGS, PEND, RPC, per-channel valid/seq, head tokens |
| 0x6000 / 0x6001 | HOST_IN push / HOST_OUT pop (+ status) |
| 0x8000–0x81FF | SRAM words (routines, entry table, data, capture ring) |

**Debug:**
- Any lane can be halted, single-stepped (exactly one EVAL/EXEC) and inspected.
- Slots, SRAM and configuration are writable only while the affected lane is halted.
- **IRQ** = OR of enabled status bits.

---

## 10. Pin map (D-029)

| Pads | Use |
|---|---|
| `ui_in[4..6]`, `uo_out[3]` | Host SPI (CS_n, SCK, MOSI, MISO) |
| `uo_out[6]` | IRQ |
| `ui_in[0..3]`, `ui_in[7]` | 5 input-only pins (sample-only for pin units) |
| `uo_out[0..2]`, `uo_out[4..5]`, `uo_out[7]` | 6 output-only pins |
| `uio[0..7]` | 8 bidirectional pins (open-drain capable) |

**19 free pins** for protocols, plus the IRQ output. The pad numbering and the host pads are in `spec/tripwire.yaml` (`pads`).

---

## 11. Timing and critical paths (to check at synthesis)

| Path | Contents | Concern |
|---|---|---|
| EVAL | 12 × condition (≈20-input AND) → 12-bit priority encoder → next-STATE mux | Main lane path; fallback: fire every other clock |
| EXEC | Operand mux → 16-bit ALU / shifter → register/output write | Standard |
| Fabric release | OR over ≤13 consumer "taken" terms per producer | Keep select decode local |
| Pin unit | 16.8 accumulator compare, cursor compare | Similar to Loom's timer path, which closed at 50 MHz |
| SRAM | Macro clock-to-Q into the routine decode | Loom's macro-launched path had +2 ns at the slow corner |

---

## 12. Area budget (estimates; replace with synthesis numbers)

| Block | Estimate |
|---|---|
| 3 lanes (registers, predicates, pipeline, routine control) | ~0.4K flops |
| Reflex slots, 3 × 12 × 53 bits, plus 3 × 4 × 16 constant (K) bits, latch arrays | ~2.1K latch bits (~90K µm²) |
| Fabric (13 producer registers, 13 ports, 7–9-way muxes, §4.6) | ~0.5K flops + muxes |
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

## 14. Cycle-exact semantics (from the phase 1 model)

This section is the text that both `tools/tripsim` and the RTL implement. Each rule was fixed while writing the model; rules L8–L11, R5–R6 and H1 answer the gaps G1–G8 found by writing the R1 lane RTL from these documents alone (`docs/reports/R1_LANE_TIMING.md` §6, D-033). A change to any rule needs a DECISIONS entry. The rule numbers are referenced from the model's source code.

**Conventions:**
- *Clock n* is a cycle.
- *Edge n* is the rising edge that ends clock n.
- All decisions in clock n read registered state as it was at the start of clock n. Their effects become visible in clock n+1.

### Fabric
- **F1.** A consumer port sees a token when `en && src.valid && last_seq != src.seq`, and its tag is in the port's `accept` mask (F7).
- **F2.** Taking a token sets `last_seq := src.seq` at the edge.
- **F3.** A producer is **free** in clock n when `!valid`, or when every enabled blocking subscriber has `last_seq == seq` at the start of clock n. Takes made in clock n do not count; there is no combinational path from consumers back to producers.
- **F4.** At an edge, takes are applied first and loads second (`seq` toggles, `valid := 1`). A tap that had the old token available and did not take it counts a drop (8-bit, saturating). **The drop counts as a take** (`last_seq := old seq`), so a tap never aliases after missing two tokens (BUGS #2).
- **F5.** Enabling or re-pointing a port sets `last_seq := src.seq`, so a newly enabled port never sees a stale token.
- **F6.** `valid` stays set until the next load.

### Lanes
- **L1.** EVAL runs every clock. (The model's `fire_period = 2` R1 fallback is a model-only experiment; D-030 chose firing every clock, so the RTL has no fallback.)
- **L2.** Selection order is given in `ISA.md` §4.3: urgent ready slots, then a waiting routine step, then other ready slots, each group lowest index first.
- **L3.** EXEC in clock n+1 executes the action selected at EVAL in clock n:
  - registers and K are read in EXEC;
  - the input head token and global time are latched at EVAL.
- **L4.** Static updates of the selected slot are applied at edge n: `STATE := NS`, dequeue (the take), output reservation, and `PEND[DF] := 1`.
- **L5.** EXEC writes are applied at edge n+1: `r[d]`, the output load (which also clears that output's reservation), and `f[DF]` (which also clears `PEND[DF]`).
- **L6.** `CALL` sets RB, and requests the entry-table read, at its EVAL edge (not at EXEC). A second CALL slot therefore sees RB = 1 on the very next clock.
- **L7.** An output is free for EVAL when it is not reserved and its producer is free (F3).
- **L8.** Operand B (G1): `BSEL = reg` reads `r[IMM[1:0]]`, `BSEL = k` reads `K[IMM[1:0]]`, `BSEL = imm` is `IMM`. `KT` keeps the head tag latched at EVAL only when `ASRC` is I0 or I1; otherwise `KT` is ignored and `OT` gives the tag. `MKCTL` always emits CTRL (G6).
- **L9.** If EXEC clears `PEND[x]` (writing `f[x]`) on the same edge that EVAL sets it for another slot, the set wins (G4).
- **L10.** `CALL` writes nothing at EXEC: no register, output or flag. It ignores `DST`, so it reserves no output and does not wait for one; `DFE` is ignored. Writes to f3 (RB) from a slot (`DF = 3`) or from `SETF`/`CLRF`/`CPYF` with arg 3 have no effect (G6).
- **L11.** Routine steps use the same pipeline as slots (G2): a step selected at EVAL in clock n executes in clock n+1, and its writes land at edge n+1.
- **L12.** Reserved codes have defined behaviour, so model and RTL agree on any bit pattern (D-035 A): `BSEL = 3` means imm; `DST = 7` means none; routine op 14 (CALL) is a NOP that writes neither rd nor RZ; `BR` conditions 3–7 are never taken; `SYS` kinds 9–15 are NOPs. tripc never emits them.

### Routines
- **R1.** SRAM rotation: `cycle` is the global time counter (0 at reset); `cycle mod 4` = 0, 1, 2 → lanes L0, L1, L2; 3 → HOST (and MEM/CAPTURE if they return, §8). The SRAM read data is registered, so a word read on slot k is usable from clock k+1.
- **R2.** On its slot, a lane fetches `SRAM[RPC]` into RIR only when RB = 1, RIR is empty, no routine step is waiting to execute, and no data access is pending. This guarantees RPC is final before the fetch.
- **R3.** A pending data access (the entry-table read after CALL, or an LD/ST) uses the lane's slot before any fetch.
  - `LD` returns its data as a second routine step, which competes for EXEC like any step.
  - The `LD`/`ST` address and the `ST` data are computed at the step's EXEC and held until the slot. `GETT` returns the time latched at the step's EVAL (as `ASRC = time` does for slots). Every SRAM address (RPC, `LD`/`ST`, the entry table) is taken modulo the SRAM size.
  - `ST` completes on the slot.
- **R4.** If a reflex's static `NS` and a routine `SETST` land on the same edge, the reflex update wins.
- **R5.** A waiting `OUT` step whose output is not free (L7) is not a candidate. It does not hold back non-urgent slots; it waits until the output frees (G3). When selected, it reserves the output at edge n like a slot.
- **R6.** `DJNZ` leaves `RZ` unchanged; its branch goes straight to RPC at EXEC. Only ALU steps and `TSTF` write `RZ` (G5).

### Reset and loading
- **H1.** After reset every lane is halted (RUN = 0). Flops (registers r0–r3, STATE, flags, PEND, RB, RIR state, producers, ports) reset to 0. Slot and K latches have no reset, so slot contents (including `V`) and K0–K3 are undefined. Before setting RUN the host writes all 12 slots and K0–K3 of a lane (52 words: unused slots with `V = 0`), and any nonzero initial r0–r3 or STATE through the lane register block (§9) (G7, D-035 E1/E2). `tripc.load` does this.
- **H2.** When RUN drops, EVAL stops from the next clock; an action already selected still executes in the next clock. The lane's routine fetches and data accesses stop (its rotation slot goes unused), while the fabric, pin units and host FIFOs keep running. STEP on a halted lane runs exactly one EVAL (and, if that clock is the lane's rotation slot, its SRAM access), then the selected action's EXEC in the next clock (D-035 D).

### Pins
- **P1.** Pad inputs pass through 2-FF synchronisers: the value sampled in clock n is the pad value of clock n−2.
- **P2.** An RX half samples in clock n and loads its producer at edge n. If the producer is not free, the new token is discarded and `OVERRUN` is set.
- **P3.** A TX half takes a token in clock n only when all its pending pad actions fall on edges ≤ n+1. The earliest edge a newly taken token can act on is n+1, so a pad output changes at the earliest in clock n+2.
- **P4.** The TX cursor counts 1/256 clocks.
  - `LEVEL`/`OE` act at `cursor + d·PRESC`, and set `cursor :=` that time. If that is earlier than the earliest edge, they act at the earliest edge, and `LATE` is set if `d > 0`.
  - `SETN` with n = 0 or 17–31 means 16. Unknown CTRL ops, BITSYNC-only ops outside BITSYNC, and ERR tokens at a TX half are taken and ignored (D-035 M).
  - `SYNC` sets `cursor :=` the earliest edge.
  - A DATA shift starts at `max(cursor, earliest)` and never sets `LATE`.
  - Bit i changes the pad at edge `(start + i·PERIOD) >> 8`. After the last bit the pad returns to IDLE, unless the next shift's first bit lands on the same edge.
- **P5.** `SHIFT_RX` shifts raw bits, including start and stop bits, first sample in bit 0 (LSB order). The start edge is the first synchronised sample that differs from IDLE; sample i is taken in clock `t0 + (SAMPLEOFS·PERIOD + i·PERIOD) >> 8`.

With these rules, the §5.5 path is exactly 7 clocks. The model measures it (`tools/tripsim/tests/test_pins.py::test_pin_to_pin_reaction_is_seven_clocks`).

Pin rules added with the I2C modes:
- **P6.** A linked TX shift changes pin A at the edge of the clock in which the synchronised pin B shows TX_EDGE, which is 3 clocks after the pad edge. The TX half takes a new DATA token as soon as the previous shift has put out all its bits. The new shift's first bit then replaces the pending return-to-IDLE on the next TX_EDGE, so consecutive bytes have no gap.
- **P7.** Pin B may be a `uo` output pad (for example, SPI data linked to our own SCK). The unit then sees the driven value directly, without a synchroniser.
- **P8.** Event generator (D-013): an EVENT `{new level of A, time[14:0]}` is emitted when the synchronised pin A shows EV_EDGE, and, if EV_QUAL is set, pin B was at EV_QUAL in both this clock and the previous one. It uses this clock's RX load, so a sample due in the same clock is skipped. With EV_RESET it restarts word framing (phase 0, no bits). The time counts PRESC ticks (D-024), so with PRESC > 1 long pulses fit in 15 bits: it is a per-unit 15-bit tick counter, +1 every PRESC clocks from reset (the model computes `(cycle div PRESC) mod 2^15`). Pin units are configured while their lanes are halted, before RUN; the RTL restarts the prescaler and counter on a PRESC write, which matches the model when PRESC is written before any event matters (D-035 J). At most one RX load happens per clock (P19).

Measured with these rules: the I2C target kernel queues its ACK 7 clocks after the 8th SCL rise, and SDA goes low 3 clocks after the SCL fall. It works for SCL high times ≥ 6 clocks (`tools/kernels/tests/test_i2c_target.py`). This is on an ideal bus in simulation; no rise times are modelled.

Pin rules added with the SPI modes (D-011):
- **P9.** Linked TX with TX_PRELOAD: if the unit is idle when it takes a DATA token, bit 0 goes out at the earliest edge (P3), and the remaining bits on each TX_EDGE. If the previous shift is still waiting for its final TX_EDGE, that edge carries bit 0 instead. This is continuous clocking, and it is how consecutive SPI mode-0 bytes join without a gap.
- **P10.** (Superseded by §14 F7, D-015: tag filtering moved from pin units to every fabric consumer port.)
- **P11.** CLKGEN, `CLK n` (D-016): n periods, each **IDLE for PERIOD/2, then ACTIVE for PERIOD/2**, starting from `max(cursor, earliest)`. The leading IDLE half gives SPI data setup before the first edge and I2C START hold (tHD;STA). Without STRETCH, the IDLE half after each ACTIVE half is timed from the release edge. With STRETCH, it is timed from the first clock in which the synchronised pin A reads IDLE: another device holding the line extends the phase. That costs up to 3 clocks per period (synchroniser + register). After the burst, `cursor` = the time of the final release (or of the line reading IDLE). A `CLK` token taken while a burst runs extends it seamlessly; other tokens wait for the burst to end.
- **P12.** In LEVEL mode, a DATA or EVENT token drives `data[0]` at `max(cursor, earliest)`.

Measured with these rules: the SPI controller kernel works in mode 0 up to SCK = 16.7 MHz (3 clocks per period). MISO passes through the 2-clock input synchroniser, which is what fails at 25 MHz. It takes about 38 clocks per byte at 12.5 MHz, against 32 for the bits alone.

Pin rules added with the generalized RX/TX primitives (D-013):
- **P13.** RX word framing: bits accumulate into a word of RX_NBITS bits (or, with RX_NBITS2 ≠ 0, alternately RX_NBITS then RX_NBITS2). The word is emitted right-aligned (LSB order: first bit in `data[0]`; MSB order: last bit in `data[0]`). A word is *tainted* if any of its samples was taken while a shifted bit from this unit's own TX was on pin A (from its first bit until its return to IDLE; D-016). Precisely: taint is judged on the unit's TX output register at the start of the sampling clock. Because a sample shows the pad of 2 clocks earlier, the 2 samples after our return to IDLE can still show our last bit untainted; no current program depends on those samples (D-035 I). A queued shift that has not started, LEVEL commands and released lines do not taint. With RX_ECHO = 0, tainted words are dropped instead of emitted, but framing still advances.
- **P14.** TX_LENTOK: a DATA token shifts `data[15:12] + 1` bits taken from `data[11:0]`, in ORDER. SETN is not needed, and payloads are limited to 12 bits.
- **P15.** Pin C (D-014): a unit is *selected* while its synchronised pin C equals C_ACTIVE (always, if no pin C).
  - While deselected, RX framing is held in reset, and no LINKED_RX/SHIFT_RX samples are taken. SHIFT_RX returns to "wait for IDLE, then a start edge", and SAMPLE bits due while deselected are discarded (D-035 G).
  - In the clock pin C becomes inactive, a linked TX shift in progress is aborted: its remaining bits are dropped and pin A returns to IDLE.
  - With C_OE, pin A's output enable is on only while selected, taking effect one clock after the synchronised change (3 clocks after the pad edge). This gates every TX mode, the carrier (P30) included (D-035 H).
  - Tokens may still be taken while deselected, so a preload can prepare the first bit before selection.
  - With EV_PIN = C, the event generator watches pin C: EVENT `data[15]` = new level of C.
- **P16.** WAIT (D-016): the TX half takes no further tokens until the synchronised pin B shows the given edge; in that clock, `cursor := earliest`. A WAIT taken in the clock where its edge appears, or after it, waits for the next edge (D-035 L), so firmware must arm it first (as the I2C controller does: SCL's WAIT for the START edge before SDA falls).

Fabric rule added (D-015):
- **F7.** Each consumer port has a 4-bit `accept` tag mask. A token that is available to the port (F1) but whose tag is not accepted is not visible to the consumer, and is dropped at the edge of the clock it is available in (`last_seq := seq`), exactly as if it had been taken. So a filtered subscriber never delays the producer.

Measured with these rules: the I2C controller kernel runs 100 kHz / 400 kHz / 1 MHz with and without clock stretching, meeting tLOW/tHIGH ≥ PERIOD/2 on the bus. Stretch awareness adds 3 clocks to each high phase (943 kHz at a nominal 1 MHz), and the SPI controller's limit is 12.5 MHz with a symmetric clock (§ exploration report).
- **P17.** PULSE (D-019): a DATA token of n bits (NBITS, or length-in-token) starts at `max(cursor, earliest)`. Bit b drives SYMb_FIRST at t, the opposite level at t + T1_b·PRESC, and the next bit starts at t + (T1_b + T2_b)·PRESC. After the last bit pin A returns to IDLE and `cursor` = the end time, so back-to-back tokens join with no gap. Timing is exact to the clock (integer ticks); `GAP` gives latch/reset times.
- **P18.** SETN with arg bit 5 = 1 (D-020): at `max(cursor, earliest)` (and `cursor :=` that time) the RX word length becomes n (1..16, overriding RX_NBITS/RX_NBITS2 until the next such SETN) and the framing restarts: partial bits and the two-phase position are cleared. A sample taken in that same clock is discarded as a partial bit, unless it completes a word, which is still emitted (RX runs before the TX stream in a clock; D-035 K). It is ordered with LEVEL/GAP in the TX stream, so firmware can place the restart between its own line activity and the first bit it wants counted.
- **P19.** SAMPLE delay (D-020): at `t = max(cursor + delay·PRESC, earliest)` the synchronised pin A is added to the RX framing as one bit (P13 applies: taint, echo, word emission); `cursor := t`. It works in any RXMODE. At most one RX load happens per clock, with priority EVENT, then the LINKED_RX/SHIFT_RX word, then the SAMPLE word. A word that loses is discarded and sets OVERRUN, as in §4.5 (D-035 F).
- **P20.** BITSYNC (D-023): TXMODE and RXMODE are both `bitsync`. The unit keeps one bit clock (start of the current bit, PERIOD, sample point at SAMPLEOFS·PERIOD). It free-runs while the bus is idle; pin S (or A) is sampled once per bit. IDLE_BITS consecutive recessive (= IDLE level) samples make the bus idle. Idle ends a frame without a verdict (a partial word is dropped), but only while this unit is not driving a bit, and never with DELIM = se0 (P29). A configuration must set IDLE_BITS above the longest legal recessive run inside a frame: STUFF_N + 1 with stuffing, and at least STUFF_N + 2 with DELIM = flag so that the abort rule (P27) acts first (D-035, second pass).
- **P21.** Frame start: at bus idle, a recessive-to-dominant edge on the sensed pin hard-syncs the bit clock (bit start := that clock) and starts a received frame; if that edge is the echo of our own first bit, our bit timing is kept (D-025). A `SYNC` in the TX stream makes the next TX bits a new frame: it starts at the first bit boundary after bus idle, hard-syncing to our own first bit, and emits EVENT `0x9001`. If another node's frame starts while ours is waiting and our first bit is dominant, ours joins that bit (wired-AND arbitration) and also emits `0x9001`.
- **P22.** Resync: on a recessive-to-dominant edge (or any edge with RESYNC = both) that does not start a frame (inside a frame, or before the bus is idle again), at most once per bit and never on an edge to the level this unit is driving itself (D-025), the bit start moves toward the edge by at most SJW: later if the edge is before the sample point, earlier (shortening the bit) if after it.
- **P23.** Stuffing: with STUFF_N > 0, after STUFF_N equal bits (or STUFF_N bits at STUFF_LVL) the next line bit is the complement. RX removes it (an equal bit there is a stuff error: ERR `0x1nnn`, nnn = line bit, and word framing stops for the frame); TX inserts it while `LINE` stuffing is on. Runs count line bits, stuff bits included.
- **P24.** Frame length and CRC: the RX CRC register (CRC_INIT at the frame start, MSB-first LFSR with CRC_POLY) takes every destuffed RX bit after the first CRC_SKIP. Words of RX_NBITS (ORDER) are emitted as DATA. When the destuffed count reaches the frame's n (`FRAME`), the last partial word (its low 12 bits) is emitted as EVENT (data[14] = the frame is our own; the same for frames ended by a flag, P27, or SE0, P29) if the CRC register equals CRC_RES, else as ERR `0x0www`. A CRC mismatch is reported but is not an error in the sense of P26 (no abort, no armed JAM); word framing and RX stuffing then stop, except that a stuff bit due right after bit n is still removed and checked. `FRAME` without [11] applies to the frame in progress (LATE if there is none, word framing has stopped, or the count is already at or past n); with [11], to the next frame.
- **P25.** TX queue: DATA tokens (NBITS or length-in-token, ORDER) and `LINE`/`SYNC` markers are queued; a TX token is taken only when no data bits are queued. At each bit start the next bit is driven: a stuff bit first if one is due (even before a `LINE` change), stuffing runs counting every bit sent. `LINE` markers take effect in stream order: [1:0] readback mode, [2] stuffing, [6] resets the TX CRC register (as does SYNC), [3] inserts the TX CRC register XOR CRC_XOR (CRC_WIDTH bits, MSB first), [4] ends the frame with SE0 (P29). The TX CRC register takes every data bit we send (not stuff bits, not CRC bits). With no bits queued the line is released (recessive). A TX token also waits while SE0/J items are queued or a `WAIT` [1] is pending. Within one `LINE`, [6] acts before [3], and the CRC bits go out before the SE0. RX commands (`FRAME`, `SETN` rx, `JAM`) are taken at once, even while TX data is queued; in BITSYNC, `SETN` rx applies at once (there is no cursor). `WAIT` [1] holds further TX tokens until the next sample point. Other CTRL ops (`LEVEL`, `OE`, `GAP`, `CLK`, `SAMPLE`, `SETN` without bit 5, `WAIT` without [1]) are taken and ignored in BITSYNC; the TX word length is NBITS or TX_LENTOK.
- **P26.** Readback (D-026), for a bit we drive: mode 1 (arbitration): a mismatch emits EVENT `0x8000 | level << 14 | bit << 1`, clears the TX queue and discards DATA/`LINE` tokens until a `SYNC` or `WAIT` [1]; mode 2 (expect an override): emits `0xA000 | level << 14 | bit << 1`, and it is an error if the sample equals our level; mode 3 (strict): a mismatch emits `0xB000 | level << 14 | bit << 1` and is an error. An error (these, or a stuff error) stops our TX as in mode 1 and fires an armed `JAM`. A refused frame (listen-only) emits `0xC001`.
- **P27.** DELIM = flag (D-025): STUFF_N ones (at STUFF_LVL) then the other level is a stuff bit; a (STUFF_N + 1)th one followed by the other level is a flag: the frame in progress (if it has committed bits) ends as in P24 (EVENT / ERR `0x0www` by CRC_RES), and a new frame opens with a fresh CRC; one more one aborts the frame (ERR `0x2nnn` if it had data) until the next flag. Destuffed bits are committed to the frame only when STUFF_N + 1 newer ones have arrived. With IDLE_BITS ≥ STUFF_N + 2 (P20) a ones run aborts the frame before the bus counts as idle, so idle never ends a frame with a verdict.
- **P28.** `JAM` (D-026): [11:8] n-1, [7:6] d, [5] level, [4] armed. Not armed: the unit drives the level for n bits from the first bit start after d + 1 more non-stuff sample points, bypassing the TX queue; in a frame this unit transmits, it is dropped instead. Armed: it fires at the next bit start after the next error (P26) and applies in any frame. [4] together with [0] disarms ([0] without [4] is ignored). [1] / [2] switch listen-only on / off, ignoring the other bits (nothing driven, the TX queue cleared, a `SYNC` refused); with both set, [1] wins. A new JAM replaces one in progress.
- **P29.** NRZI, SE0, pin N, OE auto (D-027): with NRZI, a data 0 is sent as a change of the line level and a 1 as none, and received the same way (runs, stuffing and CRC work on data bits; edges, idle and resync on line levels). Pin N drives the complement of pin A, except during SE0, when both are low. `LINE` [4] sends SE0 for [11:8] + 1 bits, then the idle level for 1 bit, then releases. With OE_AUTO the pads are driven only while a bit is being sent, and the unit's own frames are not reported. With DELIM = se0 a frame ends (P24 verdict) when pin S and pin B both sample low, and only then.
- **P30.** Carrier (D-024): with CARRIER > 0, whenever pin A's registered level is not IDLE it toggles between that level and IDLE with period CARRIER clocks (50 % duty), the phase restarting at every change to the active level. It applies to any TXMODE.
