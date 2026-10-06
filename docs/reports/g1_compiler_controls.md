# G1 compiler control and FSM mapping screen

Local runs `compiler_controls_20261005` and `compiler_fsm_20261005`,
2026-10-05. Same frozen G1, seed 1, existing design-set RTL/parameters and
slow-corner timing model throughout. No held-out tuning or hardware edits.

G1's eight-cell tiles share reset/enable wires. The existing compiler can
move infrequently shared controls into LUT logic via `WARP_MIN_CTRL`.
[Yosys dfflegalize documentation](https://yosyshq.readthedocs.io/projects/yosys/en/v0.64/cmd/index_passes_techmap.html)
explains this mapping threshold. These screens use the pinned tool; source
reports include its exact versions.

| Workload | Threshold 2: LCs / model MHz | Default 4 | Threshold 8 |
|---|---:|---:|---:|
| UART | 29 / 90.71 | 29 / 90.71 | 29 / 90.71 |
| SPI controller | 47 / 77.97 | 47 / 77.97 | 48 / 61.63 |
| I2C controller | 70 / 52.97 | 70 / 52.97 | 70 / 52.97 |

All nine compile/place/route and produce images. No improvement; retain 4.
Aggregate: `build/compiler_controls_20261005/summary.json`.

A second screen copies SPI/I2C sources into ignored output directories and
adds a Yosys `fsm_encoding` attribute only to the existing state register.
The [upstream FSM recoding command](https://yosyshq.readthedocs.io/projects/yosys/en/v0.54/cmd/fsm_recode.html)
and pinned local `help fsm_recode` support binary and one-hot encoding.
Original source files remain unchanged.

| Workload | Native: LCs / model MHz | Binary | Explicit one-hot |
|---|---:|---:|---:|
| SPI controller | 47 / 77.97 | 46 / 62.20 | 47 / 77.97 |
| I2C controller | 70 / 52.97 | Does not fit: 95 / 88 LCs | 70 / 52.97 |

Binary SPI saves one LC but loses model timing; binary I2C exceeds capacity.
Retain native mapping. This does not establish equivalence or behavior of
changed images: none were selected or loaded. Timing remains a screening
model, not a physical clock/rate claim. Summary and all logs:
`build/compiler_fsm_20261005/summary.json`.

## Reproduction

```sh
source .venv/bin/activate
export PATH="$PATH:/home/younix/oss-cad-suite/bin"
python spikes/compiler_controls/run.py --out build/compiler_controls_fresh
python spikes/compiler_controls/fsm.py --out build/compiler_fsm_fresh
```

Use fresh directories and the project tool pins. Separate compiler processes
isolate the threshold environment setting; neither runner launches hardening
or changes active routing inputs.

## Compiler diagnostics improved alongside the screen

`--strict-ports` now rejects missing port mappings before synthesis. Actual
negative check drops the new fault input and verifies rejection, with no
synthesis script emitted (`build/uart_fault_monitor_strict_20261005/result.txt`).
The complete mapped fault showcase compiles successfully with the option.

Place/route errors now write `failure.json`, retaining resource counts and
error/tool details. Over-capacity resources get a concise explanation.
Rebuilds clear prior success/failure reports. Actual 95-LC binary-I2C failure
checks the 95/88 diagnosis and removal of a deliberately stale success report:
`build/compiler_fit_diagnostic_20261005/{failure.json,verification.txt}`.
The source/report distinction prevents an earlier successful report from being
mistaken for the failed rebuild. Default omitted-port behavior is unchanged.

Final compiler/board regression:315tests pass in25.64s
(`build/compiler_host_unit_final_20261005.log`), including strict input/output
rejection, capacity versus placement advice, stale-report invalidation and
preservation of missing-tool errors. Fresh strict-port fault-demo build
`uart_fault_monitor_final_20261005` is byte-identical to the loaded tested
image. These are local results, not new CI evidence.
