# Phase 3: showcase firmware and deeper verification

**Status: in progress.** Entry is qualified Phase 2 hardware plus green cleanup CI on 82fef00 (test 44261361247, unit 44261361115, lint 44261361015, docs 44261360970, repo-audit 44261361423; nightly 44346919822).

## Goal

Demonstrate useful programmable devices on the existing chip, then strengthen confidence with independent peers, recorded captures, metamorphic tests, formal properties and compiler analysis. Build the full design for Basys 3 without altering official Tiny Tapeout workflow jobs.

## First milestone

Implemented a volatile 256-byte I2C memory target in firmware. One lane handles bus reactions and the other manages SRAM, keeping a read cache so the next byte does not wait for SRAM on the wire deadline. It uses 12 and 11 reflex slots, one pin unit and 304 SRAM words. No RTL, physical configuration, macro, encoding or official workflow changes.

The independent model and chip RTL exercise address rejection, current/random/sequential reads, repeated START, eight-byte page wrap, 256-byte read wrap and NACK/STOP recovery, with required sigrok decoding. The same scenarios also pass on the exact official final netlist, with zero skips/failures and required sigrok decoding. After the ACK-oracle correction: 24 focused checks included in 360/360 model/compiler regressions, plus successful RTL/official-netlist replay. The checker now rejects interrupted low intervals and reserves one observation clock; conservative setup bounds are 620/220/340 ns. Phase 2 hardware/signoff is unaffected. See [the milestone report](../reports/PHASE3_I2C_MEMORY.md) for source hashes and observed ACK setup. These checks are simulation evidence, not full EEPROM conformance, silicon testing or an exhaustive timing proof.

## Scope limits

The memory is SRAM-backed and volatile, writes commit immediately, and EEPROM write-cycle busy timing is not implemented. The original one-unit program has a completed-byte STOP-before-ACK recovery gap; the separate guarded firmware addresses the tested boundary using existing U1/uo7 selection feedback. See [the recovery report](../reports/PHASE3_I2C_RECOVERY.md) and [guard report](../reports/PHASE3_I2C_GUARD.md). Analog rise/fall times and uncharacterized pads remain unqualified. The independent RTL-peer milestone passes under both RTL simulators and on the exact official netlist. Conditional compiler ACK bounds now match the exercised model/RTL paths; generalized queue/arrival and deadlock proofs remain open.

## Next

Continue actual RTL formal proofs and the remaining decoder/compiler/FPGA gates; finite L4coverage now passes under the approved D-191timing premises; three recorded UART/I2C/SPI replays now pass and the UART multicast showcase now passes on existing units. The PS/2 malformed-frame/raw-capture audit and WS2812/DShot evidence review now close the combined functional protocol checkpoint. Standard/overdrive 1-Wire and SPI memory now pass model/RTL/exact-netlist checks in their declared scopes. Continue the actual integrated SRAM-rotation proof: arbitration lives in trw_chip plus lane/host enable gating; trw_sram only wraps the macro. Prove those actual logic cones and their composition rather than a copied standalone arbiter. Other phase checklist items remain authoritative and unchecked until their full requirements pass.

**Takeaway:** the qualified chip can gain a memory-device personality through firmware; Phase 3 is adding software and evidence, not reopening physical closure by default.

The compiler now excludes incompatible priority competitors and checks both scheduler modes. Twenty-four focused tests include 10,000 independent-model scheduler snapshots; the full suite passes 597 tests and all 22 firmware images are unchanged. This [local selection result](../reports/PHASE3_REACTION_SELECTION.md) does not yet establish an end-to-end ACK or deadlock bound and does not complete L6-FUZZ.

Opt-in [single-token ACK contracts](../reports/PHASE3_ACK_TOKEN_BOUND.md) now check the compare/flag/submission chain: address ACK becomes a visible output token within four clocks, write-data ACK within two, under explicit idle-pipeline/free-output/no-arrival assumptions. Both programs match the independent model and both RTL simulators for all 2,080 cases. The 636-test Python suite passes and all 22 firmware images remain unchanged. Full pin-path and environment-invariant bounds remain open; no additional exit box is complete.

The next [conditional edge-budget milestone](../reports/PHASE3_ACK_EDGE_BUDGET.md)
composes RX, lane and linked TX into 8/6 clocks to arm an ACK. The 716-test
Python suite passes, including 1,120 observed workload ACK paths; both RTL
simulators pass 350 internal ACK checks each. The exact official netlist passes
40 port-only ACK checks. A continuous-low negative control corrected the new
target-enable monitor before publication. All 22 images and qualified physical
inputs remain unchanged. General queue/arrival and guard-window invariants still
need analysis; this does not complete the EEPROM/compiler-bound exit gate.

