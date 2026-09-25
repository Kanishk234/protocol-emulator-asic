# Physical design and CI

Status: stub. Version 1 is written in phase 1.

## Hardening flow (how the fabric is integrated: flat or macro)
## Clock target and timing results
## Area breakdown (latest hardening)
## Routing limits and congestion history
## Workflows (what runs where, and triggers)
| Workflow | Trigger | What it runs |
|---|---|---|
| `test` (template) | every push | cocotb pin-level suite in `test/`, Icarus 12 |
| `gds` (template jobs) | push touching `src/`, `arch/`, `macro/`, `test/`, `info.yaml`, `docs/info.md` or the workflow; manual | hardening, precheck, `gl_test`, viewer. Concurrency `gds-<ref>`, **no cancel-in-progress**: a newer push queues behind a running hardening |
| `docs` (template) | template default | datasheet build |
| `fpga` (template) | manual | iCE40 build of the template design |
| `lint` (ours) | every push | `info.yaml`/Makefile source-list sync; Verilator `-Wall` and Icarus `-g2005` lint |

Local equivalents: `scripts/check_all.sh` (lint + all simulation tests), `scripts/gl_local.sh` (gate-level on a Yosys netlist with TT's Icarus 13).

## Measured hardening time
| Date | Commit | Design | `gds` job | precheck | `gl_test` | CI run | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-25 | a63877d | placeholder adder, 6x4, template `config.json` | 35.1 min | 12.3 min | 0.7 min, pass | 36170807513 | All green. Cell counts, utilisation and the CI LibreLane version are in the `GDS_logs` artifact (needs a GitHub login to download); fill in when fetched |

Budget: GitHub stops a job at 6 h. The empty 6x4 tile already costs about 35 min, most of it fixed-cost steps over the empty area, so a filled fabric will take longer; re-measure after the first fabric hardening.
