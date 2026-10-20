#!/usr/bin/env bash
# Caller activates the project venv; preserve system Icarus/venv PATH priority.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/uart_spi_checks
for up in 0 1; do
  for sp in 0 1; do
    for mode in 00 01 10 11; do
      name="u${up}_s${sp}_m${mode}"
      make -C protocols/uart_spi/test UART_PRIMS="$up" SPI_PRIMS="$sp" \
        CPOL="${mode:0:1}" CPHA="${mode:1:1}" SIM_BUILD="sim_build/system12_${name}" \
        > "build/uart_spi_checks/${name}.log" 2>&1
      cp protocols/uart_spi/test/results.xml "build/uart_spi_checks/${name}.xml"
      python -m tools.autonomy.check_xml "build/uart_spi_checks/${name}.xml" --minimum-cases 1
    done
  done
done
