# Pinned versions

Every tool used by any flow must be listed. Local PATH order: DECISIONS D-007.

| Tool | Version / commit | Where it comes from | Notes |
|---|---|---|---|
| TT CMOS5L template | `cmos5l` branch, imported as commit beb67c3 | TinyTapeout/ttihp-verilog-template | CI actions pinned by tag `@ihp-cmos5l` |
| TT support tools | `ihp-sg13cmos5l` branch, d66cf17 (2026-09-21) | TinyTapeout/tt-support-tools | Local `--check-docs` only; CI uses whatever the action checks out |
| FABulous | FABulous-FPGA 2.2.0 (2026-09-11) | PyPI, `requirements-dev.txt` | Pulls FABulous-bit-gen 0.3.1, librelane 3.0.14. Needs Python >= 3.12 and the `python3-tk` apt package |
| OSS CAD Suite | release **2026-06-29** | [official release](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-06-29); local `/home/awsma/eda/2026-06-29/oss-cad-suite` | FABulous 2.2 compatible release; September 25 synthesis interface is incompatible. Keep the Linux installation path free of spaces. |
| Yosys | 0.66+179 (e74db6dea) | OSS CAD Suite 2026-06-29 | Reference runner rejects other Yosys versions |
| nextpnr | nextpnr-generic 0.10-82-g2b560ad0 | OSS CAD Suite 2026-06-29 | FABulous uses `--uarch fabulous`; demo timing is not CMOS5L STA |
| Icarus Verilog | 12.0 (local `/usr/bin`, CI `test`: Ubuntu 24.04 apt) | apt | matches CI. `gl_local.sh` and CI `gl_test` use TT's Icarus 13.0 build |
| Reference experiment simulator | Icarus 14.0-devel, s20260301-220-g78750c51d | OSS CAD Suite 2026-06-29 | Local fabric experiment only; not a claim that the CI simulator was run. Package manifest retained per run. |
| Verilator | 5.020 (local and CI `lint`: Ubuntu 24.04 apt) | apt | matches CI |
| SymbiYosys | from OSS CAD Suite 2026-06-29 | | |
| LibreLane | set by `tt-gds-action@ihp-cmos5l` (CI); 3.0.14 in the venv (FABulous dependency) | | Fill in the CI version from the first `gds` run log |
| PDK (IHP CMOS5L) | IHP-Open-PDK 2bbec755dc67ca3db0261c3d6163e15735d66710 | same revision as `tt-gds-action@ihp-cmos5l` | used by `scripts/gl_local.sh` |
| Python | 3.12.3 (original WSL setup); 3.12.14 (`.venv-fabric` reference run); CI `test`/`lint` use 3.11 | | FABulous needs >= 3.12; per-run package manifest is authoritative for the experiment |
| cocotb | 2.0.1 | `test/requirements.txt` | |
| pytest | 8.4.2 | `test/requirements.txt` | |
