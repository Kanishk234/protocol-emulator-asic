#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/uart_i2c_checks
for up in 0 1; do
  for ip in 0 1; do
    name="u${up}_i${ip}"
    make -C protocols/uart_i2c/test UART_PRIMS="$up" I2C_PRIMS="$ip" \
      > "build/uart_i2c_checks/${name}.log" 2>&1
    cp protocols/uart_i2c/test/results.xml "build/uart_i2c_checks/${name}.xml"
    python -m tools.autonomy.check_xml "build/uart_i2c_checks/${name}.xml" --minimum-cases 1
  done
done
