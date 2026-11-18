# Phase 3 independent I2C controller peer

## What is independent

The external controller is the unmodified `i2c_master.v` from Alex Forencich's [verilog-i2c](https://github.com/alexforencich/verilog-i2c/tree/a65be4045e898a52e791c6ee71f8f79a7cd2e129), pinned at `a65be4045e898a52e791c6ee71f8f79a7cd2e129`. The MIT license, original copyright header and SHA-256 provenance are retained under `test_internal/vendor/verilog_i2c/`. Upstream is deprecated in favor of fpganinja/taxi; pinning makes this standalone verification dependency reproducible. The repository audit rejects source/license changes and mutable revision names.

Cocotb submits byte commands through the controller's AXI-stream interface. The third-party RTL generates SCL/SDA, samples target ACKs and returns read bytes. It connects only to TRIPWIRE's external pads through a wired-AND open-drain bus. Neither the TRIPWIRE Python controller nor its chip model drives these transactions. Sigrok independently decodes the recorded bus.

This core is a verification peer, not a protocol block added to the ASIC. It is excluded from info.yaml and the ASIC source list. The ASIC firmware, RTL, constraints, macros and all four official workflow files remain unchanged.

## Scenario

Each controller setting runs the same independently expected scenario:

- Write/read four distinct bytes and retain the current address across a NACK/STOP.
- Use a pointer write followed by repeated START for random reads.
- Issue a write to the wrong address. Unlike our Python controller, this RTL controller continues sending its two data bytes after the address NACK; the target must ignore all three bytes. Exactly three missed-ACK pulses are expected.
- Check eight-byte page wrap and 255-to-0 sequential-read wrap.
- Check read stream length and the controller's last-byte indication.
- Require sigrok's 14 decoded read bytes to equal both the expected data and the controller's AXI read stream.
- Assert open-drain behavior, target non-driving of SCL, and measured SCL phase limits.

## Actual bus timing

The upstream prescaler formula omits state-machine overhead, so results use observed clock edges rather than nominal settings. The passive monitor excludes START/STOP edges from data-clock measurements.

| Prescale | Minimum period | Minimum high / low | Maximum observed data-clock rate |
|---|---:|---:|---:|
| 31 | 130 clocks | 65 / 65 clocks | 384.615 kHz |
| 11 | 50 clocks | 25 / 25 clocks | 1 MHz |

Each clock is 20 ns. The fast test explicitly requires an observed 50-clock period. The slower setting honors Fast-mode's 1.3 us low interval. Exact 400 kHz and short-high 1 MHz tests remain covered separately by the [firmware milestone](PHASE3_I2C_MEMORY.md). These are digital simulations, not analog/pad characterization or full electrical compliance.

## Validation status

Final Verilator, system Icarus 12 and exact official-netlist/Tiny Tapeout Icarus 13 runs each pass 1/1 cocotb tests containing both profiles, with zero failures/skips and required sigrok decoding. The gate replay takes 246.90 s. Source/license hashes, XML hashes and measured clocks are bound in `phase3_i2c_peer_result.json`. The netlist is unchanged from official run 44189196098, SHA-256 537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9. L3B-PEER passes for these exercised scenarios; this does not complete Phase 3 or the broader EEPROM/compiler-bound checkpoint.

The earlier prescale-12 trial passed at 925.926 kHz; it was replaced by prescale 11 to exercise an actual 1 MHz maximum data-clock rate. A restricted-sandbox run passed the transaction assertions but returned empty sigrok output because of the known libusb restriction; required decoder checks are rerun outside that sandbox, not skipped.

## Reproduce

From the project venv with sigrok-cli:

```sh
make -C test_internal/i2c_peer SIM=verilator
make -C test_internal/i2c_peer SIM=icarus
```

The shared chip runner also accepts `GATES=yes NETLIST=/path/to/official/tt_um_tripwire.v PDK_ROOT=/path/to/matching/pdk`. Gate replay requires Tiny Tapeout Icarus 13 and its library/VPI paths, as described in scripts/gl_local.sh. The external peer remains the same unmodified source in both RTL and gate modes. Results belong to the named scenarios; compiler-derived reaction bounds, formal proof and exhaustive protocol conformance remain separate open tasks.
