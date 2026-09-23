# TRIPWIRE: instruction set

This document defines what a TRIPWIRE lane executes:
- the **reflex slots** (the fast path, no program counter);
- the **routines** (the slow path, sequential code in SRAM);
- the **one operation table** both of them share.

It also explains *why* the instruction set looks the way it does, compared with other protocol engines.

**Status: draft (phase 1, started early under DECISIONS D-006).** Choices here are proposals to be confirmed or reversed by the architecture model (`tripsim`, DECISIONS D-008) before the spec freeze. At the freeze, the bit encodings move into `spec/tripwire.yaml`. After that, the encoding tables in this document are generated from the YAML and never hand-edited.

Companions: `ARCHITECTURE.md` (tokens, fabric, pin units, helpers, host interface, timing), `VERIFICATION.md`, `OVERVIEW_TRIPWIRE.md`.

---

## 1. Where the protocol-specific work lives

Most protocol engines put their protocol-specific features **in the opcodes**:
- RP2040 PIO has 9 single-cycle instructions (`JMP WAIT IN OUT PUSH PULL MOV IRQ SET`) with side-set and delay fields in every word.
- TI's PRU is a plain single-cycle RISC that reads pins through `R31`, writes them through `R30` and polls with `WBS`/`WBC`.
- Loom (a competing entry) has 55 16-bit instructions: a generic ALU plus pin (`SETP`, `IN`, `OUT`), wait (`WAITD`, `WAITP`, `WAITE`), FIFO and bit-engine (`SHO`, `SHI`, CRC) classes.

In all three, the core **bit-bangs**: the program touches every bit, and the timing is in the instruction stream.

TRIPWIRE splits that work across three places, so the opcodes themselves can stay small and ordinary:

| Protocol work | Where it lives in TRIPWIRE | Prior art for that split |
|---|---|---|
| Bit timing, shifting, sampling, clock generation, pulse coding | **Pin units** (`ARCHITECTURE.md` §7), commanded by tokens | NXP FlexIO (timers + shifters emulate UART/SPI/I2C with no CPU per bit); Propeller 2 smart pins (mode/X/Y registers); XMOS timed ports |
| Protocol state machine: "what happens next" | **Reflex conditions** (STATE, flags, channel status, tags), evaluated in parallel every clock. No branch instructions. | Triggered Instructions (Parashar et al., ISCA 2013); PSoC UDB (a datapath with 8 stored configurations selected by a state machine) |
| Moving data between blocks | **Channel fabric**: forwarding, multicast and taps cost no instructions | XMOS channels and events |
| Byte/word data work (compare an address, build a frame, count bytes) | **The operation table** (§3): ordinary ALU ops plus a few protocol-shaped ones | — |

So a lane never sees individual bits: it reacts to *bytes and events* delivered by pin units. That is why its ALU ops look like a normal CPU's, while its *control* (the conditions) and its *I/O* (tokens to pin units) are where it differs. An opcode list alone makes TRIPWIRE look more conventional than it is.

The earlier draft did have a real problem here. The routine tier had its **own** LC-3-style ISA, with a different and smaller op set. That gave two decoders and two semantics to verify, and routines could not compare data at all (Q5). This draft fixes it with **one operation table for both tiers** (§3).

---

## 2. Programmer's model (per lane)

| State | Width | Written by | Read by | Notes |
|---|---|---|---|---|
| r0–r3 | 4 × 16 | Actions, routines | Actions, routines | General registers. Read in EXEC, so register dependencies between consecutive actions cost no extra clock |
| **K0–K3** | 4 × 16 | Host only, while halted | Actions (as B, and CMPM operands), routines (`GETK`) | **New:** per-lane constants (addresses, masks, pin commands). They free general registers and avoid 2-action constant building |
| STATE (p7..p4) | 4 | Reflex `NS` (static), routine `SETST` | Conditions | 16 protocol states |
| FLAGS f0–f2 (p2..p0) | 3 | Reflex `DFE` result, routine `SETF/CLRF/CPYF` | Conditions, routine `TSTF` | Compare results and user flags |
| f3 = RB | 1 | Hardware (CALL sets, RET clears) | Conditions | Routine busy; read-only |
| PEND | 3 | Hardware | Scheduler | A flag with a result in flight (§4.4) |
| I0, I1 | input ports | Fabric | Actions (`ASRC`) | Head token = 16-bit data + 2-bit tag |
| O0, O1 | output ports | Actions, routine `OUT` | Fabric | Depth-1 producer registers |
| RPC, RIR | 9 (10 with 1K SRAM), 16 | Routine sequencer | — | Routine PC and fetched-instruction register |
| RZ | 1 | Routine ALU ops | Routine branches | Routine-local condition bit; not visible to reflexes |
| Global time | 16 | Hardware | Actions (`ASRC=7`), routines (`GETT`) | Free-running, +1 per clock |

