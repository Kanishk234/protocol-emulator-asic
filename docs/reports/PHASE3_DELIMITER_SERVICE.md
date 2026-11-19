# Memory service under delimiter interference

The service analyzer now accepts an explicit `reflex_budget`, the maximum
number of reflex actions selected before the active routine returns. It charges
one extra four-clock rotation per action. This is a conditional service result;
the number is a supplied interference premise, not an inferred arrival limit.

A selected reflex can postpone a ready routine EVAL and shift its completion
past an owned SRAM slot. Charging a complete four-clock rotation covers that
slip. All previous assumptions remain: running lane, one owned SRAM slot per
four clocks, no host/configuration writes, straight-line supported instructions
and no stores aliasing entry/routine words. A reflex budget does not establish
those assumptions or prove that an external waveform obeys the budget.

| Routine | No-interference envelope | With at most two selected reflexes | Observed sweep maximum |
|---|---:|---:|---:|
| refresh | 19 clocks | 27 clocks | 20 clocks |
| store_byte | 51 clocks | 59 clocks | 52 clocks |
| advance_read | 31 clocks | 39 clocks | 32 clocks |

The default compiler report retains the zero-interference envelope and its
explicit assumptions. The API rejects non-integer, negative and excessive
budgets; `reflex_budget_proven` and `arrival_invariants_proven` remain false.

## Injection domain and independent checks

The guarded memory program uses existing L0.O1 multicast to both the memory
lane L1.I1 and guard U1.tx. Its START/STOP commands are CTRL 0x3009/0x3002.
The model harness halts L0 after loading the unchanged compiled image, starts
one actual memory routine, and injects commands through the real L0.O1 producer.
It retains both blocking consumers and the U1-to-U0 output-feedback guard.
It does not inject external SDA edges or claim to generate a valid I2C waveform.

The sweep covers three routines, four rotation offsets, four bursts (START,
STOP, START/STOP and STOP/START) and each injection offset from zero through
the routine's zero-interference envelope minus one: **1,616 cases**. It uses
pointer 7 and payload 0xA5; the separate zero-interference suite covers all 256
pointers. Commands are held by the actual producer until both subscribers take
them, and every injected command must be consumed, including late commands
after RET. This avoids silently passing by ending the monitor at routine return.

Both Icarus and Verilator run **1,616 corresponding cases** on the actual L1
slot/routine words through the existing lane/SRAM harness. Both observe maxima
20/52/32 clocks, within the explicit two-reflex envelopes. The RTL harness has
held CTRL input words with the inter-word fabric bubble; it does not contain
U1, so it supplies no new RTL guard-settling measurement. Each simulator also
retains the 96 routine-service and 2,080 ACK-token cases. All three tests pass
without failures or skips. The full Python suite passes 810 tests.

## Multicast and guard observations

In the model sweep, both L1 and U1 take each visible command one clock after
its publication, including while the memory routine is busy. The guard settles
back to idle-high, with U0 selected, within these observed intervals:

| Burst | First visible L0.O1 command to settled guard |
|---|---:|
| START | 21 clocks |
| STOP | 7 clocks |
| START/STOP or STOP/START | 25 clocks |

These start at a published internal command. They exclude external-event
synchronization, RX publication, L0 scheduling and command production. They are
finite model observations, not a complete START-to-next-ACK bound. Existing
pin-level RTL/netlist recovery evidence remains separate.

The negative control restores `rb == 0` on L1's two delimiter consumers only
in the test instance. For a store starting at its unfavorable rotation phase,
normal firmware takes both delimiters before RET with one-clock acceptance
and a 25-clock guard-settling interval. The blocked version takes neither before
RET, delays the first memory acceptance to 50 clocks and guard settling to 58.
This reproduces the previously rejected multicast backpressure mechanism; no
production firmware change is made.

Source, image, model-metric, test-log and XML hashes are in
`phase3_delimiter_service_result.json`. Raw traces stay outside Git. All 22
firmware images, qualified physical inputs and official workflows are unchanged.

## Remaining closure

Derive a wire-origin arrival envelope that limits selected delimiter actions
during the memory-service window, including event-publication jitter and any
already queued commands. Compose external-event-to-command delivery with the
guard window, then check it against the earliest next byte/ACK. Do not infer
the two-reflex premise from ordinary complete-byte spacing: interrupted frames
can create earlier delimiters. The I2C/compiler-bound exit gate remains open;
there is no new formal, physical-signoff, exhaustive-recovery or silicon claim.

The later [wire-origin evidence review](PHASE3_I2C_DEADLINE_EVIDENCE.md) checks
event delivery, the guard deadline and actual arrival/reflex counts in the
declared workloads, and assesses the finite I2C showcase checkpoint separately
from the general compiler deadlock/overrun checkpoint.
