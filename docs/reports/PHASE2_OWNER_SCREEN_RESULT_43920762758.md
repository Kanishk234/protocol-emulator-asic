# Owner screen43920762758: antenna-only failure, timing reserve still unproven

[Workflow](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43920762758), source755fea054d7532d2b26b2beb4a53658b96972364. The tool run completes; final source-bound screen gate correctly rejects two fresh antenna violations. No route was launched. Data: pad_owner_or/native_result_43920762758.json; raw artifacts remain in /tmp/tripwire-owner-screen-43920762758.

| Corner | Aggregate estimated setup WS | Hold slack, stock0.25ns uncertainty |
|---|---:|---:|
| Fast | 0ns | +0.0822082ns |
| Typical | 0ns | +0.289468ns |
| Slow | 0ns | +0.648025ns |

Fresh slew/capacitance/fanout counts are zero at every corner; final global overflow0. Fast hold is only0.0322082ns above the0.05ns gate, and is0.0256318ns worse than the pending-event reference. Setup has no reported negative aggregate value, but this does not establish positive usable reserve. The standard slow max report's first1000paths all end at latches with0slack; a functional-endpoint query is required before a positive-margin claim.

## Why the gate fails

Native antenna repair at stage43 reports zero violations. Stage44 timing repair/rerouting inserts44hold buffers; the fresh final antenna check reports:
- `_00381_` to hold8723/A (dlygate4sd3), then lane0 ex_asrc[1]. Cumulative Metal2 255.89/200 and Metal3 309.72/200.
- `net11460` to `_48450_/D`, fabric C1.pending_drop_n. Metal3 cumulative207.03/200. Summary partial159.33/200 looks safe but is not the violated cumulative quantity.

Both cells and net endpoints existed before the final timing pass. Do not call them newly inserted cells or infer diode deletion. Their reported violations emerge after repair/rerouting; this confirms the recurring flow-order problem, rather than an RTL protocol failure or an arbitrary gate threshold. Final STA state inherits antenna0 from an earlier stage; only the fresh source-bound antenna check is valid final evidence.

## Did owner factoring improve the physical design?

Not established. Local ideal-wire gain did not produce a qualifying native checkpoint. Final physical area690588um2 versus689744um2 for reference43390348317 (+0.12%); final total instance count43052 versus43101. Final named hold-cell count5106 versus5087 (+19). The smaller late-pass insertion44versus148does not mean lower total hold burden: earlier-stage insertion differs. Overflow stays0 in both. There is no owner extracted timing result, so do not claim its setup improved over the reference's -0.783631ns routed result.

## What follows

Keep the already running output-cache screen43941730264; it attacks the actual output-feedback timing cone and supplies a useful comparison. Inspect its fresh antenna and native hold results before selecting further work. Do not route this failed owner source under the old one-off diagnostic exception. Stock detailed routing can perform later antenna repair, as prior diagnostic43629225955 demonstrated, but that does not remove the user's current pre-DRT gate or guarantee setup closure. Any changed routing-exception scope must be explicit; final extracted/official gates remain fixed.

## Follow-up: which native controls actually address this failure?

Inspected pinned OpenROADdcf36133a369abc8f3c5e5738cd4d82e4903c0e0, [AntennaChecker.cc](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/ant/src/AntennaChecker.cc#L573). ratio_margin scales partial area/side-area limits in checkPAR/checkPSR. checkCAR/checkCSR do not accept that margin and compare cumulative ratios directly to LEF limits; cumulative repair initially requests one diode per violating net. Therefore increasing the margin is not a direct way to add cumulative headroom to these two failures. This is consistent with the older margin10→50experiment40570929866 producing byte-identical physical views; the historical engine cause is not independently established by current-source inspection. Do not spend another screen on this knob without evidence of a different affected rule.

Owner stage44 setup repair was not a no-op: it corrected one -0.130ns endpoint at U0 RX rt21 with3buffers and1pin swap, before inserting44hold buffers. Disabling that stage is not an acceptable shortcut to use the clean stage43antenna report; it would also skip required timing work and final routing evidence. Merely increasing antenna-repair iterations also cannot anticipate geometry exposed only after that repair ends.

Prepared manual read-only owner functional-setup audit: exact run/SHA/ODB binding, native engine/PDK checks, no repair/routing steps, repeated unchanged-baseline metrics, unchanged physical hashes and stock0.25ns report validation. It queries actual flop/output endpoints rather than the1000zero-slack latch paths.17focused tests pass; actual archived config and database hash validate. This does not admit the failed source to routing or waive any gate.
