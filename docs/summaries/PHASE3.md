# Phase 3: showcase firmware and deeper verification

**Status: in progress.** Entry is qualified Phase 2 hardware plus green cleanup CI on 82fef00 (test 44261361247, unit 44261361115, lint 44261361015, docs 44261360970, repo-audit 44261361423; nightly 44346919822).

## Goal

Demonstrate useful programmable devices on the existing chip, then strengthen confidence with independent peers, recorded captures, metamorphic tests, formal properties and compiler analysis. Build the full design for Basys 3 without altering official Tiny Tapeout workflow jobs.

## First milestone

Implemented a volatile 256-byte I2C memory target in firmware. One lane handles bus reactions and the other manages SRAM, keeping a read cache so the next byte does not wait for SRAM on the wire deadline. It uses 12 and 11 reflex slots, one pin unit and 304 SRAM words. No RTL, physical configuration, macro, encoding or official workflow changes.

The independent model and chip RTL exercise address rejection, current/random/sequential reads, repeated START, eight-byte page wrap, 256-byte read wrap and NACK/STOP recovery, with required sigrok decoding. The same scenarios also pass on the exact official final netlist, with zero skips/failures and required sigrok decoding. Focused checks: 13/13; model/compiler regression: 349/349. See [the milestone report](../reports/PHASE3_I2C_MEMORY.md) for source hashes and observed ACK setup. These checks are simulation evidence, not full EEPROM conformance, silicon testing or an exhaustive timing proof.

## Scope limits

The memory is SRAM-backed and volatile, writes commit immediately, and EEPROM write-cycle busy timing is not implemented. Mid-byte abort behavior, analog rise/fall times and uncharacterized pads remain unqualified. The scenario tests are not a third-party RTL-peer result. The compiler still lacks a context-specific ACK/reaction-bound proof.

## Next

Publish the first milestone evidence and require CI green; integrate an independent I2C controller peer; add the per-path compiler reaction analysis. Existing PS/2, 1-Wire, WS2812 and DShot examples should be audited and extended rather than recreated. The phase checklist remains authoritative, and its exit items stay unchecked until their full requirements pass.

**Takeaway:** the qualified chip can gain a memory-device personality through firmware; Phase 3 is adding software and evidence, not reopening physical closure by default.
