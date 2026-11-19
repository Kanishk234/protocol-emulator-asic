# Memory-lane service envelope and timing-report correction

The compiler now derives a conditional SRAM service envelope directly from the
encoded routine words, rather than multiplying executed steps by four. The
memory showcase's longest routine needs **51 clocks**, including an unfavorable
SRAM rotation offset. The previous report printed 48 clocks for that routine;
that estimate must not be used as a memory-service guarantee.

| Routine | Words | Executed steps | SRAM accesses including entry | Service envelope |
|---|---:|---:|---:|---:|
| refresh | 2 | 3 | 4 | 19 clocks |
| store_byte | 9 | 10 | 12 | 51 clocks |
| advance_read | 5 | 6 | 7 | 31 clocks |

The endpoint runs from the clock of CALL selection to observation of completed
RET. Each entry-table read, instruction fetch and data read/write receives a
separate rotation access. With one lane slot every four clocks, an instruction
fetch's EVAL/EXEC and a load's writeback fit before the next eligible access.
Charging four clocks per access plus three for terminal completion gives
`4 * (1 + instruction_words + loads + stores) + 3`. The final three include
observation after the RET EXEC edge; starting at the lane's own rotation phase
misses that clock's not-yet-requested entry read.

The original step count correctly counted a load writeback as another step,
but a store's data write also needs its own SRAM rotation slot. A blanket
`4 * steps + 8` did not cover that access in the store routine. Execution-step
metadata remains unchanged and distinct from the corrected elapsed-time result.

## Explicit limits

This envelope assumes an initially idle routine pipeline, a continuously running
lane, one owned SRAM slot every four clocks, no selected reflex actions until
RET, and no host/configuration writes. It covers straight-line encoded ALU,
literal, load and store instructions ending in one RET. Branches, loops, OUT,
other SYS operations, malformed image boundaries and routine ALU CALL return
unsupported with no clock bound. Bounds do not trust `max_steps` metadata.

Stores must also remain outside the entry table and executed routine words.
Otherwise a routine could overwrite its future instructions and invalidate
the decoded path. The generic analyzer explicitly leaves store non-aliasing
unproved; the finite memory-showcase checks restrict the pointer to 0–255,
whose data table is separate from its entry/routine words. This finite domain
check is not a general dynamic address-range proof.

The compiler's ordinary report now displays this conditional envelope or an
explicit unknown reason. Unsupported routines still compile normally; their
execution-step analysis remains available. This change does not alter compiled
images or weaken their checks. No RTL, ISA, firmware, physical configuration or
official workflow is changed.

## Checks

The independent whole-chip model runs each of the three routines in both memory
variants at all four rotation offsets and all 256 pointer values: **6,144 runs**.
All finish within the emitted envelope and match the existing execution-step
counts. An always-ready urgent-reflex negative control keeps the routine busy
beyond that envelope, demonstrating why the no-interference premise cannot be
silently dropped.

Both RTL simulators run the actual compiled L1 slot/routine words through the
existing lane/SRAM harness: two variants, three routines, four rotation offsets,
and four pointer boundaries (0, 7, 8, 255), **96 cases per simulator**. They count
actual SRAM accesses and observe maximum completion latencies of 19/51/31 clocks.
The same runs retain all 2,080 existing closed ACK-token cases. Source, image,
log and XML hashes are in `phase3_memory_service_result.json`. This is finite
cross-checking of an architecture-derived conditional bound, not formal proof
or a new physical timing result.

## Consequence for the ACK gate

At a 50-clock I2C bit period, consecutive complete bytes ordinarily arrive at
least nine bit periods (450 clocks) apart. The 51-clock routine envelope suggests
substantial service margin, but subtracting those two numbers does **not** prove
queue freedom. Include L0 forwarding, L1 entry/reflex work, output consumption,
repeated START/STOP timing, delimiter preemption and the guard's multicast/select
window before using it as an arrival/service proof. Interrupted transactions
can introduce delimiters much sooner than the next full byte.

The conditional [ACK edge budget](PHASE3_ACK_EDGE_BUDGET.md) is unchanged. The
EEPROM/compiler-bound Phase 3 exit checkbox remains open. The remaining task is
an explicit normal-byte and delimiter traffic contract composed with these
service and pin-path bounds; no physical rerun is justified by report-only work.

The next [delimiter-service milestone](PHASE3_DELIMITER_SERVICE.md) extends this
API with an explicit finite interference budget and tests every injection clock
of one/two-command bursts. It does not infer that budget from wire traffic.
