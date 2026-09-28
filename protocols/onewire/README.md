# 1-Wire controller: held-out protocol H2

Written in phase 4, after `hw-freeze`, for the frozen chip (`docs/design/HELDOUT.md`; results in `docs/reports/heldout_results.md`). The architecture was never tuned for it.

- **File:** `onewire_top.v` (user-design top). `PRIMS = 1`: two WARP hard timers (a 1 µs tick; a microsecond one-shot with RELOAD 959 whose `half` load is the 480 µs reset pulse and full load the 960 µs recovery) and a hard shift register (the byte, LSB first), ARCHITECTURE §8. `PRIMS = 0`: plain logic, same behaviour.
- **Line:** `dq` on FAB_IO0 (`uio[0]`), open drain: `dq_oe` pulls low, released otherwise; **needs a pull-up** (e.g. 4.7 kΩ). Standard speed (AN126): reset 480 µs low, presence sampled 70 µs after the release, 960 µs recovery; write slots low 6 µs (a 1) or 60 µs (a 0), 70 µs each; read slots low 6 µs, sampled at 15 µs.
- **Host commands** (`h_w*`, top two bits): `0x00` RESET (then `h_status[3]` = presence), `0x40` + byte = WRITE, `0x80` = READ (the byte is the reply on `h_r*`), `0xC0` = invalid (sticky `err`). Wait for `h_status[0]` (busy) to clear between commands. `h_status = {4'b0, presence, err, 0, busy}`.
- **Rate:** `US` = clocks per microsecond (50 at 50 MHz; any clock with an integer number of clocks per µs).
- **Known limits:** standard speed only (no overdrive); no strong pull-up for parasitic power; ROM search (0xF0) is not supported (it needs bit-level read-read-write triplets, which the byte commands cannot express), so one device per line unless the host knows the ROM codes (MATCH ROM works: it is a byte write); no CRC in hardware (the host checks it).

## Tests
`test/`: cocotb + Icarus against the independent reference device `tools/refmodels/onewire.py` (written from the 1-Wire timing spec; itself checked against an ideal master in `tools/refmodels/tests/test_onewire.py`): presence, no device, READ ROM with CRC-8, byte writes, invalid command. `make` / `make PRIMS=1`.
Chip level: `test/test_bitstream.py::test_onewire` loads the bitstream through the host interface and reads a device's ROM over the open-drain pin.
