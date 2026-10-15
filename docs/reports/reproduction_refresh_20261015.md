# Authenticated README reproduction refresh, October 15

[Clean reproduction38777288608](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777288608)
passes on **77edd2dfdc12184a9b69c98cfa5041e9137ac016**. The actual job runs
17 minutes on fresh Ubuntu24.04; only binary tools are cached. This validates
that revision's documented source/compile/RTL path. It does not validate later
6370e1f discovery/CI changes or establish physical/native/SDF timing.

**Later refresh with emitted bytes:**38780941472 succeeds on
8e4c117537401528814ff25fadd64de697654db5, including corrected discovery and
strict local protocol checks. Its artifact now contains all12 emitted images
(standalone UART plus11 examples). Each actual downloaded image's SHA256
matches its own same-job report; no image authentication is inferred solely
from a report. The14 XML records include loaded30/30 and cosim1/1, zero
default UART skips after discovery repair, and17 intentional idle-chip skips.
Result SHA256:
`013865c1e55ad1b476b5db36921f6a99bcd65db6bd4a7b94e579a67d909073f2`.
The earlier omission described below applies to38777288608 only. Original
primitive timing views remain missing; neither refresh is a timing signoff.

Downloaded artifact `clean-readme-reproduction-38777288608` is retained locally
under ignored `build/reproduction_refresh_20261015/`. Independent inspection
checks actual files, not merely the workflow's green conclusion:

* `result.json` reports that exact commit/run, `passed=true`, seven expected
  stages in order, every exit code0 and no timeout. Its SHA256 is
  `c5cecb94d3a75762dbea87cfb63cbfafedb164445cd307b6f28dda2239177927`.
* Recorded README SHA256
  `20c9d61ee122b99e0c9cc1c8ca0609ee219bda2cf67480827011a072e0fedfd8`
  matches `git show` at the exact revision. The result records the seven
  README commands and line numbers.
* Every one of14 retained XML files matches its recorded SHA256, testcase
  count and skip count. No failure/error element is present. The loaded
  suite has exactly30 passing cases with no skips; names match **all** tests
  in the default Makefile modules `test,test_bitstream` at that revision.
  Co-simulation has exactly1 passing case with no skips.
* All200 listed input-fingerprint records across12 compiler reports match
  their source bytes from that exact Git revision. All11 rebuilt-image hashes
  in the reports match the corresponding committed `test/bitstreams/*.wbit`
  bytes at the same revision. The rebuild stage performs the actual same-job
  byte comparison and exits0. No local compilation or EDA was performed.

## Actual census and environment

| Retained suite | Cases | Deliberate skips |
|---|---:|---:|
| Default idle chip |30|17 loaded-image tests |
| Internal primitives |2|0|
| Shell transaction UVM |1|0|
| CAN / I2C controller / I2C target |3 /6 /6|0|
| 1-Wire / SPI / SWD |5 /4 /4|0|
| Default UART |8|1 runtime-divisor test |
| UART capture / WS2812 |1 /3|0|
| Real-loaded fabric chip |30|0|
| UART source/fabric cosim |1|0|

The default UART skip predates the conditional-discovery correction in6370e1f.
It is explicitly allowed only in this default check_all path; it is not
relabeled executed coverage. Optional standalone monitor/fault/capture loaded
modules are outside the default30-case suite and need their own named evidence.

Actual versions retained in the result are Python3.12.3 in project `.venv`,
Icarus12.0, Verilator5.020, Yosys0.66+179/e74db6dea and sigrok-cli0.7.2.
The checked package pins match FABulous-FPGA2.2.0, fabulous-bit-gen0.3.1,
fabulous-fasm0.2.0, cocotb2.0.1, pytest8.4.2 and pyuvm5.0.0.
The nextpnr fetch stage succeeds; its retained fetch log identifies the pinned
2026-09-27 suite. Full pip-freeze and tool paths/version output are retained.
Not every transitive Python dependency or vendor library is content-pinned;
this is not a hermetic build claim.

| Command stage | Actual seconds |
|---|---:|
| Fetch nextpnr |25.01|
| check_all |162.45|
| Rebuild committed bitstreams |8.53|
| Compile documented UART |0.77|
| Audit UART inputs/image |0.06|
| Actual-loaded fabric suite |747.89|
| UART cosim |18.80|

## Artifact and scope omissions

The uploaded artifact contains compiler reports and logs, **not emitted image
bytes**. Independent review can compare the11 reports' image hashes to the
committed images, as above, but cannot rehash the standalone default UART
image from the download. Its report records image SHA256
`46170ac6041b5d401811988dbc10bf5705bfe491221c3fe3a196477bfc678443`;
the same-job `compile.audit` log records PASS for listed inputs and image.
Do not describe this as a separately downloaded/rehashed UART image.

The workflow's XML validation checks required named cases but is not a
replacement for independent full-census review; the latter was done here.
The result's listed-input provenance explicitly excludes recursive includes
and vendor binaries/libraries. Configuration/timing view coverage, missing
original G1 primitive SPEF and full mapped timing remain separate obligations.
No phase exit box is ticked.

## Fabric workflow observation

At inspection, earlier-revision fabric38777137217 completes SUCCESS on77edd2d:
both FABulous demo and WARP compile/load/cosim jobs pass. Its WARP job takes
21m23s, dominated by the real-loaded suite; the demo finishes in4m03s.
Corrected-revision fabric38778082028 on6370e1f has completed the demo and both
compile stages and is executing the loaded suite. These observations indicate
normal work rather than a proven stall; no workflow was cancelled. A pending
later run is not counted as successful by this report.
