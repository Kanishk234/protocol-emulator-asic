# Extracted electrical and timing repair priorities

Run [38305592967](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38305592967), head2d73b6fe4b3ee22337fe7db2240cda7761dcda5e, artifact11774829067, completed detailed routing with zero route DRC, passed routed netlist conservation and completed extraction. The Python electrical parser then stopped because OpenSTA omitted zero-violation sections. BUG103 fixes that parser using explicit zero totals only. Independently re-auditing all three saved checks reports still fails the physical requirements.

| Corner | Setup WS ns | Hold WS ns | Slew | Fanout | Cap |
|---|---:|---:|---:|---:|---:|
| fast | 0 | 0.0000215383 | 0 | 9 | 1 |
| typical | 0 | 0.0810825874 | 8 | 9 | 1 |
| slow | -1.0088126176 | 0.2183033816 | 93 | 9 | 0 |

The fast hold result is0.0215ps, not21.5ps; the acceptance gate remains50ps. Route DRC and antenna counts are zero. No extracted qualification or official signoff is claimed. Correcting the parser must not make this run physically qualified.

## Concrete repair targets

The1000-path extracted reports contain73negative setup paths:71launch at configuration latch48179 (unit0 config word0 bit4), with worst endpoint47345 (dropped67). Two launch at48112. Shared stages place7221/24875 occur on56negative paths,24876on55,30202/37714on52,37732on22. These identify actual shared physical cones; path counts are limited to the saved report, not an exhaustive proof.

A small first sizing candidate preserves logic and uses existing library variants:

| Instance | Change | Shared negative paths | Added area um2 | Allocated displacement um |
|---|---|---:|---:|---:|
| place7221 | BUF1 to BUF2 | 56 | 1.8144 | 0 |
|24876 | INV1 to INV2 | 55 | 1.8144 | 0 |
|30202 | NOR3_1 to NOR3_2 | 52 | 7.2576 | 10.44 |
|37732 | NAND2_1 to NAND2_2 | 22 | 3.6288 | 0 |

Offline site allocation against actual final DEF and pinned LEF finds complete nonoverlapping footprints for all four, total14.5152um2additional cell area. This is a proposal, not an applied ECO, timing improvement or legalization proof. O21AI and NAND3 have no stronger matching variant in this library; their overloaded outputs need bounded local isolation/splitting rather than nonexistent cell upgrades. Increasing one cell can increase upstream load, so evaluate the entire shared path after any change.

Fast min report contains19paths below50ps. Worst is47942(unit1 config word6 bit2) to46591(unit1 RX rt3); next worst endpoint46611is19.168ps. Use endpoint-local data delay with exact sink conservation; do not change clocks or relax constraints. Recheck slow setup after each proposed hold fix.

The93slow slew rows map to19nets. Leading grouped loads:21090(9rows,26706/O21AI),10222(9,35866/NOR3),19656(8,25254/O21AI),04463(7,29453/NOR2),04499(7,29540/NOR2),04427(6,29406/NOR4). SRAM address0/1/3, MEN and one additional net each contribute a singleton. Typical NOR4 output04427reaches2.91ns versus2.5074ns limit. SRAM DOUT5cap is0.064710pF fast versus0.064pF limit, requiring a very local output isolation/load reduction.

All9fanout violations include diode loads. Actual finalDEF inventory with4load branch budget identifies19candidate buffers: place7983has11loads/4diodes;45614,45869,45870,45965 and place8805/8892/8920/9341have9loads/1diode each. Treat diode protection as retained circuitry. This inventory is not a complete repair plan: adding these buffers alone does not fix the setup, hold or all slew violations.

## Next experiment contract

Use actual extracted reports and finalDEF SHAad54425d496dcc532e919bad25836c9b0b6a4de9fe0d0c2531cd1a9b1c53bca0 to prepare exact source-bound repairs. Keep20ns, full2/4hardware and all constraints unchanged. Preserve logic/reset/clock connectivity and antenna cells. Measure the physical corrections using extracted parasitics or a calibrated clean-route continuation; do not call the prior estimated-zero screen an extracted margin. Reject regressions and keep zero electrical,50pshold, setup>=0, zerooverflow/antenna gates before any further expensive route. The already completed route need not be repeated just to recover parser evidence. GL/official-flow integration remain dependent on a qualified final checkpoint.

## Fixed-SPEF sizing sensitivity experiment

Prepared `gds-extracted-sizing-sensitivity` runs seven stock OpenSTA cases on the exact extracted NL and existing SPEF from38305592967: unchanged baseline, each of the four small upgrades individually, all four together, and the same combination with BUF4/INV4 input stages. No physical routing or ODB mutation occurs. Baseline must reproduce source all-corner setup/hold within1e-6ns, including the real failures, before candidates run. All original connectivity/cell identities are retained and only reviewed masters change. Each case exports fresh all-corner timing/electrical results with `fixed_spef=true`, `physical_qualified=false`; altered cell sizes can change pin geometry/capacitance and require physical legalization/routing/re-extraction before adoption. Seven actual-source conservation checks and30focused localtests pass. The experiment is diagnostic and must not be interpreted as zero-violation signoff.

### Sensitivity baseline launcher correction — 38314443440

The first sensitivity attempt fails with `KeyError: odb`: pinned LibreLane STAPostPNR accesses its optional ODB for filtering unannotated-net reports after timing analysis. The corrected diagnostic retains the exact source ODB for that filtering only; no resized physical geometry is claimed. OpenSTA timing reads the hypothetical netlist and original SPEF, with unchanged signoff constraints. Input metrics remain empty. Pinned MultiCornerSTA stores fresh aggregate results in `state_out.json`, so the helper reads that file and requires every fresh corner report rather than an OpenROAD-only `or_metrics_out.json`. BUG104 and35focused regression tests cover both contract issues. Baseline reproduction still gates all candidate cases; no detailed routing or physical qualification is permitted.

### Sizing results — 38315236792

Actual artifact11777610336 reproduces source baseline exactly. Fixed-SPEF slow setup results:

| Case | Slow setup WS ns | Gain vs baseline ns |
|---|---:|---:|
| baseline | -1.008813 | 0 |
| place7221 BUF2 | -0.628672 | 0.380140 |
|24876 INV2 | -0.795021 | 0.213792 |
|30202 NOR3_2 | -0.672397 | 0.336415 |
|37732 NAND2_2 | -0.672397 | 0.336415 |
| four small upgrades | -0.413884 | 0.594929 |
| stronger BUF4/INV4 inputs | -0.413884 | 0.594929 |

Every case retains fast hold0.0215ps and93slow slew violations; no physical qualification. Stronger input cells do not improve global worst slack further. The combined case's new worst path still launches at48179 but ends at46883, followed by46391/46884. Its slow shared delayhold12828contributes0.611189ns, and NAND3_24811drives0.116261pF with1.576679ns slew. NAND3has no stronger libraryvariant;INV24812is a reviewed adjacent sizing option.

Prepared follow-up diagnostic cases retain the four small upgrades and compare shared delay variantsDLY4SD2/DLY4SD1, with/withoutINV24812_2. These remain noninverting A/X delaycells, with unchanged connectivity and existingextractedSPEF. Baseline must reproduce source before cases run; measure allcorner hold after reducing shared delay. No delay bypass, clock change, constraints relaxation, physicalqualification orDRT is allowed. Allsixactualsource conservation checks and43focusedtests pass. A physically legalized/routed implementation remains required for any promising combination.
