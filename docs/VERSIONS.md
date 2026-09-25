# Pinned versions

Every tool used by any flow must be listed. Local PATH order: DECISIONS D-007.

| Tool | Version / commit | Where it comes from | Notes |
|---|---|---|---|
| TT CMOS5L template | `cmos5l` branch, imported as commit beb67c3 | TinyTapeout/ttihp-verilog-template | CI actions pinned by tag `@ihp-cmos5l` |
| TT support tools | `ihp-sg13cmos5l` branch, d66cf17 (2026-09-21) | TinyTapeout/tt-support-tools | Local `--check-docs` only; CI uses whatever the action checks out |
| FABulous | FABulous-FPGA 2.2.0 (2026-09-11) | PyPI, `requirements-dev.txt` | Pulls FABulous-bit-gen 0.3.1, librelane 3.0.14. Needs Python >= 3.12 and the `python3-tk` apt package |
| OSS CAD Suite | release **2026-06-29** | YosysHQ/oss-cad-suite-build, unpacked to `~/oss-cad-suite` | The release FABulous 2.2 pins (`OSS_CAD_SUITE_VERSION` in `fabulous_repl/helper.py`: "Yosys master broke FABulous"). 2026-09-25 was tried first: its `synth_fabulous` no longer ships `prims.v`, so the demo fails in Yosys |
| Yosys | 0.66+179 (e74db6dea) | OSS CAD Suite 2026-06-29 | |
| nextpnr | nextpnr-generic 0.10-82-g2b560ad0 | OSS CAD Suite 2026-06-29 | FABulous uses `--uarch fabulous` |
| Icarus Verilog | 12.0 (local `/usr/bin`, CI `test`: Ubuntu 24.04 apt) | apt | matches CI. `gl_local.sh` and CI `gl_test` use TT's Icarus 13.0 build |
| Verilator | 5.020 (local and CI `lint`: Ubuntu 24.04 apt) | apt | matches CI |
| SymbiYosys | from OSS CAD Suite 2026-06-29 | | |
| LibreLane | CI `gds`: **3.1.0.dev3** (default `librelane-version` of `tt-gds-action@ihp-cmos5l`, 3412659, pip); 3.0.14 in the venv (FABulous dependency); 3.0.0 in the FABulous LibreLane plugin (Nix) | tt-gds-action `action.yml` | Tile hardening uses the plugin's pin |
| Nix | 2.35.2 (multi-user, systemd) | nixos.org installer; FOSSi binary cache in `/etc/nix/nix.conf` | Tile/fabric hardening only |
| FABulous tile library | `mole99/fabulous-tiles` 7999e5a + `spikes/tile_cmos5l/cmos5l.patch` (D-010) | GitHub | Its flake pins `librelane_plugin_fabulous/1.10.2` (the plugin reports itself as 1.2.0) |
| Tile-flow tools (from that flake) | LibreLane 3.0.0; OpenROAD dcf36133; KLayout 0.30.7; Magic 8.3.623; Netgen 1.5.316; Yosys 0.62 | Nix, FOSSi cache | Differs from the CI `gds` job's LibreLane (3.1.0.dev3) |
| PDK (IHP CMOS5L) | IHP-Open-PDK 2bbec755dc67ca3db0261c3d6163e15735d66710 | same revision as `tt-gds-action@ihp-cmos5l` | used by `scripts/gl_local.sh` |
| Python | 3.12.3 (WSL); CI `test`/`lint` use 3.11 | | FABulous needs >= 3.12 |
| cocotb | 2.0.1 | `test/requirements.txt` | |
| pytest | 8.4.2 | `test/requirements.txt` | |
