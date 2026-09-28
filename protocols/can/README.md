# CAN 2.0A controller: held-out protocol H4

Written in phase 4, after `hw-freeze`, for the frozen chip (`docs/design/HELDOUT.md`; results in `docs/reports/heldout_results.md`). **It does not fit the chip's fabric** (G1: 207 of 88 logic cells; G0: 241 of 96). It is a working RTL design that shows what the chip cannot hold.

- **File:** `can_top.v`. Base data frames: SOF, 11-bit ID, RTR/IDE/r0, DLC, 0–8 data bytes, CRC-15, delimiters, ACK, EOF + intermission; bit stuffing (SOF..CRC, including a stuff bit after the CRC); arbitration on ID/RTR with fall-back to receiving; the ACK slot driven as a receiver and checked as a transmitter; bus integration (11 recessive bits) before sending. One frame parser serves both roles (a transmitter receives its own bits). `PRIMS = 1`: two WARP hard timers (mid-bit sample point; bit boundary) and a hard shift register (the bytes); `PRIMS = 0` plain logic.
- **Bus pins:** `rx_i` (FAB_IN0) from a transceiver's RXD; `tx_oe` on a bidirectional pin (FAB_IO0) pulls the transceiver's TXD dominant, released = recessive through a pull-up. Not on `uo_out`: parked at 0 it would hold the bus dominant (BUGS #19).
- **Host:** bytes = the frame's bits after SOF through the data, MSB first (3 + DLC bytes, the last with 2 bits), `h_wlast` on the last; received frames come back packed the same way; `h_status = {crc_ok, acked, arb_lost, err, overrun, underrun, tx, busy}`.
- **Known limits:** no error frames or error counters (out of scope, HELDOUT.md), no remote frames, no extended IDs, sample point at 50 % with hard synchronization only (no resynchronization), host must deliver a byte within 8 bit times.

## Tests
`test/`: cocotb + Icarus against the independent reference node `tools/refmodels/can.py` (Bosch CAN 2.0A; itself tested node to node, with arbitration and CRC, in `tools/refmodels/tests/test_can.py`): transmit (a node receives and ACKs), receive (a stuffing-heavy 8-byte frame, the design ACKs), arbitration lost to a lower ID then won on the retry. `make` / `make PRIMS=1`. No chip-level test: it does not fit.