Tokens (unchanged from `ARCHITECTURE.md` §4.1): 16-bit data + 2-bit tag, `00 DATA`, `01 CTRL`, `10 EVENT`, `11 ERR`.

**Convention for EVENT tokens:** `data[15]` carries the new level of the pin (rising = 1). So I2C START (SDA falls) is `data[15]` = 0 and STOP is 1. Short RX words, such as the I2C ACK/NACK bit, are right-aligned, so their bit is `data[0]`. Reflex conditions can test either bit directly (§4.2 `HE/HV/HS`).

---

## 3. The operation table (shared by reflexes and routines)

One 4-bit `OP` field, same meaning in both tiers. Inputs:
- **A:** the primary operand (a register, an input head, zero or time in reflexes; a register in routines).
- **B:** the second operand.
- **F[7:0]:** the "field" operand used by the protocol-shaped ops. It is the slot's `IMM` in a reflex, or `b` / `r[b][7:0]` in a routine (§5.1).

Every op also produces a **1-bit result R**:
- in a reflex, R is written to `f[DF]` when `DFE` is set;
- in a routine, R always goes to `RZ`.

<!-- GENERATED:ops -->
<!-- GENERATED by tools/gen/gen.py from spec/tripwire.yaml. DO NOT EDIT. Edit spec/tripwire.yaml. -->
| OP | Name | Data result d | Flag result R | Used for |
|---|---|---|---|---|
| 0 | MOV | A | d == 0 | Forwarding tokens, loading registers |
| 1 | ADD | A + B | d == 0 | Counters, pointers |
| 2 | SUB | A − B | d == 0 | Count-down with zero test in one action |
| 3 | AND | A & B | d == 0 | Masking; bit test |
| 4 | OR | A \| B | d == 0 | Setting bits; placing constants (`zero \| K`) |
| 5 | XOR | A ^ B | d == 0 | Equality test; arbitration readback |
| 6 | SHL | A << B[3:0] | d == 0 |  |
| 7 | SHR | A >> B[3:0] | d == 0 |  |
| 8 | SHOR | (A << F[3:0]) \| r[F[5:4]] | d == 0 | Frame building (start/stop/ACK bits) in one action |
| 9 | EXT | (A >> F[3:0]) & mask(F[7:4] + 1) | d == 0 | Pull a field out of a frame |
| 10 | CMPM | A (pass-through) | (A & M) == V; M, V = K[F[1:0]], K[F[3:2]] if F[4] else r[F[1:0]], r[F[3:2]] | Address match, multi-bit checks |
| 11 | LTU | A (pass-through) | A < B (unsigned) | Bounds: buffer ends, EEPROM wrap |
| 12 | PAR | A (pass-through) | XOR-reduce(A) | Parity check while forwarding |
| 13 | MKCTL | {F[7:4], A[11:0]}, tag CTRL | d == 0 | Pin command with a register argument |
| 14 | CALL | — | — | Start routine F[4:0] (reflex only); implicit RB == 0 |
| 15 | MOVB | B | d == 0 | React to an input with a constant (D-009) |
<!-- /GENERATED:ops -->

Changes from the earlier op table (`ARCHITECTURE.md` §5.3 before DECISIONS D-007):
- `CMPEQ` and `TSTZ` are gone. `XOR` and `AND` with a zero result do the same job, now that every op produces a flag result.
- Their codes went to `LTU` and `MOVB` (D-009).
- `PAR`, `CMPM` and `LTU` pass A through, so a byte can be checked and forwarded in the same action.

---

## 4. Reflex slots

### 4.1 Encoding (53 bits; host writes 4 × 16-bit words)

