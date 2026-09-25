# WARP — programmable protocol fabric

Research branch for the Jane Street Protocol Emulator ASIC Competition.
WARP explores a small FABulous-based eFPGA with a fixed configuration and
host-data shell, targeting Tiny Tapeout IHP CMOS5L in 6x4 tiles.

**Status:** phase 0. The tapeout top is still a placeholder counter.
Protocol implementations, the management shell and a physically validated
WARP fabric are not implemented yet. `anish_branch` starts from the
separate `efpga` history; `main` contains the team's TRIPWIRE direction.

Start with the [architecture review and experiment plan](docs/design/ANISH_RESEARCH_PLAN.md),
then the [phase checklist](docs/design/phases/PHASE0_SETUP.md) and
[worklog](docs/WORKLOG.md).

* [Configuration census and its limits](docs/reports/REFERENCE_CONFIG_CENSUS.md)
* [Tiny FABulous integration research](docs/notes/tiny_fabulous.md)
* [PRISM and other prior art](docs/notes/prior_art.md)
* [Organizer questions — draft, not sent](docs/notes/organizer_questions.md)
* [Architecture overview](docs/design/OVERVIEW.md)
* [Versions](docs/VERSIONS.md), [decisions](docs/DECISIONS.md), [claims](docs/CLAIMS.md)

## Development

Use Linux/WSL and Python **3.12 or 3.13** for the pinned FABulous/cocotb
combination. `WARP_PYTHON=/path/to/python3.12 bash scripts/setup_venv.sh`
selects an interpreter when creating `.venv`; it does not replace an
existing incompatible environment. Install the documented EDA tools,
activate the venv, then run `bash scripts/check_all.sh`.

The configuration auditor can run without EDA tools or third-party Python
packages in a Python venv:

```sh
python -m unittest discover -s tools/fabric_audit -p 'test_*.py' -v
python -m tools.fabric_audit.configmem path/to/LUT4AB_ConfigMem.csv \
  --frame-width 32 --frames 20 --expected-bits 616
```

The project uses the [Tiny Tapeout CMOS5L template](https://github.com/TinyTapeout/ttihp-verilog-template/tree/cmos5l).
See [the project datasheet](docs/info.md) and [simulation instructions](test/README.md).
