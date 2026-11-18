# Firmware-only I2C recovery guard

`programs/i2c_target_eeprom_guard.trw` is a separate firmware personality for
the unchanged qualified Phase 2 chip. It uses existing selection, clock output
and multicast primitives. It does not replace the one-unit memory example,
change the architecture, or add a dedicated I2C hardware block.

## Mechanism and cost

U0 still handles SDA/SCL. Lean unit U1 drives output uo7, which U0 reads as its
select input through the existing internal output feedback. Deselecting U0
aborts its linked transmit shift and resets receive framing. No board jumper
or external component is needed; uo7 is reserved for this firmware and emits
the guard waveform.

L0 multicasts delimiter CTRL tokens to L1 and U1. START uses nine two-clock
cycles; STOP uses two. Repeated deselections cover late queued words as well as
the active ACK. The single-pulse prototype did not handle every repeated START
boundary. Nine cycles are an exercised firmware setting, not a new hardware
feature or an exhaustive cancellation proof.

L1 consumes delimiters through urgent reflexes even while a memory routine is
busy. Retaining the old `rb == 0` condition caused a phase-dependent failure:
the slow multicast recipient delayed later guard tokens. A negative control
restores that condition and reproduces failure; corrected firmware recovers.
The reflex changes state and consumes the delimiter without modifying the
routine's registers; the bounded routine still finishes.

| Resource | One-unit example | Guarded example |
|---|---|---|
| Lanes / reflex slots | 2 / 12 + 11 | 2 / 12 + 11 |
| SRAM / routines | 304 words / 3 | 304 words / 3 |
| Pin units | U0 | U0 + lean U1 |
| Protocol pins | uio0 SDA, uio1 SCL | Same, plus reserved output uo7 |
| L0 constants | Three | Four; r0 holds the eight-bit length token |
| Physical design changes | None | None |

## Verification scope

The model matrix exercises all zero-through-seven-bit address/write prefixes,
STOP and repeated START, and interrupted reads recovered with nine clocks and
STOP. It covers 100 kHz, 400 kHz, 1 MHz and 1 MHz with 260 ns high. No extra idle
delay is inserted after STOP. Thirty additional cases shift initial stimulus
by one, two and three clocks at both 1 MHz duty cycles. All 190 guarded cases
pass, as do the original 22 recovery cases. The complete non-slow model/compiler
suite passes 573 tests.

RTL passes three maintained tests: original memory scenarios, original recovery
coverage, and the guarded variant. The guarded test includes three normal
timing profiles and twelve fault/recovery cases run consecutively without
host reset or firmware reload between them. Corrected sampled ACK setup bounds
remain 620/220/340 ns. Required sigrok, open-drain checks and passive START/STOP
observations remain enabled. Independent decoding begins before the recovered
transaction; full fault traces remain available locally.

The pinned unmodified third-party RTL controller also passes both firmware
variants, each at its two existing profiles, including measured 1 MHz. It tests
normal interoperability, not deliberate malformed-prefix injection.

Both corrected exact official-netlist replays pass. The guard completes three normal timing profiles and twelve consecutive recovery cases in one selected test, zero selected failures/skips, 449.57 seconds. Two unrelated original tests are filtered out. The independent peer completes both profiles in one selected test, zero selected failures/skips, 220.00 seconds; its original firmware test is filtered out. All required decoder checks pass. Source/image/log/XML hashes are in `phase3_i2c_guard_result.json`. Superseded gate runs were stopped after the model alignment failure and are not counted as evidence.

## Limits and next step

The original one-unit program retains its documented late-ACK gap. This guard
is an explicit resource tradeoff, not a silent change to that program. Immediate
writes remain immediate: STOP preparation after seven payload bits completes
`0x66`, while repeated START preparation completes `0x67`; tests check the
committed value rather than assuming rollback.

This is finite simulation coverage, with no characterized pads, SDF annotation,
silicon experiment or full EEPROM/I2C conformance proof. Context-specific
compiler reaction bounds and the guard's worst-case timing/queue analysis remain
open; the Phase 3 EEPROM exit gate stays unchecked. Next: derive those conditional timing and queue bounds from the actual workload and compiler graph, preserving the finite scope of this simulation evidence.
