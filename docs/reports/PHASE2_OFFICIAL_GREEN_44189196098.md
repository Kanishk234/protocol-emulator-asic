# Official full-design GDS green:44189196098

Verified revision:e19556e1df1e2f87d4c195af618adb67a8063852.
https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44189196098

The unchanged official workflow succeeds in all four jobs: GDS, precheck, gl_test
and viewer. This is the real8x4design:2lanes,4pin units,U0full,512x16SRAM,20ns.
Required main CI also passes at this revision: test44189195952,lint44189196138,
unit44189195981,docs44189195946.

| Check | Verified result |
|---|---|
| Detailed routing DRC | 0; runtime1h26m04s |
| Whole-GDS CMOS5L KLayout DRC | 0; empty fresh violation report |
| LVS | 0; circuits match |
| Antenna nets/pins | 0/0 |
| Setup/hold violation counts | 0 at fast,typical,slow |
| Slew/capacitance | No reported violations at any corner |
| Fast hold | +0.150773287ns;50psminimum satisfied |
| Typical/slow hold | +0.391302668/+0.742154359ns |
| Ordinary aggregate setupWS | 0 at every corner; not relabeled positive |
| Actual functional setup reserve fast/typical/slow | +11.807575/+7.647178/+0.163304ns; provenance below |
| TT precheck | 10/10; independent XML review, no skips |
| Official gate-level protocols | UART/SPI/I2C3/3; independent XML review, no skips |
| Full routed protocol suite | Exact official final netlist already passes22/22 in44123392388 |
| Viewer | Success; full rendered design image inspected |
| GDS job / complete workflow | 2h58m43s /3h07m50s |

Final routedODB357f01366aea053ca83db4b035625033424378aecc5ff17addaf4711421b00d4
and post-fillNL537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9
exactly match the qualified route/extraction and22-case replay. All six official
max/min corner reports are byte-identical to44031468510. Extracted SPEF differs
only in itsDATEline; all capacitance/resistance data are identical. The positive
functional reserve from that source-bound audit therefore applies to the same
physical data; no additional synthetic timing result or new constraint is used.
Stock uncertainty remains0.25ns. The163psslow reserve is narrow, not a guarantee
for future hardware/tool changes.

Submission GDS SHA256:
2a16d4e6d8dc12d60ce355153b3e4c30fc58cdc7610dafe895a3224b299f28f8.
The official submission's final Verilog also has the exact22-case netlist hash.
PDK is CMOS5L/Ciel89d42ee, LibreLane3.1.0.dev4, recorded in submission metadata.

D-185signoff policy is explicit: unsupported SRAM MagicDRC is not run and its
abstract-overlap error gate is waived; actual whole-GDS KLayoutDRC0and all other
listed checks remain required. The10raw obsm4/metal4markers are byte-identical to
the independently reviewed SRAM-only inventory in44138149950. There are no new
unexplained overlap markers. Do not claim zero rawMagic markers or that every
Magic check passes. Main RTL/physical recipe and official jobs are unchanged by
this checker-policy adoption.

The fit is now measured:57.14%reported utilization excluding fill,
645003um²standard cells plus45309um²macro in1208170um²core;2418flops,
2071latch bits,42951standard cells and101728total instances including58776fill.
This satisfies the routable-budget gate; earlier6x4estimates remain historical.

Current-revision L2 refresh now passes1,000,000clocks with0divergences
(4781.64s). Clean RX/cursor baselines pass and the injected priority/cursor faults
are caught at clocks99/326. Evidence:l2_result_e19556e.json. Every Phase2exit item
has evidence on the verified revision; final documentation-publication CI must
be green before Phase3entry. No hardware/silicon or exhaustive formal claim.