<!-- GENERATED:slot_fields -->
<!-- GENERATED by tools/gen/gen.py from spec/tripwire.yaml. DO NOT EDIT. Edit spec/tripwire.yaml. -->
| Bits | Field | Part | Meaning |
|---|---|---|---|
| [0] | V | condition | slot valid |
| [1] | U | condition | urgent: pre-empts a waiting routine step |
| [2] | SE | condition | STATE-match enable |
| [6:3] | SV | condition | required STATE |
| [10:7] | FM | condition | flag mask over f3..f0 (f3 = RB) |
| [14:11] | FV | condition | required flag values |
| [15] | TE | condition | tag match on the A input's head |
| [17:16] | TAG | condition | required tag |
| [18] | HE | condition | head-bit match enable |
| [19] | HV | condition | required head bit |
| [23:20] | OP | action | operation (ops table) |
| [26:24] | DST | action | destination (enum DST) |
| [29:27] | ASRC | action | A source (enum ASRC) |
| [30] | DQ | action | dequeue the A input (only if ASRC is I0/I1) |
| [32:31] | BSEL | action | B source (enum BSEL) |
| [40:33] | IMM | action | 8-bit immediate; also the field operand F |
| [41] | NSE | action | next-STATE enable (static update) |
| [45:42] | NS | action | next STATE |
| [46] | DFE | action | write the flag result R |
| [48:47] | DF | action | which flag: 0-2 = f0-f2, 3 = none |
| [50:49] | OT | action | output tag (DST O0/O1; ignored for MKCTL and when KT) |
| [51] | KT | action | keep the A input head's tag on the output |
| [52] | HS | condition | head-bit select for HE/HV: 0 = data[15], 1 = data[0] |

| Enum | Codes |
|---|---|
| DST | 0 r0, 1 r1, 2 r2, 3 r3, 4 O0, 5 O1, 6 none |
| ASRC | 0 r0, 1 r1, 2 r2, 3 r3, 4 I0, 5 I1, 6 zero, 7 time |
| BSEL | 0 reg, 1 imm, 2 k |
<!-- /GENERATED:slot_fields -->

53 bits. Host words: w0 = bits [15:0], w1 = [31:16], w2 = [47:32], w3[4:0] = [52:48].

### 4.2 When a slot is ready

The programmer writes the **explicit** part: state, flags, and tag/head tests. The hardware adds the **implicit** part from what the action uses, as Triggered Instructions do. That way, a slot can never read an empty input, write a full output, or CALL while a routine is running.

```
ready(s) =  V
         && (!SE || STATE == SV)
         && ((FLAGS ^ FV) & FM) == 0
         && (PEND & FM) == 0                                    // pending rule, §4.4
         && (ASRC ∉ {I0,I1} || ( avail(ASRC)                    // implicit
                                 && (!TE || head.tag == TAG)
                                 && (!HE || (HS ? head.data[0] : head.data[15]) == HV) ))
         && (DST  ∉ {O0,O1} || free(DST))                       // implicit, includes reservation
         && (OP != CALL || !RB)                                 // implicit
```

This replaces the old explicit `IN` and `OUT` fields. Those allowed a slot to read `I0` without checking that it held a token.

### 4.3 Which slot fires
- **No routine waiting (RIR empty):** the lowest-index ready slot fires.
- **A routine step is waiting (RIR valid, §5.3):** urgent ready slots first (lowest index), then the routine step, then non-urgent slots.

One action per clock per lane.

### 4.4 Pipeline and timing (unchanged from `ARCHITECTURE.md` §5.4)

```
clock n    EVAL : evaluate all slots, pick one (§4.3)
                  static updates now: STATE := NS (if NSE), dequeue (if DQ), reserve the output (if DST is O0/O1)
                  latch the A input head; if DFE: PEND[DF] := 1
clock n+1  EXEC : read registers/K, ALU, write r[d] or load O0/O1, write f[DF] and clear PEND[DF]
```

- STATE updates are visible to the next EVAL (0 extra clocks).
- A slot whose `FM` covers a pending flag waits exactly **one** extra clock.
- Registers are read in EXEC, so a slot that uses a register written by the previous action pays nothing extra.

---

## 5. Routines