Memory-service analysis found and corrected a compiler report underestimate:
the store routine needs up to 51 clocks, rather than the old 48-clock estimate,
because its data write needs a separate SRAM slot. The new conditional
[service envelope](../reports/PHASE3_MEMORY_SERVICE.md) is checked against 6,144
model runs and 96 cases per RTL simulator. Firmware and hardware are unchanged.
Delimiter interference and arrival contracts remain the next gap.

The [delimiter-service sweep](../reports/PHASE3_DELIMITER_SERVICE.md) now checks
one/two-command bursts at every active routine clock: 1,616 cases on the model
and each RTL simulator. A two-action interference premise gives a conservative
59-clock store envelope; the observed maximum is 52. The model's multicast
commands are accepted in one clock and two-command guard bursts settle within
25 clocks after first internal publication. A restored routine-busy guard
reproduces delayed delivery. The full Python suite passes 810 tests. The
wire-origin arrival count and external-event-to-guard bound remain unclosed.

The subsequent [wire-origin review](../reports/PHASE3_I2C_DEADLINE_EVIDENCE.md)
checks those premises in 198 guarded workloads: 1,586 delimiters and 2,354
routine executions, guard settled within 26 clocks of each wire event and at
least 12 clocks before the next first SCL rise. Actual reflex counts and every
observed 59-clock delimiter window stay within the explicit two-action budget.
The full suite passes 828 tests. Together with the existing compiler, RTL and
exact-netlist ACK evidence, this completes the I2C showcase checkpoint for the
declared tested guarded personality. Generalized arrival/deadlock certificates
remain a separate open compiler checkpoint; Phase 3 is not complete.

The next [SPI memory personality](../reports/PHASE3_SPI_MEMORY.md) serves
READ/FAST_READ from a 256-byte volatile window without host refill during the
transaction. It uses one lane, two existing units and 300 SRAM words. Model,
Icarus and Verilator checks pass at 250/333/500 kHz; the full Python suite passes
939 tests, with final four-phase model checks also passing. The official-netlist
replay passes both complete-read and abort/restart tests, including all three
rate profiles. An independent higher-level flash decoder also validates
the six complete-frame RTL/gate captures. No new hardware or official workflow
change; the combined protocol exit checkbox remains open.

The [1-Wire master profiles](../reports/PHASE3_ONEWIRE_OVERDRIVE.md) add genuine
standard-speed entry into overdrive, faster reset/ROM reads and standard-speed
exit using idle host reconfiguration. The peer stays alive throughout. The full
Python suite passes 952 tests; model and both RTL simulators plus the exact
official netlist pass entry, four presence corners, absence and ROM checks.
All three transition captures are byte-identical and independently decode.
A retained stock-decoder recovery warning is isolated to its synthetic reset
timestamp: actual bus recovery is 28.48 us, with independent control evidence.
Each profile uses one lane, U0, nine slots and 51 SRAM words; the previous 23
firmware images and all physical inputs remain unchanged. Phase 3 remains open.

The [PS/2 framing milestone](../reports/PHASE3_PS2_FRAMING.md) checks all start/parity/stop combinations at three clock rates: 144 model scenarios and 288 frames. The full Python suite passes 1,117 tests. Icarus, Verilator and the exact official netlist each pass three focused chip tests, including sixteen clock-complete fault/recovery frames. A pinned unmodified upstream decoder removes the need for a fabricated recorder clock; valid-start captures independently decode with their actual stop/parity bits. All 24 emitted firmware images and physical inputs remain unchanged. The combined SPI/1-Wire/PS2/WS2812/DShot functional gate is checked with finite scoped evidence; the all-L3-sigrok gate remains open because DShot lacks a decoder. Phase 3 remains incomplete.

The [UART multicast showcase](../reports/PHASE3_UART_MULTICAST.md) uses both existing lanes (3/2 slots) to send validated RX to the host and valid-byte echo. Eight model tests and both RTL simulators pass; exact official-netlist replay passes both 115200/460800-baud profiles in 97.01 seconds. Each profile captures seven DATA and three raw ERR tokens and echoes only valid bytes. All six TX captures independently decode. Host service is required: a deliberate sustained no-service test overruns RX. This is host capture, not the deferred SRAM recorder. The full non-slow Python suite passes 1,126 tests. Hardware remains qualified and unchanged; no extra phase exit gate is ticked.

The [recorded-device checkpoint](../reports/PHASE3_RECORDED_CAPTURES.md) passes for three complete pinned upstream hardware captures: 42 UART bytes, one I2C access including ACKs and five SPI bytes. Original source timing is preserved with less than20nsclock quantization. Model, both RTL simulators and the exact official netlist match sigrok decoding of the original files. A live-host SPI failure led to a bounded64-word firmware capture using existing SRAM, retaining the failed service case as a negative control. The full Python suite passes1,145tests. This closes only L3B-DUMPS for the named recordings; Phase3remains open.

