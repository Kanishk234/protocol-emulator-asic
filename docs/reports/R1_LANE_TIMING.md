# R1: lane timing at 50 MHz (risk spike)

Phase 1 task 13. **Question:** can a lane evaluate all 12 reflex conditions, pick a slot and apply its static updates in one 20 ns clock (EVAL every clock), or must it fall back to firing every other clock? **Decision it drives:** the fire rate (ARCHITECTURE §14 L1). Decision: DECISIONS D-030.

**Answer: fire every clock.** Before layout, the worst EVAL path is 3.5–6.9 ns at the typical corner and 5.4–10.8 ns at the slow corner (committed RTL; up to 11.4 ns in earlier runs, see the mapping-noise note in §3). The worst case seen in any run (no buffering, configuration treated as changing, slow corner) still has 8.2 ns of slack: the path could grow by 72 % before it fails. The buffered latch build has 3.5× margin.

Date: 2026-09-24 (final run with the library clock gate `sg13cmos5l_lgcp_1` and the slot read port, see §3 and §5). Reproduce: `spikes/r1_lane/run_r1.sh` (outputs in `spikes/r1_lane/build/`, not committed).

---

## 1. What was built

A throwaway lane in `spikes/r1_lane/` (see its README), written only from `ARCHITECTURE.md`, `ISA.md` and `spec/tripwire.yaml`. It does not use `tools/tripsim` (independence rule).