Routines are bounded, non-urgent sequential code in SRAM (setup, bookkeeping, error reports, table walks). They use the **same operation table** (§3). The only routine-specific instructions are for sequencing, memory, output and flags.

### 5.1 Encoding (16-bit words)

<!-- GENERATED:routine_formats -->
<!-- GENERATED by tools/gen/gen.py from spec/tripwire.yaml. DO NOT EDIT. Edit spec/tripwire.yaml. -->
| Word | [15] | [14:12] | Fields | Meaning |
|---|---|---|---|---|
| ALU | 0 | (op) | op[14:11] rd[10:9] ra[8:7] bs[6] b[5:0] | one op from the operation table; RZ := R |
| LDI | 1 | 000 | rd[11:10] imm[9:0] | rd := zext(imm10) |
| LDIH | 1 | 001 | rd[11:10] imm[9:0] | rd := {imm[5:0], rd[9:0]} |
| BR | 1 | 010 | cond[11:9] off[8:0] | branch if cond (enum BR_COND); off signed, from the next word |
| DJNZ | 1 | 011 | rd[11:10] off[9:0] | rd := rd - 1; branch if rd != 0; off signed |
| LD | 1 | 100 | rd[11:10] ra[9:8] off[7:0] | rd := SRAM[r[ra] + off] |
| ST | 1 | 101 | rd[11:10] ra[9:8] off[7:0] | SRAM[r[ra] + off] := rd |
| OUT | 1 | 110 | port[11] tag[10:9] ra[8:7] | enqueue r[ra] with tag on O0/O1; waits while full |
| SYS | 1 | 111 | fn[11:8] arg[7:0] | system op (enum SYS) |

BR conditions: 0 = always, 1 = rz, 2 = nrz.

| SYS kind | Name | Effect (arg = word[7:0]) |
|---|---|---|
| 0 | NOP | no operation |
| 1 | RET | return: RB := 0 |
| 2 | SETST | STATE := arg[3:0] |
| 3 | SETF | f[arg[1:0]] := 1 |
| 4 | CLRF | f[arg[1:0]] := 0 |
| 5 | TSTF | RZ := f[arg[1:0]] |
| 6 | CPYF | f[arg[1:0]] := RZ |
| 7 | GETT | r[arg[1:0]] := time |
| 8 | GETK | r[arg[1:0]] := K[arg[3:2]] |
<!-- /GENERATED:routine_formats -->

- ALU words: B = bs ? zext(b) : r[b[1:0]]; F = bs ? zext(b) : r[b[1:0]][7:0]; rd := d (write rd = ra for compare-only use). Op 14 (CALL) is reserved in routines (no nesting).

Branch offsets are signed and relative to the next instruction.

This resolves:
- **Q4:** branches test only `RZ`, so a 3-bit `cond` is enough. `DJNZ` has its own format with a register field. Shared flags are tested with `TSTF` first.
- **Q5:** routines now have every compare and field op.

### 5.2 Calling and returning
- `CALL n` (reflex, OP 14) reads the start address from entry-table word `n` (SRAM words 0–31) on the lane's next rotation slot. It sets RB. The first instruction is fetched on the rotation slot after that.
- `RET` clears RB.
- Every loop is a `DJNZ` with a compile-time-known count, so the compiler can compute each routine's worst-case step count.

### 5.3 Routines and reflexes share EXEC (resolves Q1)
- SRAM access rotates `cycle mod 4`: 0 → L0, 1 → L1, 2 → L2, 3 → MEM/CAPTURE/HOST (`ARCHITECTURE.md` §6.2).
- On its rotation slot, a lane with RB set and an empty RIR fetches `SRAM[RPC]` into RIR.
- A valid RIR is a **candidate for EXEC**. It is beaten only by an **urgent** ready slot (§4.3). A non-urgent slot waits behind it.
- Once the step executes, RIR empties and the next fetch happens at the next rotation slot.
  - `LD`/`ST` use the following rotation slot for the data access.
  - `OUT` stays in RIR (and retries) while its output is full.

