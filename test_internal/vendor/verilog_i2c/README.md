# Independent I2C verification peer

Unmodified `rtl/i2c_master.v` from [alexforencich/verilog-i2c](https://github.com/alexforencich/verilog-i2c/tree/a65be4045e898a52e791c6ee71f8f79a7cd2e129), revision `a65be4045e898a52e791c6ee71f8f79a7cd2e129`. Copyright Alex Forencich; MIT license retained in COPYING and the source header. PROVENANCE.json records exact file hashes.

Used only in the external I2C testbench. It is not in info.yaml, ASIC RTL, synthesis sources or the official workflows. The upstream project is deprecated in favor of fpganinja/taxi; we deliberately pin this standalone Verilog controller for reproducible peer verification. No upstream waveform-generation code is shared with TRIPWIRE firmware or its Python model.
