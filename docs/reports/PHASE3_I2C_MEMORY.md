# Phase 3 first milestone: SRAM-backed I2C memory firmware

## Implementation and scope

`programs/i2c_target_eeprom.trw` is a volatile 256-byte I2C memory target with a configurable seven-bit address, eight-byte page-write wrap, a persistent current-address pointer between transactions, repeated-START random reads and sequential reads wrapping at 256 bytes. Writes commit immediately. It is not a drop-in emulation of every 24xx02 variant: there is no nonvolatile retention, write-protect pin, write-cycle busy interval or vendor-specific address aliasing. Start from the supplied 0xFF image. Host changes to SRAM need a pointer refresh before using the read cache.

L0 retains the fast I2C address/ACK/data path. L1 services memory operations and keeps the current read byte cached. A direction or controller ACK token triggers a cached reply; a bounded routine prepares the next byte while the current byte is shifting. No protocol-specific hardware, ISA extension, helper unit, clock/config change or official workflow edit is involved. [The Phase 2 physical baseline](../BASELINE.md) remains unchanged. All 2 lanes are occupied by this showcase.

| Resource | Usage |
|---|---:|
| L0 reflex slots | 12 / 12 |
| L1 reflex slots | 11 / 12 |
| SRAM | 304 / 512 words |
| SRAM data | 256 words, one emulated byte per word |
| Pin units | U0 only |
| Routine bounds | refresh 3, store 10, advance 6 steps |

The routine bounds come from tripc and exclude external output stalls as documented by the compiler. Its generic seven-clock urgent-reaction text is not a context-specific proof of this complete ACK path. That compiler-analysis task remains open.

## Checks

The shared external controller drives complete-byte transactions and monitors ACK at the pads. Its timing checks enforce 1.3 us SCL low at 400 kHz and mode-specific START/STOP spacing; separate edge tests include the first data clock after START. Expected read bytes are fixed independently from firmware. The scenario covers the initial image, nontrivial writes and readback, address mismatch, pointer-only writes, repeated START, current-address reads, eight-byte page wrap, 255-to-0 read wrap, final-byte NACK and recovery. Both model and RTL checks require sigrok; decoding cannot silently skip. RTL also checks that the target never drives SDA high or drives SCL. ACK assertions enforce the applicable NXP data-setup minimum, including 20 ns quantization, and reject SDA changes during the sampled ACK-high phase.

- Model: eight combinations (addresses 0x50/0x2A; exact 100 kHz, 400 kHz, 1 MHz and 1 MHz short-high waveform) pass with no skips. Five additional checks reject an invalid 400 kHz low interval and independently inspect emitted SCL edges in all four profiles, including the first low phase after START.
- Chip RTL: one cocotb test executes three complete scenarios, at exact 400 kHz, exact 1 MHz and 1 MHz with SCL high for 13 clocks (260 ns).
- Regular model/compiler regression: 349 passed, non-slow suite.
- Exact official-netlist replay: 1/1 cocotb test passes all three corrected profiles with zero skips/failures, required sigrok decoding and explicit ACK setup checks (344.29 s runner wall time). The netlist is unchanged from successful official run 44189196098. Compact input hashes, XML hashes, resource usage and observations are in `phase3_i2c_memory_result.json`.

Observed minimum ACK setup before the SCL rising edge:

| Controller period / high phase | Model / RTL setup minimum |
|---|---:|
| 125 / 60 clocks (400 kHz) | 32 clocks / 640 ns |
| 50 / 25 clocks (1 MHz) | 12 clocks / 240 ns |
| 50 / 13 clocks (1 MHz, short high) | 18 clocks / 360 ns |

These are sampled digital pad-level observations at a 20 ns simulation clock, not WNS, extracted timing or characterized pad timing. The model additionally passes 100 kHz. Analog rise/fall behavior, mid-byte aborts, exhaustive traffic and a compiler-derived ACK bound remain unqualified. Independent RTL-peer interoperability is subsequently verified in [the peer milestone](PHASE3_I2C_PEER.md). The Phase 3 EEPROM exit item is not ticked by this milestone alone.

## References

- [NXP UM10204 revision 7, Table 11](https://www.nxp.com/docs/en/user-guide/UM10204.pdf): protocol timing reference. The short-high case uses the Fm+ 260 ns minimum high interval. Observed ACK setup exceeds the table's 100 ns Fast-mode and 50 ns Fm+ data-setup requirements for these simulated waveforms; this is not a full electrical-compliance claim.
- [Microchip 24AA02/24LC02B/24FC02 datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/24AA02-24LC02B-24FC02-Data-Sheet-20001709K.pdf): reference for memory addressing, page wrap and sequential-read behavior; the deliberate differences above remain part of this firmware's contract.

## Reproduce

Use the project venv and install sigrok-cli. Model checks:

```sh
python -m pytest -q tools/kernels/tests/test_i2c_target_eeprom.py
```

Chip RTL (Verilator version compatible with cocotb 2):

```sh
make -C test_internal/chip SIM=verilator COCOTB_TEST_MODULES=test_phase3
```

For gate replay, use Tiny Tapeout Icarus 13, the matching official PDK cell/UDP models and `NETLIST` pointing to the original successful submission. The make target selects `tb_chip_gl.v`:

```sh
make -C test_internal/chip GATES=yes SIM=icarus \
  NETLIST=/path/to/tt_submission/tt_um_tripwire.v PDK_ROOT=/path/to/matching/pdk \
  COCOTB_TEST_MODULES=test_phase3
```

Set the extracted Tiny Tapeout compiler's `-B` and VPI paths when using a cached installation, as described in scripts/gl_local.sh. This does not synthesize or modify the official netlist and does not perform SDF-annotated simulation. The exact official netlist identity is SHA-256 537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9 from run 44189196098.