Consequences, which the compiler reports:
- **Urgent reflexes** are never delayed by a routine.
- **Non-urgent reflexes** are delayed by at most one clock per routine step, i.e. at most 1 clock in every 4.
- **A routine** makes one step per rotation (4 clocks), unless urgent reflexes are firing on the clocks when its step is waiting.
- Routine writes to STATE/flags (`SETST`, `SETF`, `CLRF`, `CPYF`) take effect at the routine's EXEC. Reflex conditions see them from the next clock. If a reflex's static `NS` and a routine `SETST` hit the same clock, the ordering is fixed in the cycle-exact semantics section (P1). The proposal is that the reflex update wins.

---

## 6. Commands carried in tokens

Pin units and helpers are not programmed with instructions. They are sent **CTRL tokens**: `data[15:12]` is the command, `data[11:0]` the argument. Examples are `LEVEL`, `OE`, `CLK`, `GAP`, `SYNC` and `SETN` for pin TX halves, and `RESET`/`READ`/`ADDR` for helpers. The tables live in `ARCHITECTURE.md` §7.3 and §8.

A lane produces these tokens in one of two ways:
- a constant from `K` (`OR` with `A = zero`, `BSEL = K`, `OT = CTRL`);
- a register-derived argument (`MKCTL`).

---

## 7. Worked examples

Syntax used below (the real `.trw` language comes with `tripc`):
`slot N [U] when <conditions> do <op> <dst> := <A>, <B/F> ; <static updates>`

### 7.1 Counting bytes: the zero flag at work
Forward `r0` bytes from I0 to O0, then report DONE on O1.

```
slot 0    when STATE=SEND, f0=0                 do MOV O0 := I0 ; deq ; STATE:=DEC
slot 1    when STATE=DEC                        do SUB r0 := r0, #1 -> f0 ; STATE:=SEND
slot 2    when STATE=SEND, f0=1                 do MOV O1 := zero, tag EVENT ; STATE:=IDLE
```

- **Cost per byte:** 3 clocks (slot 0, slot 1, one pending clock on f0).
- **Old draft:** 4 clocks and one more slot (`SUB`, then `TSTZ`, then pending), because only compare ops could write flags.

### 7.2 I2C target: address match and ACK
Setup:
- U0: pin A = SDA (`uio0`, open-drain), pin B = SCL (`uio1`); LINKED_RX on SCL rise, 8 + 1 bit framing, echo suppression; events on SDA edges while SCL is high (START/STOP); TX linked to SCL fall, length in the token.
- The full read + write kernel (12 slots) is `tools/kernels/i2c_target.py`; the listing below is the address/ACK part as first drafted.
- L0.I0 ← U0.rx (blocking); L0.O0 → U0.tx.
- `K0 = 0x00FE` (address-bit mask), `K1 = own address << 1`, `K2 = 0x6001` (`SETN 1`).
- All general registers stay free.

```
slot 0 U  when I0:EVENT, head[15]=0 (START)     do MOV none := I0 ; deq ; STATE:=ADDR   (A = I0 so the tests apply)
slot 1 U  when STATE=ADDR, I0:DATA              do CMPM none := I0, mask K0, val K1 -> f0 ; deq ; STATE:=ACKQ
slot 2 U  when STATE=ACKQ, f0=1                 do OR O0 := zero, K2, tag CTRL ; STATE:=ACK1
slot 3 U  when STATE=ACK1                       do MOV O0 := zero (DATA 0: one ACK bit) ; STATE:=ACKD
slot 4    when STATE=ACKD                       do CALL addr_ok ; STATE:=XFER
slot 5 U  when STATE=ACKQ, f0=0                 do MOV none := zero ; STATE:=IDLE
slot 6 U  when I0:EVENT, head[15]=0 (STOP)      do MOV none := I0 ; deq ; STATE:=IDLE
```

- **Timeline:** unchanged from `ARCHITECTURE.md` §13. The ACK is armed about 10 clocks (200 ns) after the 8th SCL rising edge, against a ≥ 600 ns (400 kHz) or ≥ 260 ns (1 MHz) budget.
- **Improvements over the old version:**
  - START and STOP are told apart by the condition alone (`HE/HV`). The old version needed a compare action.
  - The constants no longer use two of the four registers.
  - CALL waits for RB = 0 automatically.
- **Possible pin-unit improvement (for the model to evaluate):** separate TX and RX `NBITS` in the pin unit would remove the `SETN` token entirely, arming the ACK about 2 clocks earlier.

