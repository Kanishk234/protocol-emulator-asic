# Mutation campaign (phase 4)

Each mutant plants one realistic bug in a throwaway copy of the repository (`scripts/mutation.py`); the check listed must fail. Local run.

| Mutant | Bug planted | Check that should catch it | Result |
|---|---|---|---|
| `timer_reload_off_by_one` | timer reloads RELOAD - 1 at terminal count (period one clock short) | white-box primitive tests vs the Python model | **killed** |
| `shift_wrong_end` | shift register outputs the wrong end (MSB/LSB swapped) | white-box primitive tests vs the Python model | **killed** |
| `fifo_drops_items` | host channel FIFO silently drops every second push | chip suite (black-box fabric): host channel tests | **killed** |
| `crc_check_disabled` | loader accepts a bad CRC | chip suite: test_bad_crc | **killed** |
| `arch_check_disabled` | loader accepts any architecture version | chip suite: test_wrong_arch_version | **killed** |
| `inverted_output_enable` | bidirectional pins' output enable inverted | chip suite with a real bitstream (counter4 checks FAB_IO0's enable) | **killed** |
| `parking_gate_removed` | fabric outputs reach the pins while not RUNNING | F1 formal proof (output isolation) | **killed** |
| `config_bit_position` | wrong configuration-bit position: a LUT's INIT shifted by one bit in logic4's bitstream (`X4Y2.G.INIT[15:0] = 0000111100001111 -> 0001111000011110`) | chip suite with the real bitstream (logic4 truth table) | **killed** |
| `bad_cmd_overwrites_error` | a bad command overwrites a pending load error code (D-021: only when ERROR_CODE is 0) | pyuvm shell environment vs the shell reference model | **killed** |
| `overflow_never_clears` | ch_overflow is not cleared by READ_STATUS | pyuvm shell environment vs the shell reference model | **killed** |
| `tx_ready_when_stopped` | STATUS.tx_ready reported while not RUNNING (a CH_WRITE would be refused) | pyuvm shell environment vs the shell reference model | **killed** |

## Notes
- Mutants are planted in a copy (`build/mutation/<name>/`); the working tree is never changed. Logs: `build/mutation/<name>.log` (not committed).
- The check for each mutant is the one designed to catch that class of bug; a wider suite would catch several of them more than once (e.g. the inverted output enable also breaks `test_logic4`).
- Not covered by this campaign: faults inside the hardened tiles' netlists (the per-tile netlist-vs-RTL equivalence of D-023 is not done), and mutants of the protocol designs themselves (their RTL tests against independent models play that role).
