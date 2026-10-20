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

Verified configuration RTL SHA256: `d17c05bfe5ca002eb5ca09885727bee039766f815817c27a9b56da6041b7adc7`; event-late BITSYNC SHA256: `bb65c952124198014308a6b2c3eb74a11312d635a870b2466c741e7cff426066`. Full-suite XML SHA256: `b820f4885f6c2c27833fc08a33d140223546f18bcf721cf7cfe4448d71d1b409`. The native screen result is recorded below; no extracted timing result exists for this candidate.

## Native screen result — 2026-10-20

[Screen 39378465307](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39378465307), exact head `6d640f3`, completes in 2015.54 seconds without timeout but fails electrical reserve. Actual electrical violations are zero at all corners; antenna nets/pins are zero. Fast/typical/slow hold is +100.667/+221.363/+429.733 ps. Companion test/lint/unit/docs workflows passed.

Slow slew reserve utilization is 0.785857 on `_11513_` at `wire12720/A`, and 0.483185 on `_15192_` at `_41849_/S`, against the fixed 0.45 limit. The first net also exceeds typical reserve at 0.510384. Capacitance reserve passes. These are reserve misses, not actual maximum-transition violations; both distinctions matter.

The independent production capture parser gives setup minima +12.273766 ns fast, +8.347774 ns typical, and **+1.725550 ns slow**. Slow headroom improves 0.242503 ns over the original event-late wire150 screen, but is still 1.774450 ns below the unchanged +3.5 ns guard. The run stops at the earlier electrical reserve gate, so the stronger setup guard does not execute; the saved report independently demonstrates that it would fail too. Global setup WS remains0, which does not establish positive usable headroom.

Do not route this checkpoint, relax the gates or claim extracted timing improvement. Next inspect these exact source-bound nets and the updated worst configuration path. The local 153→22 load reduction was real, but this physical result shows it was insufficient to meet the chosen reserve. Keep the event-late routed baseline separately. Early evidence: `/tmp/tripwire-cfg-staging-gates-39378465307`; direct job log: `/tmp/tripwire-cfg-staging-job-39378465307.log`.

## Exact-netlist diagnosis and composed follow-up

The audited post-antenna netlist from screen39378465307 confirms the actual worst start `_49003_` is **U0 configuration word15 bit1, SJW[1]**, not a mode bit inferred from an older run. Its endpoint `_46962_` is `u_chip.g_unit[0].u_prod.tok[14]`. The report gives 2.180271ns of time borrowed at the launch latch and data arrival3.615038ns before the SJW arithmetic cone. Staging moved the limiting path; it did not remove every deep configuration-to-token path.

The final reserve offenders are distinct: `_11513_` is driven by `_37593_`/a221oi_1 and feeds wire12720/buf_1, with structural downstream endpoints in lane1 output/register/routine control; `_15192_` is driven by `_41848_`/nor4_1, feeds five mux select pins and two buffers, and reaches the16TX cursor eq flops. These are structural cone observations, not proof that every enumerated path is sensitizable, and neither is the configuration staging write-enable net.

Native electrical repair was active: its actual command uses max_wire_length150/slew_margin55/cap_margin55, finds68slew/27capacitance problems and2302long wires, and inserts4857buffers in2306nets, with zero resizes. Later timing repair inserts36hold buffers. These logs do not establish exactly when the final two reserve misses appeared; intermediate missing-route warnings alone do not prove incorrect final STA. Future physical repair work must distinguish these cases rather than assume an unused knob or a single failing stage.

The next isolated variant is **bs-resync-event-cfg-staging**: keep the verified staging module byte-identical and apply the previously proven resync arithmetic cancellation to the now-critical SJW path. This changes one hardware optimization relative to staging alone. It replaces sample-time evaluation through the corrected boundary with saturated expressions using the precomputed nominal sample time, without adding state or cycles. The two electrical cones are not directly rewritten, so reserve clearance remains a separate measured requirement.

Fresh evidence in `/tmp/tripwire-resync-cfg-staging-20261020`:892bit-clock equivalence points;403/385/445/399configuration equivalence points and10400phase checks per build;60full pin tests, five chip tests,2048L2comparison clocks. Focused helper/gate tests:92passed. Expanded protocol replay passes **22/22, zero failures/skips**, in 207.42 seconds under Verilator with independent decoders enabled. Evidence: `test_internal/chip/results_l3_resync_cfg_staging.xml`, `l3.log` and the source-bound `cfg_staging_receipt.json` in the composed trial directory. All owned local checks have finished. The dedicated verifier now checks both bit-clock and configuration modules; generic verification still rejects these variants to avoid using the wrong clock model.

Paired local mapping:26445→26550cells and395625.9888→397041.4098µm² standard-cell area (+105cells,+1415.4210µm²,+0.358%) over staging alone; resettable flops remain2266. Versus original event-late, total standard-cell increase is about1.620%. Same local recipe/library and unchanged SRAM, not native or routed area.

Prepared `gds-native-resync-cfg-staging-setup-reserve-screen`, binding configuration hash `d17c05bfe5ca002eb5ca09885727bee039766f815817c27a9b56da6041b7adc7` and bit-clock hash `c77f87ce20a8b2f7eec2b58b4db72476ccf4eb5fc89dde4d60b9461f486a346d`. AREA1,20ns, wire150/hold125, all electrical/antenna/reserve/hold guards and measured slow capture≥3.5ns are unchanged. No physical result yet; no DRT until qualification.

Combined full-suite XML SHA256: `111edc19756b247930c7fb2fd051776595c8d8d94508d423ecf0758185b41ec0`. Exact frozen-source comparison confirms only trw_pin_bs.v and trw_pin_cfg.v differ. The native screen remains unlaunched pending publication; every original gate remains mandatory.