---

## 8. Open questions Q1–Q6: proposed resolutions

| Q | Issue | Resolution in this draft |
|---|---|---|
| Q1 | When do routine steps run vs. reflexes; what does `U` block? | §5.3: all reflexes stay eligible; `U` only decides who wins EXEC when a routine step is waiting |
| Q2 | CALL encoded twice | CALL is OP 14 only; DST 7 is reserved |
| Q3 | MKCTL can't set bit 11 | MKCTL passes `A[11:0]`; constant commands come from `K` |
| Q4 | Routine branch format too narrow | Branches test `RZ` only; `DJNZ` has its own format; `TSTF` moves a shared flag into `RZ` |
| Q5 | No compares in routines | One shared operation table (§3) |
| Q6 | `OTAG` shares immediate bits | `OT` (2 bits) and `KT` (1 bit) are separate fields |

---

## 9. What the model must measure before the freeze

These are deliberately **not** decided by argument. The architecture model (`tripsim`, DECISIONS D-008) runs UART, SPI and I2C (controller and target), SPI flash emulation and 1-Wire on the ISA above, and reports:

| Question | Metric | Decision it drives |
|---|---|---|
| Are 12 slots enough? | Slots used per protocol and per lane | 12 vs 16 slots |
| Are 4 registers + 4 constants enough? | Register/constant pressure; spills into routines | Keep, or 8 registers |
| ~~What should OP 15 be?~~ | Answered: `MOVB` (D-009). The model's first latency kernel needed "on an input, emit a constant" | Done |
| Do implicit checks, the zero flag, `K` and `HE/HV` pay off? | Slots and clocks per protocol, with and without each | Keep or drop each (ablation) |
| What does the R1 fallback cost? | Protocol deadlines met at "fire every other clock" | Whether the fallback is acceptable |
| Separate TX/RX NBITS in pin units? | ACK and turnaround latency | Pin-unit spec change |
| Routine rate | Worst-case routine steps vs. protocol gaps | SRAM rotation and routine features |

---

## 10. Prior art and honesty labels

| Idea | Label | Prior art |
|---|---|---|
| Conditions evaluated in parallel, no PC, implicit channel checks, tag matching | [NEW-FIELD] for this competition; the paradigm is not ours | Parashar et al., *Triggered Instructions*, ISCA 2013. Their example PE: 8 registers, 8 predicates, 16 instructions, 2 sources; the scheduler is under 2% of PE area |
| Pin units doing bit timing | [STANDARD] | NXP FlexIO, Propeller 2 smart pins, XMOS timed ports, Loom, TEMPO |
| Small state-selected datapath configurations | [STANDARD] | PSoC UDB datapath (8-entry configuration RAM), PRISM (state table in latch arrays) |
| Two tiers sharing one op table, urgent pre-emption of routine steps | [OURS] | — |
| Per-lane host-loaded constants (`K`) | [STANDARD] | Common in configurable datapaths |

Sources:
- [Triggered Instructions (ISCA 2013)](https://www.parashar.org/isca13.pdf)
- [NXP: Emulating UART using FlexIO (AN5034)](https://www.nxp.com/docs/en/application-note/AN5034.pdf), [NXP: Understanding FlexIO](https://community.nxp.com/t5/Kinetis-Microcontrollers/Understanding-FlexIO/ta-p/1115419)
- [Propeller 2 I/O pins](https://p2docs.github.io/pin.html)
- [XMOS XS1 architecture](https://docs.alexrp.com/xcore/xmos_xs1.pdf)
- [PSoC UDB datapaths (AN82156)](https://www.infineon.com/assets/row/public/documents/cross-divisions/42/infineon-an82156-designing-psoc-creator-components-with-udb-datapaths-applicationnotes-en.pdf?fileId=8ac78c8c7cdc391c017d071b9c9a1dfb)
- [TI PRU assembly instruction guide](https://www.ti.com/lit/ug/spruij2/spruij2.pdf)
- [RP2040 PIO overview (Circuit Cellar)](https://circuitcellar.com/resources/quickbits/rp2040-programmable-io/)
- [Loom ISA (`isa/isa.yaml`)](https://github.com/thomasgilbert481/tt_um_loom)
