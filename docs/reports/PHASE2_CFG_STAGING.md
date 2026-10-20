# Unit-local configuration write staging

Status: isolated Phase 2 experiment, 2026-10-20. Main hardware is unchanged.

## Why this change

The exact routed event-late baseline has a shared host data register driving configuration and slot storage across both lanes and all four pin units. Critical bits 2/4 feed 153 latch D pins plus one NOR4 input through 51/49 buffers. Their incoming configuration-latch data paths arrive at 5.37/4.96 ns and borrow 4.01/3.55 ns. This is a measured distribution bottleneck, although it does not account for every downstream critical-path delay.

`bs_event_cfg_staging.patch` preserves the existing event-late BITSYNC change and changes only the pin configuration staging behavior relative to that baseline: `wdata_q` captures on a unit write, holds otherwise, and keeps synchronous reset to zero. The latch enables, restart, cached carrier predicate, pin interface, instruction set, clock period and visible write timing remain unchanged. There are no new architectural cycles or protocol-specific blocks.

## Behavioral verification

`python scripts/ci/verify_cfg_staging.py <fresh-directory>` archives frozen RTL/spec 3393eea with current committed test/firmware fixtures, regenerates only Python resource tables, and applies the reviewed combined patch. It retains raw proof/simulation evidence outside Git.

| Configuration | Differential phase checks | Sequential equivalence points |
|---|---:|---:|
| Basic, latches | 10400 | 403 |
| Basic, FPGA flops | 10400 | 385 |
| Full, latches | 10400 | 445 |
| Full, FPGA flops | 10400 | 399 |

The phase bench covers every address, idle bus movement, consecutive writes, invalid addresses, reset during writes and control changes during both clock phases. The proof retains configuration outputs, restart and the cached carrier predicate. It excludes only correspondence for intentionally changed idle staging state and its internal combinational predicate. Host inputs come from same-clock registers, matching trw_spi and the combinational decode in trw_host. Induction has a six-step cap; full latch proof closes at step 1. This is module sequential equivalence under that host drive model, not arbitrary asynchronous-input equivalence or whole-chip formal. Initial-state confidence comes from phase simulation including initialization/reset; no defined power-up latch contents are claimed.

Negative controls reverse the stage enable, capture on the wrong edge or disable the carrier predicate; all are rejected by the phase comparator. The generic timing verifier rejects this variant rather than silently applying its unsuitable generic clock model.

Both full and basic pin builds pass 60 tests each; the chip suite passes 5 tests and L2 compares 2048 clocks without divergence. Expanded protocol replay passes **22/22, zero failures/skips**, in 422.84 seconds under Verilator, with independent decoders enabled. Evidence: `test_internal/chip/results_l3_cfg_staging.xml`, `l3.log` and `cfg_staging_receipt.json` in the isolated directory. Focused tools/gate tests: 81 passed.

## Paired local mapping

Same Yosys flatten/dfflibmap/ABC recipe, same typical CMOS5L library, same frozen event-late source, macro blackbox unchanged. This is not the native LibreLane synthesis recipe or routed area.

| Metric | Event-late baseline | Unit-local staging |
|---|---:|---:|
| Mapped cells | 26301 | 26445 |
| Resettable flops | 2202 | 2266 |
| Latches | 2065 | 2065 |
| Standard-cell area, µm² | 390711.0816 | 395625.9888 |
| U0 data-bit4 latch D loads | 153 | 22 |
| Each basic unit data-bit4 latch D loads | 153 shared | 9 local |

All four unit staging nets are distinct after mapping. The two slot banks still share their original 104-latch broadcast; this experiment does not alter them. U0 has 24 total input loads including 22 latch D loads; each basic bank has 10 including 9 latch D loads. Added area is 4914.9072 µm², about 1.258% of this mapped standard-cell estimate. A faster write-data tree is a hypothesis until measured physically; enable muxes, added clock load and hold repair can offset the benefit.

## Next qualification

Prepared separate manual `gds-native-cfg-staging-setup-reserve-screen`, bound to both exact RTL SHA256s. It retains AREA 1, 20 ns, 2 lanes/4 units/U0 full/SRAM, density 56, wire 150, hold target 125 ps, 50 ps fast-hold acceptance, all corner electrical/reserve/antenna checks and the measured slow FF-capture ≥3.5 ns guard. No detailed routing until every gate passes. No official integration, phase checklist ticks or physical improvement claim.

Local evidence: `/tmp/tripwire-cfg-staging-verified-20261020`, including cfg_staging_receipt.json, phase/proof logs, map-baseline/map-staged and mapping_comparison.json. Raw logs and netlists are not committed.

Verified configuration RTL SHA256: `d17c05bfe5ca002eb5ca09885727bee039766f815817c27a9b56da6041b7adc7`; event-late BITSYNC SHA256: `bb65c952124198014308a6b2c3eb74a11312d635a870b2466c741e7cff426066`. Full-suite XML SHA256: `b820f4885f6c2c27833fc08a33d140223546f18bcf721cf7cfe4448d71d1b409`. No physical timing result exists for this candidate yet.