The [L4-TAP milestone](../reports/PHASE3_METAMORPHIC_TAP.md) adds a deliberately unserviced observer to existing UART/SPI/I2C firmware. Sixteen paired model workloads compare517,960clocks; three blocking-observer negatives prove the comparator detects interference. Both RTL simulators and the exact official netlist pass all three paired cases, requiring unchanged protocol traces and host-observed timing while the tap drops tokens. Trace hashes and host observation checkpoints match across simulators. The full Python suite passes1,164tests. That milestone covered one of five L4 relations; LOOP/IDLE progress follows below, while SCALE/PERM remain open. A UART audit shows fixed four-clock launch latency does not scale with baud even though bit intervals do, so the SCALE time origin must be explicit before claiming exact global scaling.

[Two-lane loopback and idle insertion](../reports/PHASE3_METAMORPHIC_LOOP_IDLE.md) now pass for UART, SPI and I2C. Eight model profiles run baseline/two seeds, with disconnected-wire negatives and independent decoding; the full Python suite passes1,175tests. Both RTL simulators and the exact official netlist pass all three paired cases. Idle moves later real frame starts but preserves the returned bytes, and capture hashes match across simulators. The test-only I2C fixture uses a controller lane and a target lane that returns the last written byte through tied open-drain SDA pads; no hardware or production firmware change. Three of five L4 relations now have finite scoped evidence. SCALE/PERM and the full L4/Phase3exit remain open.

[Strict fast-path permutation checks](../reports/PHASE3_METAMORPHIC_PERM.md) now pass24raw-cycle mapping comparisons across UART, SPI controller and I2C target, with three wrong-owner negatives. Both RTL simulators and the exact official netlist pass3/3paired cases; trace hashes and host checkpoints match, and Python1,187tests pass. Production instructions and physical inputs remain unchanged. The native SRAM-backed I2C controller is an explicit counterexample to unconditional lane invariance: its grant phase changes pad timing while data remains correct. A matched-start-phase model diagnostic restores the trace, without normalizing it. The user approved D-191timing-domain/phase wording, now reflected in VERIFICATION.md; SCALE and hardware routine-phase checks still need implementation/evidence, and the full L4exit remains open.

The [final SCALE/native-phase milestone](../reports/PHASE3_METAMORPHIC_SCALE_PHASE.md) completes the finite L4checkpoint. Eight model SCALE pairs compare815declared programmed intervals; independent decoders and edge-error negatives remain active. Both RTL simulators and the exact official netlist pass4/4timing cases, with matching capture hashes and phase observations. The native routine case uses an actual pre-load clock and documented host TIME read to match SRAM grant phase; its unaligned trace still differs while data passes. Fixed I2C recognition latency stays separately measured at3clocks. The full Python suite passes1,198tests and all27production images remain unchanged. Only L4is ticked; decoder/formal/compiler/FPGA and final main-CI/physical requirements remain separate.

The first [native channel formal milestone](../reports/PHASE3_FORMAL_CHANNELS.md) passes locally: three unbounded proofs, reachability witnesses and five deliberate faults caught with counterexamples. Scope is one producer/four blocking consumers and a paired tap composition under static configuration; eventual consumption is conditional on readiness. Remaining formal properties and the aggregate gate stay open.

The [RX overrun proof](../reports/PHASE3_FORMAL_PIN_RX.md) now also passes unbounded, with blocked event/data and recovery witnesses and five fault controls. It covers the RX indication and native producer preservation; sticky unit flags and BITSYNC integration remain to be proved before full F-CHAN-4 acceptance.

[Lean pin-unit sticky integration](../reports/PHASE3_FORMAL_PIN_UNIT.md) now passes unbounded for default and qualified cache parameters, with reachability and five rejected fault controls. Full/BITSYNC safety remains unresolved. An invalid idle/stuffing configuration triggers a native status-collision assertion; correcting only its threshold removes that finite replay failure, without establishing a universal full-unit result.

The later qualified full-unit diagnostic FAIL is retained: an11-clock native replay produces simultaneous readback/frame-start status with overrun low. Its configuration/command admission needs review; the finite idle4control passes but is not an adopted restriction. See the integration report and BUGS. This blocks a full/BITSYNC proof claim, not the already qualified physical timing result.

The [four-token reduction and scratch repair](../reports/PHASE3_STATUS_MERGE_CANDIDATE.md) now identify a native P26status loss-accounting defect. The general merge candidate passes its finite queue matrix and both60-test pin suites, but is not adopted and lacks full formal/physical qualification. Qualified hardware remains unchanged.

The [D-192candidate queue and full-unit proofs](../reports/PHASE3_STATUS_MERGE_FORMAL.md) now pass unbounded with explicit interface premises, and their reachability tasks pass. Original native failure remains recorded; candidate adoption and physical qualification are still open.

The exact D-192candidate also passes55/55whole-chip protocol/showcase/metamorphic scenarios under Verilator with no failures/skips. Current local candidate verification is complete; physical evaluation and official requalification are next before adoption.
