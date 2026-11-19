# Recorded-device replay inputs

`manifest.json` pins three complete upstream sigrok-dumps files and their capture
READMEs at revision `0ad13477abc959d37fc9a5acbd23901c371c9c76`. The root README
releases dump files into the public domain unless otherwise stated. The chosen
capture READMEs identify physical recording hardware and do not override that
license. Their source hashes are verified alongside the SR archives.

Fetch once before direct pytest/cocotb runs:

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m capture_replay --fetch
python -m pytest -q tools/kernels/tests/test_capture_reader.py \
  tools/kernels/tests/test_capture_replay.py tools/kernels/tests/test_spi_capture.py
make -C test_internal/chip COCOTB_TEST_MODULES=test_capture_replay
```

Files stay in ignored `build/captures/`; raw recordings are not committed.
`check_all.sh`, the internal aggregator and our unit/nightly workflows fetch
and verify them explicitly. Missing or changed inputs fail, rather than skip.

The reader supports the selected one-byte digital SR layout. It preserves the
entire recording, all channel sample levels and the sample rate. It maps time
onto 50 MHz by exact integer arithmetic; each edge is delayed by less than one
20 ns clock. There is no cumulative rounding drift, trimming, inversion, idle
removal, pulse stretching or ideal-protocol regeneration. A held final sample
allows pending chip/host activity to complete after the recording ends.

UART and I2C results stream through HOST_OUT; SPI bytes are stored in the bounded
SRAM capture firmware and read back through the host. These are simulations
using third-party hardware recordings, not measurements of fabricated TRIPWIRE.
See [the report](../../docs/reports/PHASE3_RECORDED_CAPTURES.md) for current status
and limitations, including the original live-host SPI failure.
