# TRIPWIRE

[![gds](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/gds.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/gds.yaml) [![test](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/test.yaml) [![lint](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/lint.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/lint.yaml) [![unit](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/unit.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/unit.yaml) [![docs](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/docs.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/docs.yaml) [![nightly](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/nightly.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/nightly.yaml) [![repo-audit](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/repo-audit.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/repo-audit.yaml) [![protocol-replay](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/protocol-replay.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/protocol-replay.yaml) [![fpga](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/fpga.yaml/badge.svg?branch=main)](https://github.com/Kanishk234/protocol-emulator-asic/actions/workflows/fpga.yaml)

A firmware-programmable protocol emulator for the Jane Street ASIC competition. Two reflex lanes, four timed pin units and a 512×16 SRAM fit in **8×4 IHP CMOS5L tiles** at a 20 ns clock period.

**Phase 2 is complete.** The full design passed the unchanged official Tiny Tapeout GDS, precheck, gate-level tests and viewer in [run 44189196098](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44189196098). The exact final netlist passed all 22 routed protocol cases. See the [qualified baseline and explicit SRAM signoff policy](docs/BASELINE.md) for evidence and limitations.

## Start here

- [How the chip works](docs/HOW_IT_WORKS.md)
- [Documentation map](docs/README.md)
- [Architecture contract](docs/design/ARCHITECTURE.md) and [ISA](docs/design/ISA.md)
- [Protocol evidence](docs/PROTOCOL_SUPPORT.md)
- [Layout viewer](https://kanishk234.github.io/protocol-emulator-asic/)

## Develop and test

```sh
scripts/setup_venv.sh
source .venv/bin/activate
python tools/gen/gen.py --check
python -m pytest -q -n auto -m 'not slow'
make -C test_internal
```

`scripts/check_all.sh` runs the local lint, synthesis sanity, model, top-level and white-box simulation checks. It needs Icarus, Verilator, Yosys and sigrok-cli. The million-cycle lockstep test is separate: `make -C test_internal l2`. Always use the project venv for Python and cocotb.

For local gate-level checks, `scripts/gl_local.sh path/to/official/netlist.v` uses the qualified CMOS5L models and Tiny Tapeout Icarus 13. With no argument it makes a synthesis-only smoke netlist; this does not replace official hardening or timing signoff.

## Repository layout

| Directory | Contents |
|---|---|
| `src/`, `macro/` | Qualified RTL, physical configuration and licensed SRAM views |
| `spec/`, `tools/` | Encoding source, generator, compiler, simulator and protocol models |
| `programs/` | Firmware examples |
| `test/`, `test_internal/`, `formal/` | Top-level tests, internal suites and scoped proofs |
| `scripts/`, `.github/workflows/` | Maintained development and CI entry points |
| `docs/` | Contract, phase gates, evidence and navigation |
| `spikes/phase2_stock_flow/cache_final_antenna/` | Retained qualification receipts referenced by baseline guards |

Hundreds of superseded timing experiments are preserved on the [Phase 2 archive branch](docs/archive/README.md), rather than presented as active workflows on main.

Contributors: Kanishk and Krithik. No real-hardware validation is claimed. See [LICENSE](LICENSE) and the SRAM's provenance/license files for third-party terms.
