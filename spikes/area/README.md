# Area estimate spike (phase 2 task 2.0)

Estimates the whole chip's area before any chip RTL exists. Result and method: `docs/reports/AREA_ESTIMATE.md`.

- `ae_prims.v`: representative building blocks (timers, cursor, shifters, CRC, BITSYNC counters, pad selects, fabric producer and port, SPI slave, read-back muxes, configuration storage), written from ARCHITECTURE.md §4, §7, §9 and §14. **Not chip RTL.**
- `run_area.sh`: synthesizes each block alone with Yosys onto the cmos5l cells (typical corner) and writes `build/prims.tsv`. It needs the liberty cached by `spikes/r1_lane/run_r1.sh`.
- `estimate.py`: multiplies the block areas by the counts each chip part needs, reads the pin configuration layout from the generated spec tables and feature use from `programs/`, and prints the report tables. Run it in the venv.
