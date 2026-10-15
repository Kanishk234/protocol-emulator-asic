# WARP on the Tiny Tapeout demo board

`warp.py` loads WARP bitstreams into the chip and talks to the loaded design from the demo board's RP2040 (MicroPython, Tiny Tapeout's `ttboard` SDK). It is the "how the bitstream gets loaded" part of the software flow (D-032):

```
protocol Verilog + pin map --tools/compile--> .wbit --copy to the board--> warp.py --host SPI--> chip
```

## Use

On the host computer:

```sh
cd tools
python -m compile.compile --pins compile/examples/uart16.yaml -o ../build/compile/uart16 \
    ../protocols/uart/*.v                       # -> build/compile/uart16/uart16.wbit
mpremote cp board/warp.py :warp.py
mpremote cp ../build/compile/uart16/uart16.wbit :uart16.wbit
```

On the board (MicroPython REPL):

```python
import warp
w = warp.on_demo_board(clock_hz=10_000_000)   # selects tt_um_warp, clocks it, resets it
w.load_file("uart16.wbit")                     # refuses another architecture; checks length/CRC
w.run()
w.ch_write(0x55)                               # byte to the design; it leaves on FAB_OUT0 (uo_out[2])
w.set_fab_in(1)                                # drive the design's inputs FAB_IN0..4 (ui_in[3..7])
print(w.ch_read(), w.user_status(), w.status())
w.stop()                                       # every fabric pin parked
```

## API

| Call | Does |
|---|---|
| `Warp(pins)` | `pins`: any object with `write_ui(byte)`, `read_uo() -> byte`, optionally `wait(clocks)` |
| `on_demo_board(clock_hz, project)` | the demo-board pins via `ttboard`, project enabled, clocked (PWM), reset |
| `read_id()` | architecture version of the chip (raises if it is not a WARP chip) |
| `load(arch, words)`, `load_file(path)` | checked load (ARCHITECTURE §3); raises unless the chip ends in `LOADED` |
| `run()`, `stop()`, `user_reset()` | run control (§4) |
| `ch_write(byte, last=False)`, `ch_read()` | host byte channel (§7.3) |
| `status()`, `read_status()`, `user_status()` | STATUS decoded, STATUS + error code, the design's `h_status` |
| `set_fab_in(value)` | the design's five input pins |

Limits: the shell needs every SPI pin level to last 4 project clocks; MicroPython pin writes take microseconds, so any project clock of 1 MHz or more is safe. No SPI hardware peripheral is used (the host pins are ordinary project inputs).

If pin I/O raises an exception or the transfer is interrupted, `xfer` attempts
to release CS with SCK and MOSI low, keeps FAB_IN unchanged, and re-raises the
original exception. It does not retry the command. Some bytes or a complete
command may already have reached the chip; a failed channel write or read has
an uncertain outcome. Restore the transport before inspecting chip status and
choosing recovery. An interrupted configuration load should be restarted from
`LOAD_BEGIN` with a complete checked image while the chip is stopped. If idle
cleanup also fails, re-establish CS high and the required idle interval before
any new transaction. Successful cleanup does not undo chip state changes.

## Tested

- `tools/board/tests/test_warp.py` (pytest): transactions, CRC (incl. the pure-Python fallback), `.wbit` parsing and status decoding equal the reference host (`tools/host/protocol.py`) and bitstream code, byte for byte.
- `test/test_bitstream.py::test_board_loader` (cocotb): this module's code, unchanged, drives the chip's pins in simulation: checked load of `uart16`, RUN, bytes out as UART frames, a frame in read back over the host channel.
- **Not tested on hardware** (no board yet): the `ttboard` glue (`on_demo_board`) and real pin timing.

## Host service budget

Before choosing a streaming rate, use the analytical planner from the project
root (activate the project venv first):

```sh
PYTHONPATH=tools python -m board.budget --clock-hz 8000000 --sck-hz 1000000 \
  --arrival-bytes-s 1000 --direction read --blackout-us 2000 --queue-bytes 2
```

This example intentionally flags insufficient buffering despite adequate
average service capacity. It includes the existing API's one STATUS poll plus
one channel command per payload byte, conservative CS framing and optional
`--overhead-us` per transaction. Supply worst-case host scheduling overhead,
not just ideal wire timing. The planner assumes an initially empty queue,
a bounded arrival burst and one initial blackout followed by guaranteed service
intervals. Repeated pauses, opposite-direction traffic and extra status polls
must be covered by the service budget; simultaneous traffic is not independently
certified by two single-direction plans. The existing shell has two FIFO entries
per direction; a larger requested queue is a hypothetical design budget, not
additional chip storage. Protocol-side readiness and physical timing remain
separate requirements. No board throughput is measured by this tool.
