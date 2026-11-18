# Phase 3 I2C interrupted-transaction investigation

The qualified Phase 2 hardware remains unchanged. These are new firmware
qualification tests, not a new physical signoff or a claim of complete EEPROM
conformance. No Phase 3 exit checkbox is completed by this report.

## Passing scope

At 50 MHz, the controller uses a 50-clock period with 13 clocks high
(1 MHz, 260 ns high). Each case seeds bytes `12 A5 00 FF` at address `20`,
interrupts another transaction, and verifies those four bytes with a pointer
write followed by repeated START and read.

| Interruption | Recovery | Model cases | RTL cases |
|---|---|---:|---:|
| Address after 0–6 bits | STOP | 7 | 6-bit boundary |
| Payload after 0–6 bits | STOP | 7 | 6-bit boundary |
| Read after 0–7 bits | Nine clocks with SDA released, then STOP | 8 | 0 and 7 bits |

All 22 model cases pass. The complete model/compiler suite passes 382 tests.
The four representative RTL cases pass as one Cocotb test, with no skips,
open-drain assertions, a passive check that recovery STOP actually reached the
bus, controller readback, and required independent sigrok decoding.

Source: `tools/protomodels/i2c_recovery.py`,
`tools/kernels/tests/test_i2c_recovery.py`, and
`test_internal/chip/test_phase3.py::test_i2c_memory_recovery`.
The existing Phase 3 CI module discovers the new test without workflow edits.

Nine-clock bus clearing follows NXP UM10204 rev. 7.0 §3.1.16:
[I2C-bus specification](https://www.nxp.com/docs/en/user-guide/UM10204.pdf).
No analog pad, rise/fall time or real hardware result is claimed.

## Important unresolved boundary

The STOP sequence first drives SDA low and raises SCL, then releases SDA. After
seven prefix bits, that SCL rise completes an eighth bit. This is a completed
byte interrupted before its ACK clock, rather than an ordinary incomplete-byte
STOP. A payload can legitimately commit under our immediate-write contract;
old contents cannot simply be assumed to survive this sequence.

Model and pin-only RTL diagnostics both reproduce a failure to accept the next
address after this sequence for address and payload transfers. The passive RTL
trace contains a real STOP, followed by START, but the subsequent address is
NACKed. These cases are **not** included in the passing recovery claim.

An additional model-state diagnostic finds a pending one-bit low ACK across
STOP and the next START. It is driven at that START's first SCL falling edge,
corrupting the first address bit. An additional Icarus RTL internal-state diagnostic confirms the same mechanism: `rem=1` at the observed STOP and next START; the first subsequent SCL rise has controller SDA released, target output-enable asserted, SDA low, `rem=0` and return-to-idle pending. The diagnostic passes by reproducing the failure; it is not a successful-recovery test.
Existing generic transmit commands wait for linked transmission to
be ready; changing a cursor is not documented as canceling a transfer. No
hardware, ISA or architecture change has been made to work around this.

For an interrupted read, requesting STOP without clearing the bus may produce
no actual STOP because the target holds SDA low. RTL traces confirm this
distinction; those requested actions are not counted as observed STOPs.

## Decoder and evidence boundaries

Sigrok's byte decoder retains framing across the deliberately interrupted
mid-byte sequence in this test. The test preserves the full fault VCD, checks
the recovery STOP passively, and independently decodes the subsequent complete
transaction from its idle preamble in a second VCD. It requires exactly the
four expected read bytes, not a suffix of an arbitrary decoded stream. This
does not qualify sigrok's interpretation of the malformed prefix itself.

## Next

The exact official-netlist replay also passes all four cases (one selected Cocotb test, zero selected failures/skips, 319.34 seconds). The unrelated EEPROM scenario was filtered out in these targeted RTL/gate runs; its earlier separate evidence remains unchanged. Required sigrok and matching PDK models are retained. Source/log/XML hashes are in `phase3_i2c_recovery_result.json`. Functional simulation has no SDF annotation and is not a fresh physical timing result.

UM10204 §3.1.10 note 4 requires targets to recognize a fresh START even when it follows an improperly positioned transfer. The reproduced behavior is therefore a real recovery gap, not something to dismiss solely because the preceding sequence was malformed.

Next, evaluate firmware-only recovery using
existing primitives. If a hardware change is required, propose its general
purpose, cost and qualification plan before implementing it. Preserve the
qualified baseline as the fallback. Compiler reaction bounds and the actual
SRAM rotation proof remain open after this recovery work.
