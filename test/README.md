# TRIPWIRE top-port tests

`test.py` runs the reviewed UART TX, SPI-controller and I2C-controller cases against the Tiny Tapeout top. Firmware is compiled and loaded over the host SPI pins; reference models check the protocol pins. The same tests run under the unchanged official RTL and gate-level jobs. No internal design signals are accessed.

From the repository root:

```sh
source .venv/bin/activate
cd test
make
```

The Makefile includes the committed SRAM behavioral models in both modes. Its `PROJECT_SOURCES` matches `info.yaml`. Firmware compilation uses the generated 2-lane/4-unit software tables.

For gate-level simulation, copy the official final netlist to `test/gate_level_netlist.v`, provide the matching PDK in `PDK_ROOT`, and use Tiny Tapeout's Icarus13:

```sh
make GATES=yes
```

The official action performs these setup steps. Tests always compare with protocol reference models. Sigrok decoding also runs when `sigrok-cli` is installed; the official template jobs do not install it. Required-sigrok coverage for all22cases is recorded separately by routed replay44123392388 and the unit workflow. These are functional simulations, not SDF-annotated timing simulations.

The harness supports pad loopback but does not dump the full SRAM/gate hierarchy by default. Results are written to `results.xml`; protocol traces are ignored local VCD files.
