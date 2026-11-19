# Guarded I2C memory deadline evidence

The guarded volatile memory personality now connects wire-origin delimiter
delivery, memory service and the compiler's conditional ACK budget in the
exercised workloads. This is simulation and conditional compiler analysis on
the unchanged qualified chip. It is not an unconditional protocol proof,
characterized pad timing or a physical signoff change.

## Wire-origin monitor

The monitor samples the resolved bus every model clock. Every SDA transition
with SCL continuously high must match, in order, an RX EVENT, the correct
L0 guard command, consumption by both multicast subscribers, and a settled
idle-high guard with U0 selected. It rejects missing, wrong or late endpoints.
For a START followed by an SCL rise, selection must settle strictly before that
first rise. The observation includes the guard's registered selection state.

The same monitor checks every memory routine from CALL to observed RET. It
counts actual selected reflexes while busy, rather than assuming their count,
and compares elapsed time to the decoded routine-service envelope with that
count. It also checks every 59-clock half-open window of observed wire events
and memory delimiter consumption for a maximum of two. These are checked trace
properties; they do not prove an arrival curve for arbitrary external traffic.

The regression covers eight complete memory workloads (four timing profiles,
two initial phases) and all 190 existing guarded recovery cases. The latter
include incomplete address/write/read prefixes, the completed-byte boundary,
STOP, repeated START, bus clear, timing profiles and clock shifts.

| Observation across 198 guarded workloads | Result |
|---|---:|
| Matched wire delimiters | 1,586 |
| Completed memory-routine executions | 2,354 |
| Wire event to visible RX EVENT | At most 3 clocks |
| Wire event to visible L0 guard command | At most 5 clocks |
| Wire event to settled guard | At most 26 clocks |
| Settled selection to next first SCL rise | At least 12 clocks |
| Selected reflexes during one memory routine | At most 2 |

The explicit two-reflex store-service envelope is 59 clocks. Actual routine
durations remain within the envelope computed from each observed reflex count.
No event, command or still-running routine may be dropped at trace completion.
Ten synthetic checks exercise missing/late RX and commands, wrong event/command
identity, late subscriber consumption, an unfinished guard, excessive reflexes,
slow routines and skipped observations. The earliest guard settlement is recorded
independently of routine return.

## How the I2C showcase criterion is assessed

The exit checklist asks for memory-target operation at 400 kHz and 1 MHz, ACK
deadlines in every run and agreement with the compiler's reported bound. Its
evidence is the combination below, not a claim that the conditional compiler
alone proves every possible bus history.

| Requirement | Evidence and scope |
|---|---|
| Functional memory target at 400 kHz and 1 MHz | Guarded memory report: model, RTL and exact official netlist; address handling, cached SRAM reads, immediate writes, wrap and recovery; required sigrok |
| Independent interoperability | Pinned third-party controller passes on both RTL simulators and exact official netlist; separate peer report |
| ACK reaction matches compiler | Token-bound report: all 2,080 query cases checked on model and both lane RTL simulators; address/write token bounds 4/2 clocks |
| Complete ACK path in exercised workloads | Edge-budget report: 1,120 model ACK paths, 350 internal checks per RTL simulator, and 40 port-only exact-netlist ACK checks; conservative arm bound 8/6 clocks |
| Guard/service premises in interrupted workloads | This monitor: 198 guarded workloads, every observed delimiter and routine checked; separate all-clock injection sweep stresses interference |

The guarded firmware uses two lanes, U0 plus existing lean U1, reserved uo7,
12/11 reflex slots and 304 SRAM words. It remains volatile SRAM-backed memory,
with immediate writes, not full nonvolatile EEPROM/write-cycle emulation.
The original one-unit firmware retains its documented late-ACK recovery gap.

The I2C showcase checkpoint can therefore be recorded for this declared,
tested guarded personality with the above evidence. The broader compiler
deadlock/overrun-analysis checkpoint remains open: universal queue/arrival
invariants, arbitrary malformed traffic and generalized program certificates
are not supplied by these observations. No other Phase 3 exit item is completed
by this result, and Phase 3 remains in progress.

## Reproduce and audit

```sh
source .venv/bin/activate
python -m pytest -q tools/kernels/tests/test_delimiter_path.py \
  tools/kernels/tests/test_delimiter_path_monitor.py \
  tools/kernels/tests/test_i2c_recovery.py
```

The full non-slow Python regression passes 828 tests. All 22 compiled images,
qualified physical inputs and official workflows remain unchanged. The receipt
`phase3_i2c_deadline_evidence.json` binds source hashes, the full regression log,
all 198 workload summaries and prior RTL/netlist receipts. Those earlier replays
remain historical evidence on identical firmware/hardware; this monitor adds
model observations and does not re-label them as new RTL or gate-level results.
