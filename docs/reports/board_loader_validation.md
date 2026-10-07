# Demo-board loader validation

Date: 2026-10-07. Host software change; frozen hardware is unchanged.

The MicroPython-compatible loader in `tools/board/warp.py` had not received
the unsigned-field and chunk validation already present in the reference
host. A negative chunk produced LOAD_BEGIN and LOAD_END without LOAD_DATA.
Architecture `0x10003` transmitted as `0x0003`; word `0x100000001` transmitted
as `0x00000001`; 65536 words advertised a zero length. These failures were
reproduced using lightweight local Python before the fix.

The board loader now rejects non-positive or non-integer chunks, architecture
IDs outside unsigned 16-bit range, words outside unsigned 32-bit range and
lengths exceeding 65535 words. Boolean values are also rejected. Validation
runs before READ_ID or any load-related device transaction, so malformed
arguments cannot start a partial configuration attempt. Exceptions use the
existing `WarpError` board API. Valid transaction bytes, CRC calculation,
SPI timing and bitstream format are unchanged.

Boundary tests exercise every rejection, assert that invalid requests never
contact the chip, compare a maximum-length valid load against the reference
host, and preserve zero/maximum unsigned word values. The existing randomized
valid loads, CRC fallback, file parsing and status tests still pass.

Local evidence (project venv, 2026-10-07):

```sh
source .venv/bin/activate
PYTHONPATH=tools pytest -q tools/board/tests/test_warp.py tools/host/tests/test_protocol.py
```

Result: **317 passed in 0.84s**. This is Python validation and transaction
evidence, not real-board testing or a new chip simulation result. The normal
`unit` workflow already collects these tests; hosted unit37663965540 passes on675a03c, covering the board fix through the normal unit suite.
