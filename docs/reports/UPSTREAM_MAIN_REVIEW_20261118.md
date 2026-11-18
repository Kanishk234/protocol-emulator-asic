# Upstream main review — 2026-11-18

Reviewed f1dbbaf5dd0e0cf67d507ecd1a9f3d619fe42d72 in an isolated source snapshot.
No merge, rebase, RTL change or upstream publication. Main now has the stronger
development baseline: integrated real2-lane/4-unit/512x16SRAM design,8x4,20ns,
official physical success, and firmware-only Phase3 work. Recommend concentrating
development there while preserving this independent branch as historical evidence.

## Independently verified evidence

[Official44189196098](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44189196098)
at e19556e succeeds in GDS, precheck, gl_test and viewer. Downloaded the complete
GDS_logs, submission, precheck and GL archives; full ZIP hashes match API digests.
Actual contents show:

- Precheck10/10; official gate tests3/3; no failures/errors/skips.
- Final native routeDRC0, KLayoutDRC0, LVS0, antenna nets/pins0/0.
- Extracted setup/hold violation counts0 and slew/cap counts0 at all3corners.
- All6actual max/min reports confirm native0.25ns uncertainty.
- Hold fast/typical/slow:+0.150773287/+0.391302668/+0.742154359ns.
- Aggregate setupWS0 is retained, not called positive global margin.
- Raw functional-frontier reports in extraction44031468510 show worst reported
  flop/output setup+11.807575/+7.647178/+0.163304ns fast/typical/slow. All6stock
  reports are byte-identical to official reports. Actual SPEF is identical after
  removing only DATE; normalizedSHA2562abe1c64d90e517c4b2362c2592ec642f93984cba168d1995b4045bc28be2e21.
- Submitted NL537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9
  and GDS2a16d4e6d8dc12d60ce355153b3e4c30fc58cdc7610dafe895a3224b299f28f8
  match the baseline receipts.
- [Full routed replay44123392388](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44123392388)
  succeeds. Downloaded combined XML has22unique executed cases, no bad/skipped
  entries; full ZIPSHA2565817c04ccac3e1612963c87caf75680118d37469a28b45aff352361c82844573.

This establishes extracted computational closure for the exact pinned flow.
The163psreserve is narrow and applies to the reported functional frontier;
ordinary all-endpoint latch checks remain independently required. No silicon,
analog-pad or SDF simulation claim follows.

## Findings

1. **Medium: ACK setup monitor can over-credit unstable SDA.**
   [i2c_memory.py45–54](https://github.com/Kanishk234/protocol-emulator-asic/blob/f1dbbaf5dd0e0cf67d507ecd1a9f3d619fe42d72/tools/protomodels/i2c_memory.py#L45)
   retains first_low with setdefault even if SDA returns high during SCL low.
   Reproduced37reported setup clocks despite only1contiguous low clock before
   SCL rise; requirement3. The37clock low phase matches the50/13profile. This
   is an oracle weakness, not an observed chip failure. Reset the stability
   start on SDA-high during SCL low; add pulse/reassertion and clean controls,
   then rerun model/RTL/official-netlist scenarios.
2. **SRAM checker waiver is real and disclosed.** D-185 disables unsupported
   SRAM MagicDRC and abstract-overlap fatality, while requiring whole-GDS CMOS5L
   KLayoutDRC. Ten reviewed abstract markers remain. Green is under this policy;
   do not call it rawMagic zero or final manufacturing acceptance.
3. **Phase3 is not complete.** Volatile I2C memory firmware now exercises
   page wrap, repeated START, current-address reads and write/readback. It uses
   both lanes and304/512SRAM words. Recorded local RTL and official-netlist
   simulation is valuable, but compiler-derived ACK bounds, third-party peer,
   abort/recovery coverage and remaining phase gates stay open. Analog/power
   integration assumptions remain documented limitations.

## Additional checks and recommendation

Maintained repo audit passes qualified physical inputs, official workflow bytes,
source lists, generated tables and documentation links.27CI-helper tests and
5controller timing/invalid-stimulus tests pass locally. Long protocol suites were
not rerun locally. Latest main test/docs/repo-audit/lint pass; unit's model and
Verilator jobs pass, Icarus RTL job remains active at review time.

Prioritize the ACK-oracle correction, compiler ACK bounds, peer/abort coverage
and further general firmware showcases on frozen hardware. Do not reopen
physical tuning without a specific measured need. No automatic branch migration
or new hardware adoption is authorized by this recommendation.

Our separate diagnostic44025267292 finished failure and dependent replay
44026980046 stopped; selector lockstep44027736274 succeeded. No failure cause
is inferred here. These results do not detract from main's official green result.

Reproducer for the monitor finding (project venv, main snapshot, PYTHONPATH=tools):

```python
from protomodels.i2c_memory import MemoryController
c = MemoryController(50, 13)
c._gen = False  # isolate observation from transaction generation
c._ack_window = {}
for _ in range(4): c.step(0, 0)
for _ in range(32): c.step(0, 1)
c.step(0, 0)
c.step(1, 0)
assert c._ack_window['setup_clocks'] == 37  # actual continuous low: 1
```
