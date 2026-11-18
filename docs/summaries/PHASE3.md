# Phase 3: showcase firmware and deeper verification

**Status: in progress.** Entry is qualified Phase 2 hardware plus green cleanup CI on 82fef00 (test 44261361247, unit 44261361115, lint 44261361015, docs 44261360970, repo-audit 44261361423; nightly 44346919822).

## Goal

Demonstrate useful programmable devices on the existing chip, then strengthen confidence with independent peers, recorded captures, metamorphic tests, formal properties and compiler analysis. Build the full design for Basys 3 without altering official Tiny Tapeout workflow jobs.

## First milestone

Implemented a volatile 256-byte I2C memory target in firmware. One lane handles bus reactions and the other manages SRAM, keeping a read cache so the next byte does not wait for SRAM on the wire deadline. It uses 12 and 11 reflex slots, one pin unit and 304 SRAM words. No RTL, physical configuration, macro, encoding or official workflow changes.

The independent model and chip RTL exercise address rejection, current/random/sequential reads, repeated START, eight-byte page wrap, 256-byte read wrap and NACK/STOP recovery, with required sigrok decoding. The same scenarios also pass on the exact official final netlist, with zero skips/failures and required sigrok decoding. After the ACK-oracle correction: 24 focused checks included in 360/360 model/compiler regressions, plus successful RTL/official-netlist replay. The checker now rejects interrupted low intervals and reserves one observation clock; conservative setup bounds are 620/220/340 ns. Phase 2 hardware/signoff is unaffected. See [the milestone report](../reports/PHASE3_I2C_MEMORY.md) for source hashes and observed ACK setup. These checks are simulation evidence, not full EEPROM conformance, silicon testing or an exhaustive timing proof.

## Scope limits

The memory is SRAM-backed and volatile, writes commit immediately, and EEPROM write-cycle busy timing is not implemented. Mid-byte abort behavior, analog rise/fall times and uncharacterized pads remain unqualified. The independent RTL-peer milestone subsequently passes under both RTL simulators and on the exact official netlist; see [its separate evidence](../reports/PHASE3_I2C_PEER.md). The compiler still lacks a context-specific ACK/reaction-bound proof.

## Next

Require correction CI green, then add recovery scenarios and per-path compiler reaction analysis. L3B-PEER now passes, including measured 1 MHz, with pinned unmodified external RTL and sigrok. The peer implementation is isolated in test_internal/i2c_peer and its pinned source/license in test_internal/vendor; see [the peer report](../reports/PHASE3_I2C_PEER.md). Existing PS/2, 1-Wire, WS2812 and DShot examples should be audited and extended rather than recreated. For F-ROT-1, the arbitration is integrated into trw_chip plus lane/host enable gating; trw_sram only wraps the macro. Prove those actual logic cones and their composition rather than a copied standalone arbiter. The phase checklist remains authoritative, and its exit items stay unchecked until their full requirements pass.

**Takeaway:** the qualified chip can gain a memory-device personality through firmware; Phase 3 is adding software and evidence, not reopening physical closure by default.
