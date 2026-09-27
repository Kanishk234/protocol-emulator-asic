"""Host library for TRIPWIRE's SPI host interface (ARCHITECTURE.md §9, DECISIONS D-046).

The same API drives the cocotb testbench and, later, real hardware:
  - `frame_write` / `frame_read`: the §9 transaction bytes (pure functions),
  - `load_sequence(image)`: every host write that loads a tripc image (§14 H1), as (address, words),
  - `Host(xfer)`: a client over any full-duplex SPI transfer function `xfer(bytes) -> bytes`,
  - `RegisterModel`: a software model of the write side of the map, for checking sequences offline.
"""

from .host import (HM, Host, RegisterModel, frame_read, frame_write, load_sequence, port_word,  # noqa: F401
                   slot_words)