- **EVAL, the full path the spec describes** (ISA §4.2–4.4, §14 L2, L4, L6, L7):
  - 12 `ready()` terms: V, STATE match, flag mask/values, the pending rule, and the implicit input, output and CALL checks (TE/HE/HS on the head of I0 or I1);
  - the §4.3 group rule (a waiting routine step lets only urgent slots through) and a single lowest-index priority encoder;
  - a 12-way mux of the selected slot's fields;
  - static updates at the edge: STATE, dequeue (the consumer port's `last_seq`), output reservation, PEND, RB and the CALL request;
  - latching the EXEC fields and the A head (or time).
- **In front of EVAL, the real fabric logic:** two consumer ports with the D-029 source lists (8 and 9 sources) and F7 tag filtering. Behind the output-free check, the §4.4 release term over the real subscriber lists: 8 subscribers for O0, 9 for O1.
- **EXEC:** operand muxes (registers, K, zero, latched head/time), the 16-op ALU (two barrel shifters, compare, CMPM with K or register operands, LTU, parity), register, flag, RZ and output writes, plus routine ALU, LDI, LDIH, DJNZ, OUT and SYS steps.
- **Slot store:** 12 × 53 bits + K0–K3, as an Ibex-style latch array with one clock gate per 16-bit host word, or as flops (the fallback).
- **Harness:** every register the lane talks to (producers, subscriber state, RIR, RUN, host port) sits in the harness, so every timed path is register to register.

**Sanity simulation** (`tb_r1_lane.v`, Icarus, both slot stores): ISA §7.1 forwards 4 bytes at exactly 3 clocks per byte and then emits the EVENT. This matches the cost ISA §7.1 states, arrived at independently of the model. Verilator `-Wall` is clean.

## 2. Method

| Item | Value |
|---|---|
| Synthesis | Yosys 0.69+24: `synth -flatten; dfflibmap; abc` onto the cmos5l cells (the `scripts/gl_local.sh` recipe) |
| Mapping variants | **plain**: ABC delay mapping with no buffering, so high-fanout nets are left unbuffered (the flow's resizer would fix them); **sized**: `abc -D 4000 -constr` (ABC buffering + gate sizing), a rough stand-in for the resizer |
| Liberty | IHP-Open-PDK `2bbec75` (the revision `tt-gds-action@ihp-cmos5l` pins): `typ_1p20V_25C` (TT sign-off corner) and `slow_1p08V_125C` |
| STA | OpenSTA 2.6.0 (standalone `sta` from the OpenROAD `2.0-17598-ga008522d8` Ubuntu 22.04 build) |
| Constraints | 20 ns clock, ideal (no CTS), 0.25 ns setup uncertainty, no wire parasitics |
| Configuration | **cfg 0**: every register is a timing startpoint. **cfg 1**: host-written configuration (slot and K store, port `sel`/`en`/`accept`, subscriber `sel`/`en`/`mode`) is a false-path startpoint, because it only changes while the lane is halted (ARCHITECTURE §9) |
| Endpoint groups | **EVAL**: STATE, PEND, RB, reservations, the EXEC-stage fields, the A latch, CALL, the consumer ports' `last_seq` (64 registers). **EXEC**: r0–r3, f0–f2, RZ, O0/O1 (108 registers) |

## 3. Results (20 ns clock)

Arrival = data arrival at the endpoint (ns); slack against 20 ns minus uncertainty and setup.

| Slots | Mapping | Corner | Config | EVAL arrival | EVAL slack | EXEC arrival | EXEC slack |
|---|---|---|---|---|---|---|---|
| latch | plain | typ | 0 | 6.94 | 12.69 | 5.27 | 14.34 |
| latch | plain | typ | 1 | 5.95 | 13.68 | 5.27 | 14.34 |
| latch | plain | slow | 0 | **10.78** | **8.78** | 8.26 | 11.24 |
| latch | plain | slow | 1 | 9.26 | 10.29 | 8.26 | 11.24 |
| latch | sized | typ | 0 | 3.58 | 16.04 | 4.10 | 15.52 |
| latch | sized | typ | 1 | 3.48 | 16.15 | 4.10 | 15.52 |
| latch | sized | slow | 0 | 5.62 | 13.91 | 6.41 | 13.12 |
| latch | sized | slow | 1 | 5.45 | 14.11 | 6.41 | 13.12 |
| flop | plain | typ | 0 | 6.45 | 13.18 | 6.91 | 12.70 |
| flop | plain | typ | 1 | 5.83 | 13.79 | 6.91 | 12.70 |
| flop | plain | slow | 0 | 10.06 | 9.49 | 10.69 | 8.80 |
| flop | plain | slow | 1 | 9.12 | 10.43 | 10.69 | 8.80 |
| flop | sized | typ | 0/1 | 3.68 | 15.95 | 3.94 | 15.68 |
| flop | sized | slow | 0/1 | 5.78 | 13.77 | 6.17 | 13.36 |

**Mapping noise.** These are the numbers for the committed RTL. Two earlier runs of the same lane differed only outside the critical path (first a behavioural clock gate instead of the library ICG, then no slot read port). They gave EVAL values up to 11.39 ns (flop, plain, slow, slack +8.16) and moved individual rows by up to ±1.2 ns. ABC restructures the logic differently whenever the netlist changes, so read every number here as ±1.5 ns. The conclusion is the same in every run.

**Margin.** How much the EVAL path could grow before it fails at 20 ns:

| Case | Growth allowed |
|---|---|
| Worst case in any run (flop, plain, slow, cfg 0: 11.39 ns) | 1.72× |
| Worst row of the final run (latch, plain, slow, cfg 0) | 1.81× |
| Planned build before resizing (latch, plain, slow, cfg 1) | 2.1× |
| Latch, sized, slow | 3.5× |

Wire delay, clock skew and a long route to producers in other blocks all eat into this margin; none of them is plausibly 70 %.

**The critical paths:**
- **EVAL (plain):** the consumer-port `sel` register or a producer's tag register → source mux → `accept` filter → `avail` → `ready[i]` → group mask → priority encoder → the selected slot's ASRC → the A-latch data mux (`a_lat`). This is the §11 EVAL path (conditions → encoder → mux), with the fabric source mux in front of it. In the first run, about 3 ns of the 6.4 ns (typ) was three unbuffered nets with fanout 31–35, which buffering removes (the "sized" rows).
- **EVAL (sized):** O1's `out_seq` → the 9-subscriber release term → `ofree` → `ready` → encoder → the CALL index mux.
- **EXEC:** `ex_rt` (routine or slot) → operand muxes (fanout 107 when unbuffered) → ALU → the zero/compare flag → RZ. At 8.3–10.7 ns (slow, plain) it is about as long as EVAL, and it is also comfortably inside 20 ns.
- **Latch writes:** the latch array times cleanly: write data borrows under 1 ns into the transparent phase. With the first, behavioural clock gate the gating check passed with +0.15 ns hold (ideal clock); the library ICG now used has its own checks inside the cell.

## 4. Area (Yosys, typ liberty, plain mapping, before placement)

| Block (one lane) | Cells | Flops | Latches | Area (µm²) |
|---|---|---|---|---|
| `trw_lane` (control, registers, EXEC muxes) | ~2,450 | 170 | 0 | 34,978 |
| `trw_alu` | ~580 | 0 | 0 | 5,850 |
| `trw_slots`, latch array (no read port) | ~950 | 16 | 700 (636 slot + 64 K), + 52 `lgcp` clock gates | 24,549 |
| `trw_slots` debug read port (52 × 16-bit word mux, used by R2) | | | | +9,350 |
| `trw_slots`, flop fallback (no read port) | 2,840 | 700 | 0 | 51,721 |
| Two consumer ports | 307 | 2 | 0 | 3,255 |
| **Lane total, latch slots** | | | | **~65,400** |

- **Three lanes, latch slots:** ~196K µm², 22 % of the 902K µm² 6x4 core, before placement density.
- **Latch vs flop slots:** latches save ~27K µm² and ~1,900 cells per lane (~80K µm² for three lanes).
- **Debug read port:** reading slots back (useful for host debug and for R2's test) costs ~9.4K µm² per lane, about 14 % of a lane. The final area numbers need a decision on whether phase 2 keeps it.
- **Against ARCHITECTURE §12:** the slot estimate (~90K µm² for three lanes) holds at ~74K. Lane control needs 3 × 170 = 510 flops against the "~0.4K" estimate, plus ~42K µm² per lane of logic. §12 should be updated after R2 with post-layout numbers.

## 5. What this does not show
- **Before layout.** No wire RC, no clock tree and skew, no placement. The TT flow's resizer will buffer and size the plain netlist, and routing will add wire delay. The "sized" rows bound the first effect; the margin above covers the second. The R2 hardening, a 2x2 project built around this lane's latch array, will give post-route numbers.
- **One lane and a harness,** not the chip. In the real floorplan the producer registers sit in pin units and other lanes, so the fabric part of the EVAL path gets longer wires. In the plain typical path that part (select decode, source mux, tag filter) takes about the first 1.9 ns.
- **Hold** is not meaningful before CTS. The slot store's clock gate is the library ICG `sg13cmos5l_lgcp_1` in synthesis (`ifdef SYNTHESIS` in `trw_slots.v`) and a behavioural latch + AND in simulation and lint. The first run used the behavioural gate in synthesis too; the latch rows above are from the re-run with the library cell (EVAL within ±0.4 ns of the first run).
- **Area** is Yosys's, not LibreLane's. LibreLane synthesizes with its own strategy and then resizes.

## 6. Spec gaps found by writing RTL from the documents alone

**Answered in D-033 (2026-09-24):** `ARCHITECTURE.md` §14 rules L8–L11, R5–R6 and H1. The spike matches every answer except G6 `KT` (§14 L8: with a non-input A, `KT` is ignored and `OT` applies). That must change before this lane becomes the phase 2 RTL.

The RTL had to pick an answer for each of these. The model has presumably picked one too; the text of `ARCHITECTURE.md` §14 / `ISA.md` should say which, so the RTL and the model provably agree. None of them affects the timing result.

| # | Gap | Where | Spike's choice |
|---|---|---|---|
| G1 | Which register / K is B for `BSEL = reg` / `k`? | ISA §4.1 | `IMM[1:0]` |
| G2 | A routine step: is it chosen at EVAL and executed in the next clock (like a slot), or executed in the clock it wins? | ISA §4.3, §5.3; §14 L2 | chosen at EVAL, executed in the next clock |
| G3 | A routine `OUT` whose output is full: is it still a "waiting step" that holds back non-urgent slots? | ISA §5.3 | no: it is not a candidate until its output is free |
| G4 | PEND[x] set by EVAL and cleared by EXEC on the same edge | §14 L4/L5 | set wins |
| G5 | How DJNZ reports "rd ≠ 0" to the sequencer; does it write RZ? | ISA §5.1 | RZ untouched; a separate signal |
| G6 | `KT` when ASRC is not an input; `CALL` with a register DST; `SETF/CLRF/CPYF` with arg 3 (RB is read-only) | ISA §3, §4.1, §5.1 | the latched I0/I1 head tag; CALL writes nothing; writes to f3 ignored |
| G7 | Slot latches have no reset, so V is unknown after power-up | §5.2, PHYSICAL §4 | the host must write all 48 slot words before RUN; RUN resets to 0 |
| G8 | Inconsistent numbers: PEND 4 bits (ARCH §5.1) vs 3 (ISA §2); "52-bit slots" (ARCH §5.2) vs 53; "RPC, RRET" (ARCH §5.1) vs "RPC, RIR" (ISA §2) | ARCH §5.1, §5.2 | ISA's values |
